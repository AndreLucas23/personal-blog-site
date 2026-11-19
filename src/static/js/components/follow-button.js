import { API } from '../api.js';
import { showToast } from '../ui/toast.js';

function renderFollowState(button, followed) {
    button.setAttribute('aria-pressed', String(followed));
    button.classList.toggle('btn--primary', !followed);
    button.classList.toggle('btn--secondary', followed);
    button.querySelector('.follow-btn__text').textContent = followed ? 'Seguindo' : 'Seguir';
}

/** Follow or unfollow on click. onChange gets the answer, with the new count of followers. */
export function bindFollowButton(button, { onChange } = {}) {
    let busy = false;

    button.addEventListener('click', async () => {
        // Not disabled while it waits, which would take the focus away from keyboard users.
        if (busy) return;
        busy = true;
        const wasFollowed = button.getAttribute('aria-pressed') === 'true';
        // Show the result at once and undo it if the server refuses.
        renderFollowState(button, !wasFollowed);

        try {
            const username = button.dataset.follow;
            const result = wasFollowed ? await API.unfollow(username) : await API.follow(username);
            renderFollowState(button, result.followed);
            onChange?.(result);
        } catch (error) {
            console.error(error);
            renderFollowState(button, wasFollowed);
            showToast(wasFollowed
                ? 'Não foi possível deixar de seguir agora. Tente de novo.'
                : 'Não foi possível seguir agora. Tente de novo.', { type: 'error' });
        } finally {
            busy = false;
        }
    });
}
