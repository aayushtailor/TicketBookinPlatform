// ===============================
// Main.js - Nehru Garden Website
// ===============================

// Parallax Hero
document.addEventListener("DOMContentLoaded", function () {
  if (typeof Rellax !== "undefined") {
    try {
      new Rellax(".rellax");
    } catch (err) {
      console.warn("Rellax not initialized:", err);
    }
  }
});

// ===============================
// Modal Gallery Effects
// ===============================
function openModal(src) {
  const modal = document.getElementById("modal");
  const modalImg = document.getElementById("modal-img");

  if (modal && modalImg) {
    modalImg.src = src;
    modal.style.display = "flex";
  }
}

function closeModal() {
  const modal = document.getElementById("modal");
  if (modal) {
    modal.style.display = "none";
  }
}

// ===============================
// Review Slider Logic
// ===============================
let currentReview = 0;

function showReview(idx) {
  const reviews = document.querySelectorAll(".review-card");
  if (!reviews.length) return;

  reviews.forEach((el, i) => {
    el.classList.toggle("active", i === idx);
  });
}

function moveSlider(n) {
  const reviews = document.querySelectorAll(".review-card");
  if (!reviews.length) return;

  currentReview = (currentReview + n + reviews.length) % reviews.length;
  showReview(currentReview);
}

// Initialize reviews
document.addEventListener("DOMContentLoaded", () => {
  showReview(0);
});

// ===============================
// Toast Notification
// ===============================
function showToast(msg) {
  let toast = document.getElementById("toast");

  if (!toast) {
    toast = document.createElement("div");
    toast.id = "toast";
    toast.style.position = "fixed";
    toast.style.bottom = "30px";
    toast.style.right = "30px";
    toast.style.padding = "12px 18px";
    toast.style.borderRadius = "8px";
    toast.style.background = "linear-gradient(45deg, #21d4fd, #b721ff)";
    toast.style.color = "#fff";
    toast.style.fontWeight = "600";
    toast.style.zIndex = "9999";
    toast.style.opacity = "0";
    toast.style.transition = "opacity 0.5s ease";
    document.body.appendChild(toast);
  }

  toast.textContent = msg;
  toast.style.opacity = "1";

  setTimeout(() => {
    toast.style.opacity = "0";
  }, 2200);
}
