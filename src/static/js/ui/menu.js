// Dropdown menus: a button with data-menu-button and aria-controls pointing at the menu.

function items(menu) {
    return [...menu.querySelectorAll('[role^="menuitem"]')];
}

function close(button, menu, { restoreFocus = false } = {}) {
    menu.hidden = true;
    button.setAttribute('aria-expanded', 'false');
    if (restoreFocus) button.focus();
}

function open(button, menu) {
    menu.hidden = false;
    button.setAttribute('aria-expanded', 'true');
    items(menu)[0]?.focus();
}

function bindMenu(button) {
    const menu = document.getElementById(button.getAttribute('aria-controls'));
    if (!menu) return;

    button.addEventListener('click', () => {
        if (menu.hidden) open(button, menu);
        else close(button, menu);
    });

    document.addEventListener('click', (event) => {
        if (!menu.hidden && !menu.contains(event.target) && !button.contains(event.target)) {
            close(button, menu);
        }
    });

    menu.addEventListener('keydown', (event) => {
        const list = items(menu);
        const index = list.indexOf(document.activeElement);

        if (event.key === 'Escape') {
            event.preventDefault();
            close(button, menu, { restoreFocus: true });
        } else if (event.key === 'ArrowDown') {
            event.preventDefault();
            list[(index + 1) % list.length]?.focus();
        } else if (event.key === 'ArrowUp') {
            event.preventDefault();
            list[(index - 1 + list.length) % list.length]?.focus();
        } else if (event.key === 'Tab') {
            close(button, menu);
        }
    });
}

export function initMenus(root = document) {
    root.querySelectorAll('[data-menu-button]').forEach(bindMenu);
}
