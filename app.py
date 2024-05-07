from flask import Flask, render_template, request, redirect, make_response, session
import json
from flask_session import Session
import uuid
import boto3
import datetime
from data import *

app = Flask(__name__)
app.config['SESSION_PERMANENT'] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)




def get_public_bucket():
    s3 = boto3.resource(service_name='s3', region_name='us-east-2', aws_access_key_id=AWSKEY,
                        aws_secret_access_key=AWSSECRET)
    bucket = s3.Bucket(PUBLIC_BUCKET)
    return bucket


def get_table(name):
    client = boto3.resource(service_name='dynamodb',
                            region_name='us-east-2',
                            aws_access_key_id=AWSKEY,
                            aws_secret_access_key=AWSSECRET)
    table = client.Table(name)
    return table


@app.route('/hello')
def hello_world():
    return 'Hello World!'


@app.route('/home')
def home():
    if is_logged_in():
        return redirect("/loggedIn")
    return render_template("home.html")


@app.route('/register')
def register():
    return render_template("register.html")


@app.route('/login')
def login():
    email = request.args.get("email")
    password = request.args.get("password")

    table = get_table("Users")
    item = table.get_item(Key={"email": email})

    if 'Item' not in item:
        return {'result': 'Email not found.'}

    user = item['Item']

    if password != user['password']:
        return {'result': 'Password does not match.'}

    session["email"] = user["email"]
    session["username"] = user["username"]
    session["profilePic"] = user["url"]
    result = {'result': 'OK'}

    response = make_response(result)

    remember = request.args.get("remember")
    if remember == "no":
        response.delete_cookie("remember")
    else:
        key = add_remember_key(user["email"])
        response.set_cookie("remember", key, max_age=60 * 60 * 24 * 14)

    return response;


def is_logged_in():
    if not session.get("email"):
        return auto_login()
    return True


def add_remember_key(email):
    table = get_table("Remember")
    key = str(uuid.uuid4()) + str(uuid.uuid4()) + str(uuid.uuid4())

    item = {
        "key": key,
        "email": email
    }

    table.put_item(Item=item)
    return key


def auto_login():
    cookie = request.cookies.get("remember")
    if cookie is None:
        return False

    table = get_table("Remember")
    result = table.get_item(Key={"key": cookie})

    if 'Item' not in result:
        return False

    remember = result['Item']

    table = get_table("Users")
    result = table.get_item(Key={"email": remember["email"]})

    user = result['Item']
    session['email'] = user['email']
    session['username'] = user['username']

    return True


@app.route("/loggedIn")
def loggedIn():
    if not is_logged_in():
        return redirect("/home")
    return render_template("loggedIn.html", username=session["username"], email=session["email"],
                           profilePic=session["profilePic"])


@app.route('/logout')
def logout():
    session.pop("email", None)
    session.pop("username", None)
    session.pop("profilePic", None)

    response = make_response(redirect("/home"))
    response.delete_cookie("remember")
    return response


@app.route('/registerAccount', methods=['POST'])
def register_account():
    bucket = get_public_bucket()
    table = get_table('Users')

    file = request.files["profilePic"]
    email = request.form["email"]
    username = request.form["username"]
    password = request.form["password"]
    uid = str(uuid.uuid4())

    item = table.get_item(Key={"email": email})

    if 'Item' in item:
        return {'result': "exists"}

    filename = uid + "-" + file.filename

    item = {
        'email': email,
        'password': password,
        'username': username,
        'url': "https://gabefansh-web-public.s3.us-east-2.amazonaws.com/" + filename
    }

    ct = 'image/jpeg'
    if filename.endswith('.png'):
        ct = "image/png"
    if filename.endswith(".gif"):
        ct = "image/gif"

    table.put_item(Item=item)
    bucket.upload_fileobj(file, filename, ExtraArgs={'ContentType': ct})

    return {'results': item}


@app.route('/profile')
def profile():
    email = request.args.get("email")
    try:
        if email == session["email"]:
            session_email = session["email"]
            upload = "true"
        else:
            session_email = session["email"]
            upload = "false"
    except:
        upload = "false"
        session_email = "none"
    table = get_table("Users")
    item = table.get_item(Key={"email": email})

    user = item['Item']
    return render_template("profile.html", email=user["email"], username=user["username"], profilePic=user["url"],
                           upload_post=upload, session_email=session_email)


def sortDate(post):
    return post['date']


@app.route('/uploadPost', methods=['POST'])
def upload_post():
    table = get_table("posts")
    postID = str(uuid.uuid4()) + str(uuid.uuid4()) + str(uuid.uuid4())
    username = session['username']
    current_time = str(datetime.datetime.now())
    post_subject = request.form["post_subject"]
    post_caption = request.form["post_caption"]

    item = {
        'postID': postID,
        'date': current_time[0:19],
        'username': username,
        'profilePic': session['profilePic'],
        'email': str(session['email']),
        'subject': post_subject,
        'caption': post_caption,
        'comments': []
    }

    table.put_item(Item=item)
    return {'results': 'ok'}


@app.route("/getposts")
def get_posts():
    page = request.args.get("page")
    result = {"Result": "None"}
    if int(page) == 0:
        table = get_table('posts')
        posts = []
        for item in table.scan()["Items"]:
            posts.append(item)

        posts.sort(key=sortDate)
        posts.reverse()

        result = {
            "page": page,
            "posts": posts
        }
    if int(page) == 1:
        user = request.args.get("user")
        table = get_table('posts')
        posts = []
        for item in table.scan()["Items"]:
            if item['email'] == user:
                posts.append(item)

        posts.sort(key=sortDate)
        posts.reverse()

        try:
            if user == session['email']:
                delete_button = True
            else:
                delete_button = False
        except:
            delete_button = False

        result = {
            "page": page,
            "posts": posts,
            "deleteButton": delete_button
        }

    return result


@app.route("/deletePost")
def delete_post():
    postID = request.args.get("postID")
    table = get_table("posts")
    table.delete_item(Key={"postID": postID})
    return {'result': 'ok'}


@app.route("/showPost")
def show_post():
    postID = request.args.get("postID")
    table = get_table("posts")
    item = table.get_item(Key={"postID": postID})
    post = item['Item']
    post_comments = post['comments']
    try:
        if session["email"]:
            session_email = session["email"]
        if session["profilePic"]:
            session_profilePic = session["profilePic"]
    except:
        session_email = "none"
        session_profilePic = "none"
    print(post)
    return render_template("post.html",
                           subject=post["subject"],
                           caption=post["caption"],
                           username=post["username"],
                           date=post["date"],
                           postProfilePic=post["profilePic"],
                           postID=post["postID"],
                           comments=post_comments,
                           userProfilePic=session_profilePic,
                           userEmail=session_email)


@app.route("/addComment", methods=['POST'])
def add_comment():
    new_comment = request.form["commentInput"]
    commentID = str(uuid.uuid4()) + str(uuid.uuid4()) + str(uuid.uuid4())
    postID = request.form["postID"]
    table = get_table("posts")
    item = table.get_item(Key={"postID": postID})
    post = item['Item']

    comment = {
        "comment": new_comment,
        "commentID": commentID,
        "username": session["username"],
        "email": session["email"],
        "profilePic": session["profilePic"],
        "date": str(datetime.datetime.now())[0:19]
    }

    comments = post['comments']
    comments.append(comment)
    table.update_item(Key={"postID": postID}, UpdateExpression="set comments = :c",
                      ExpressionAttributeValues={":c": comments})
    print(post["comments"])
    return {'result': 'ok'}


@app.route("/showComments")
def show_comments():
    postID = request.args.get("postID")
    table = get_table("posts")
    item = table.get_item(Key={"postID": postID})
    post = item['Item']
    post_comments = post['comments']
    return {'comments': post_comments}


if __name__ == '__main__':
    app.run(debug=True)
