// Runs before the page is drawn, so a theme picked in the account menu applies without a flash.
(function () {
    try {
        var theme = localStorage.getItem('theme');
        if (theme === 'light' || theme === 'dark') {
            document.documentElement.dataset.theme = theme;
        }
    } catch (error) {
        // Storage can be blocked; the system theme still applies.
        console.warn('Could not read the stored theme', error);
    }
})();
