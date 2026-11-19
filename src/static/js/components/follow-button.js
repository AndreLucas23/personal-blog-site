import { API } from '../api.js';
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
