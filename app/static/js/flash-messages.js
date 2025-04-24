function injectFlashMessage(category, message) {
  let container = document.querySelector(".flash-messages");

  // If doesn't exist, create
  if (!container) {
    container = document.createElement("div");
    container.className = "flash-messages";
    document.body.appendChild(container);
  }
  
  // Always update the position based on current header height
  const header = document.querySelector("header");
  if (header) {
    // Use getBoundingClientRect to get the precise bottom position of the header
    const headerRect = header.getBoundingClientRect();
    container.style.top = headerRect.bottom + "px";
  }

  // Create the alert element
  const alert = document.createElement("div");
  alert.className = `alert alert-${category}`;
  alert.textContent = message;
  
  // Check if a modal is currently open
  const isModalOpen = document.querySelector('.modal[style*="display: flex"]') || 
                     document.querySelector('.modal.show') ||
                     document.querySelector('.modal[style*="display: block"]');
  
  if (isModalOpen) {
    // Add a special class when a modal is open to ensure it matches the overlay
    alert.classList.add('modal-active');
  }
  
  container.appendChild(alert);

  // Auto-dismiss with fade-out
  setTimeout(() => {
    alert.classList.add("fade-out");
    setTimeout(() => alert.remove(), 300);
  }, 2000);
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

// Also update the position when the window is resized
window.addEventListener('resize', function() {
  const container = document.querySelector(".flash-messages");
  const header = document.querySelector("header");
  if (container && header) {
    const headerRect = header.getBoundingClientRect();
    container.style.top = headerRect.bottom + "px";
  }
});

// Make sure existing flash messages are also properly positioned
document.addEventListener('DOMContentLoaded', function() {
  const container = document.querySelector(".flash-messages");
  const header = document.querySelector("header");
  if (container && header) {
    const headerRect = header.getBoundingClientRect();
    container.style.top = headerRect.bottom + "px";
  }
  
  // Handle all already-injected alerts (e.g., from Flask or dynamic JS)
  setTimeout(() => {
    const allAlerts = document.querySelectorAll('.flash-messages .alert');
    allAlerts.forEach(alert => {
      alert.classList.add("fade-out");
      setTimeout(() => alert.remove(), 300);
    });
  }, 2000);
});