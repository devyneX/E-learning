function openForm(id) {
  document.getElementById(id).style.display = "block";
  // document.getElementsBy(id2).style.display = "none";
}

function closeForm(id) {
  document.getElementById(id).style.display = "none";
}


const btn = document.querySelector("button");
const post = document.querySelector(".feedback_post");
const widget = document.querySelector(".feedback_star-widget");
const editBtn = document.querySelector(".feedback_edit");
btn.onclick = () => {
    widget.style.display = "none";
    post.style.display = "block";
    editBtn.onclick = () => {
        widget.style.display = "block";
        post.style.display = "none";
    }
    return false;
}

