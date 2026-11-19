import { icon } from '../ui/dom.js';

// Lets members check what they typed in a password field.
document.querySelectorAll('[data-password-toggle]').forEach((button) => {
    const input = document.getElementById(button.dataset.passwordToggle);

    button.addEventListener('click', () => {
        const show = input.type === 'password';
        input.type = show ? 'text' : 'password';
        button.setAttribute('aria-pressed', String(show));
        button.setAttribute('aria-label', show ? 'Ocultar senha' : 'Mostrar senha');
        button.replaceChildren(icon(show ? 'eye-off' : 'eye'));
        input.focus();
    });
});

// On the registration page, show the profile address the username will give.
const usernameInput = document.getElementById('username');
const usernameHint = document.getElementById('username-hint');

if (usernameInput && usernameHint) {
    const rule = usernameHint.textContent;
    const pattern = new RegExp(usernameInput.dataset.pattern);
    const reserved = new Set(usernameInput.dataset.reserved.split(' '));

    const isValid = (username) => username.length >= usernameInput.minLength
        && username.length <= usernameInput.maxLength
        && pattern.test(username)
        && !reserved.has(username);

    const showAddress = () => {
        const username = usernameInput.value.trim().replace(/^@/, '').toLowerCase();
        usernameHint.textContent = isValid(username) ? `Seu perfil vai ficar em /@${username}` : rule;
    };

    usernameInput.addEventListener('input', showAddress);
    // The server fills the field back in after an error.
    showAddress();
}
