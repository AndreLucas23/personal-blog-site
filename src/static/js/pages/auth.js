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
