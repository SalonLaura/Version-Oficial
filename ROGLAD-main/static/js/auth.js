document.addEventListener('DOMContentLoaded', function() {
    // Toggle password visibility
    const passwordToggle = document.querySelector('.password-toggle');
    const passwordInput = document.getElementById('password');
    
    if(passwordToggle && passwordInput) {
        passwordToggle.addEventListener('click', function() {
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
        });
    }

    // Form validation
    const form = document.getElementById('loginForm');
    
    if(form) {
        form.addEventListener('submit', function(e) {
            const business = document.getElementById('business').value;
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;

            if(!business || !username || !password) {
                e.preventDefault();
                alert('Por favor complete todos los campos');
            }
        });
    }
});