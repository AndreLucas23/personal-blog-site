import { API } from '../api.js';
import { el } from '../ui/dom.js';
import { showToast } from '../ui/toast.js';

function renderFollowState(button, followed) {
    button.dataset.followed = String(followed);
    button.classList.toggle('btn--primary', !followed);
    button.classList.toggle('btn--secondary', followed);
    button.querySelector('.follow-btn__text').textContent = followed ? 'Seguindo' : 'Seguir';
}

/**
 * Follow or unfollow on click. onChange gets every state the button shows: at once with
 * followers null, then with the count the server gives, or again when it is undone.
 */
export function bindFollowButton(button, { onChange } = {}) {
    let busy = false;
    const show = (followed, followers = null) => {
        renderFollowState(button, followed);
        onChange?.({ followed, followers });
    };

    button.addEventListener('click', async () => {
        // Not disabled while it waits, which would take the focus away from keyboard users.
        if (busy) return;
        busy = true;
        const wasFollowed = button.dataset.followed === 'true';
        // Show the result at once and undo it if the server refuses.
        show(!wasFollowed);

        try {
            const username = button.dataset.follow;
            const result = wasFollowed ? await API.unfollow(username) : await API.follow(username);
            show(result.followed, result.followers);
        } catch (error) {
            console.error(error);
            show(wasFollowed);
            showToast(wasFollowed
                ? 'Não foi possível deixar de seguir agora. Tente de novo.'
                : 'Não foi possível seguir agora. Tente de novo.', { type: 'error' });
        } finally {
            busy = false;
        }
    });
}

/** The follow button of a member drawn by a script, like the one the pages draw. */
export function createFollowButton({ username, display_name: name, followed }, { size = 'btn--sm', onChange } = {}) {
    const button = el(
        'button',
        {
            class: `btn ${followed ? 'btn--secondary' : 'btn--primary'} ${size} follow-btn`,
            type: 'button',
            dataset: { follow: username, followed: String(followed) },
        },
        el('span', { class: 'follow-btn__text', text: followed ? 'Seguindo' : 'Seguir' }),
        el('span', { class: 'u-visually-hidden', text: ` ${name}` }),
    );
    bindFollowButton(button, { onChange });
    return button;
}

/**
 * What the viewer can do about a member drawn by a script, as partials/follow_button.html
 * does in the pages: nothing for themselves, a link to sign in for visitors and the button
 * for members. viewer is the username of the member reading, empty for visitors.
 */
export function createFollowAction(member, { viewer, loginUrl, onChange }) {
    if (!viewer) {
        return el(
            'a',
            { class: 'btn btn--primary btn--sm follow-btn', href: loginUrl },
            'Seguir',
            el('span', { class: 'u-visually-hidden', text: ` ${member.display_name}` }),
        );
    }
    return viewer === member.username ? null : createFollowButton(member, { onChange });
}
