function injectFlashMessage(category, message) {
  let container = document.querySelector(".flash-messages");

  // If doesn't exist, create
  if (!container) {
    container = document.createElement("div");
    container.className = "flash-messages";
    document.body.prepend(container);
  }

  // Create the alert div
  const alert = document.createElement("div");
  alert.className = `alert alert-${category}`;
  alert.innerText = message;
  container.appendChild(alert);

  // Auto-dismiss after 4 seconds with fade-out
  setTimeout(() => {
    alert.classList.add("fade-out");
    setTimeout(() => alert.remove(), 500); // remove after fade-out finishes
  }, 4000);
}

function showConfirm(message, onConfirm) {
  const modal = document.getElementById("confirmModal");
  const messageEl = document.getElementById("confirmModalMessage");
  const yesBtn = document.getElementById("confirmYesBtn");
  const noBtn = document.getElementById("confirmNoBtn");

  messageEl.textContent = message;
  modal.style.display = "flex";

  // Remove previous listeners to prevent stacking
  const cloneYes = yesBtn.cloneNode(true);
  yesBtn.parentNode.replaceChild(cloneYes, yesBtn);

  const cloneNo = noBtn.cloneNode(true);
  noBtn.parentNode.replaceChild(cloneNo, noBtn);

  cloneYes.onclick = () => {
    modal.style.display = "none";
    onConfirm(); // Execute callback
  };

  cloneNo.onclick = () => {
    modal.style.display = "none";
  };
}

document.addEventListener('DOMContentLoaded', function () {
    // Handle all already-injected alerts (e.g., from Flask or dynamic JS)
    setTimeout(() => {
        const allAlerts = document.querySelectorAll('.flash-messages .alert');
        allAlerts.forEach(alert => {
            alert.classList.add("fade-out");
            setTimeout(() => alert.remove(), 500);
        });
    }, 4000);
});