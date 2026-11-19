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

const PENDING_KEY = 'pendingToast';

/** Show a message on the next page, for actions that end by leaving this one. */
export function showToastAfterLeaving(message, options = {}) {
    try {
        sessionStorage.setItem(PENDING_KEY, JSON.stringify({ message, options }));
    } catch (error) {
        console.warn('Could not keep the message for the next page', error);
    }
}

export function showPendingToast() {
    let pending = null;
    try {
        pending = JSON.parse(sessionStorage.getItem(PENDING_KEY));
        sessionStorage.removeItem(PENDING_KEY);
    } catch (error) {
        console.warn('Could not read the message left by the previous page', error);
    }
    if (pending?.message) showToast(pending.message, pending.options);
}
