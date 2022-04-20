function openForm(id) {
  document.getElementById(id).style.display = "block";
}

function closeForm(id) {
  document.getElementById(id).style.display = "none";
}


const container = document.querySelector(".feedback_container"),
      privacy = container.querySelector(".feedback_post .feedback_privacy"),
      arrowBack = container.querySelector(".feedback_audience .feedback_arrow-back");
      privacy.addEventListener("click", () => {
        container.classList.add("active");
      });
      arrowBack.addEventListener("click", () => {
        container.classList.remove("active");
      });