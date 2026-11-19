import { el } from './dom.js';

const AVATAR_COLORS = 8;

// Same rules as template_helpers.py, so a member looks the same in pages and in lists.
export function initials(name) {
    const words = (name || '').trim().split(/\s+/).filter(Boolean);
    if (!words.length) return '?';

    const first = [...words[0]][0];
    const last = words.length > 1 ? [...words[words.length - 1]][0] : '';
    return (first + last).toUpperCase();
}

export function avatarColor(name) {
    let value = 0;
    for (const character of name || '') {
        value = (Math.imul(value, 31) + character.codePointAt(0)) >>> 0;
    }
    return value % AVATAR_COLORS;
}

/**
 * The member's photo when there is one, their initials otherwise. Photos load when
 * they get near the screen, unless eager asks for them at once.
 */
export function avatar(name, size = 'md', imageUrl = null, { eager = false } = {}) {
    if (imageUrl) {
        // The name is always shown next to it, so the photo needs no text of its own.
        return el('img', {
            class: `avatar avatar--${size}`,
            src: imageUrl,
            alt: '',
            loading: eager ? null : 'lazy',
            decoding: 'async',
        });
    }

    return el('span', {
        class: `avatar avatar--${size} avatar--c${avatarColor(name)}`,
        'aria-hidden': 'true',
        text: initials(name),
    });
}
