document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        const flashMessages = document.querySelector('.flash-messages');
        if (flashMessages) {
            // Optional: add a fade-out effect
            flashMessages.style.transition = "opacity 0.5s ease-out";
            flashMessages.style.opacity = 0;
            setTimeout(function() {
                flashMessages.remove();
            }, 500); // wait for the fade-out transition to complete
        }
    }, 5000); // time in milliseconds (5000ms = 5 seconds)
});