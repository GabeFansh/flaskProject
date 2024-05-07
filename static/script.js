function loadDoc(url, func) {
    let xhttp = new XMLHttpRequest();

    xhttp.onload = function() {
        if (xhttp.status != 200) {
            console.log("Error");
        } else {
            func(xhttp.response);
        }
    }
    xhttp.open("GET", url);
    xhttp.send();
}

function login() {
    let txtEmail = document.getElementById("txtEmail");
    let txtPassword = document.getElementById("txtPassword");
    if (txtEmail.value == '' || txtPassword.value == '') {
        alert("Email and Password cannot be blank.");
        return;
    }
     let URL = "/login?email=" + txtEmail.value + "&password=" + txtPassword.value;


    let checkRemember = document.getElementById("checkRemember");
    if (checkRemember.checked) {
        URL += "&remember=yes";
    } else {
        URL += "&remember=no";
    }
    loadDoc(URL, login_response)
}


function register_page() {
    window.location.href = "register";
}

function login_response(response) {
    let data = JSON.parse(response);
    let result = data["result"];
    if (result != "OK") {
        alert(result);
    }
    else {
        window.location.replace("/loggedIn");
    }
}



function logout() {
    window.location.href = "logout";
}

function register() {
    let xhttp = new XMLHttpRequest();
    xhttp.onload = function() {
        if (xhttp.status != 200) {
            console.log("Error");
        } else {
            register_response(xhttp.response);
        }
    }

    let txtEmail = document.getElementById("txtEmail");
    let txtPassword = document.getElementById("txtPassword");
    let txtUsername = document.getElementById("txtUsername");
    let profilePic = document.getElementById("profilePic");

    if (txtEmail.value == '' || txtPassword.value == '' || txtUsername.value == '' || profilePic.value == '') {
        alert("Fields cannot be blank.");
        return;
    }

    xhttp.open('POST','/registerAccount',true);
    var formData = new FormData();
    formData.append("profilePic", document.getElementById('profilePic').files[0]);
    formData.append("email", document.getElementById('txtEmail').value);
    formData.append("username", document.getElementById('txtUsername').value);
    formData.append("password", document.getElementById('txtPassword').value);

    xhttp.send(formData);
}

function register_response(response) {
    let result = JSON.parse(response);
    if (result["results"] == "exists") {
        alert("EMAIL EXISTS, TRY AGAIN");
        return;
    }

    let user = result["results"];
    console.log(user);

    let email = user["email"];
    let password = user["password"];

    let loginURL = "/login?email=" + email + "&password=" + password + "&remember=yes";
    loadDoc(loginURL, login_response)

}




function upload_post() {
    let xhttp = new XMLHttpRequest();
    xhttp.onload = function() {
        if (xhttp.status != 200) {
            console.log("Error");
        } else {
            upload_response(xhttp.response);
        }
    }

    xhttp.open('POST','/uploadPost',true);
    var formData = new FormData();
    formData.append("post_subject", document.getElementById('postSubject').value);
    formData.append("post_caption", document.getElementById('postText').value);

    xhttp.send(formData);
}

function upload_response(response) {
    location.reload();
}


function display_posts(page, user = null) {
    let postsURL = "/getposts?page=" + page;
    if (user != null) {
        postsURL += "&user=" + user;
    } else {
        postsURL += "&user=null";
    }
    loadDoc(postsURL, post_response);
}


function post_response(response) {
    let data = JSON.parse(response);
    let posts = data["posts"];
    let postDiv = document.getElementById("postsContainer");
    postDiv.innerHTML = "";
    for (let i = 0; i < 10  ; i++) {
        let post = posts[i];
        let postDiv = document.createElement("div");
        let email = post["email"];
        let postID = post["postID"];
        postDiv.className = "post";
        let innerText = ""
        innerText += `
            <a href="/profile?email=${email}">
            <img src="${post["profilePic"]}" class="pfp" />
            </a>
            <p class="username">${post["username"]}</p>
            <p class="postSubject" onclick="showPost('${postID}')">${post["subject"]}</p>
            </a>
            <p class="postText">${post["caption"]}</p>`;
        if (Boolean(data["deleteButton"])) {
            innerText += `<button class="deleteButton" onclick="delete_post('${postID}');">Delete</button>`;
        }
        postDiv.innerHTML = innerText;
        document.getElementById("postsContainer").appendChild(postDiv);
    }
}

function upload_post_container(upload) {
    if (Boolean(upload)) {
        let postContainer = document.getElementById("uploadPostContainer");
        postContainer.style.display = "block";
    }
}

function delete_post(postID) {
    let URL = "/deletePost?postID=" + postID;
    loadDoc(URL, delete_response);
}

function delete_response(response) {
    location.reload();
}

function showPost(postID) {
    let URL = "/showPost?postID=" + postID;
    window.location.href = URL;
}

function addComment(postID) {
    let xhttp = new XMLHttpRequest();
    xhttp.onload = function() {
        if (xhttp.status != 200) {
            console.log("Error");
        } else {
            upload_response(xhttp.response);
        }
    }

    xhttp.open('POST','/addComment',true);
    var formData = new FormData();
    formData.append("commentInput", document.getElementById('commentInput').value);
    formData.append("postID", postID);
    xhttp.send(formData);
}

function comment_response(response) {
    window.location.reload();
}

function showComments(postID) {
    let URL = "/showComments?postID=" + postID;
    loadDoc(URL, showComments_response);

}

function showComments_response(response) {
    let data = JSON.parse(response);
    let comments = data["comments"];
    let commentsDiv = document.getElementById("showCommentContainer");
    commentsDiv.innerHTML = "";
    for (let i = 0; i < comments.length; i++) {
        let comment = comments[i];
        let commentDiv = document.createElement("div");
        commentDiv.className = "comment";
        let innerText = ""
        innerText += `
            <a href="/profile?email=${comment["email"]}">
            <img src="${comment["profilePic"]}" class="pfp" />
            </a>
            <p class="username">${comment["username"]}</p>
            <p class="commentText">${comment["comment"]}</p>`;
        console.log(Boolean(data["deleteButton"]));
        if (Boolean(data["deleteButton"])) {
            innerText += `<button class="deleteButton" onclick="delete_comment('${comment["commentID"]}');">Delete</button>`;
        }
        commentDiv.innerHTML = innerText;
        document.getElementById("showCommentContainer").appendChild(commentDiv);
    }
}





