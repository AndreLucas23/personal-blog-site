// The theme choice in the account menu. js/theme.js applies the stored choice on load.
const STORAGE_KEY = 'theme';
const THEMES = ['light', 'dark'];

function storedTheme() {
    try {
        return localStorage.getItem(STORAGE_KEY) || 'system';
    } catch {
        return 'system';
    }
}

function storeTheme(theme) {
    try {
        if (THEMES.includes(theme)) localStorage.setItem(STORAGE_KEY, theme);
        else localStorage.removeItem(STORAGE_KEY);
    } catch {
        // Without storage the choice lasts until the page closes.
    }
}

function applyTheme(theme) {
    if (THEMES.includes(theme)) document.documentElement.dataset.theme = theme;
    else delete document.documentElement.dataset.theme;
}

export function initThemePicker() {
    const buttons = document.querySelectorAll('[data-theme-choice]');
    const mark = (theme) => buttons.forEach((button) => {
        button.setAttribute('aria-checked', String(button.dataset.themeChoice === theme));
    });

    mark(storedTheme());
    buttons.forEach((button) => button.addEventListener('click', () => {
        const theme = button.dataset.themeChoice;
        storeTheme(theme);
        applyTheme(theme);
        mark(theme);
    }));
}
