const form = document.querySelector('form');
const username = document.querySelector('input[name="username"]');
const password = document.querySelector('input[name="password"]');
const confirmPassword = document.querySelector('input[name="confirm_password"]');
const usernameError = document.querySelector('#username_error');
const passwordError = document.querySelector('#password_error');

function shakeInput(input) {
    input.classList.add('input-error', 'shake');
    input.addEventListener('animationend', function () {
        input.classList.remove('shake');
    }, { once: true });
}

if (usernameError.textContent.trim()) {
    shakeInput(username);
}

form.addEventListener('submit', function (event) {
    if (password.value !== confirmPassword.value) {
        event.preventDefault();

        passwordError.textContent = '两次密码不一致';
        shakeInput(confirmPassword);
    }
});

username.addEventListener('input', function () {
    usernameError.textContent = '';
    username.classList.remove('input-error');
});

confirmPassword.addEventListener('input', function () {
    passwordError.textContent = '';
    confirmPassword.classList.remove('input-error');
});
