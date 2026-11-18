import { el, icon } from './dom.js';

const ICONS = { info: 'info', success: 'check', error: 'alert' };
const VISIBLE_MS = 4000;

export function showToast(message, { type = 'info' } = {}) {
    const region = document.getElementById('toasts');
    if (!region) return;

    const toast = el(
        'div',
        { class: `toast toast--${type}`, role: type === 'error' ? 'alert' : 'status' },
        icon(ICONS[type] || ICONS.info),
        el('span', { text: message }),
    );
    region.append(toast);

    setTimeout(() => {
        toast.classList.add('is-leaving');
        setTimeout(() => toast.remove(), 250);
    }, VISIBLE_MS);
}
