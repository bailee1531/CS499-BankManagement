// Spring 2025 Authors: Braden Doty, Bailee Segars
document.addEventListener('DOMContentLoaded', () => {
    const buttons = document.querySelectorAll('.account-btn');
    const hiddenInput = document.querySelector('input[name="account_type"]');

    buttons.forEach(button => {
        button.addEventListener('click', () => {
            const selectedType = button.getAttribute('data-type');
            hiddenInput.value = selectedType;

            // Visually and semantically indicate selection
            buttons.forEach(btn => {
                btn.classList.remove('selected');
                btn.setAttribute('aria-pressed', 'false');
            });

            button.classList.add('selected');
            button.setAttribute('aria-pressed', 'true');

            // Submit the form
            document.getElementById('accountForm').submit();
        });
    });
});