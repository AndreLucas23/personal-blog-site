import { API } from '../api.js';
import { el, icon } from '../ui/dom.js';
import { formatCount } from '../ui/format.js';
import { showToast } from '../ui/toast.js';

export function renderLikeState(button, { liked, likes }) {
    button.classList.toggle('is-liked', liked);
    button.setAttribute('aria-pressed', String(liked));
    button.dataset.likes = likes;
    button.querySelector('.like-btn__count').textContent = formatCount(likes);
    button.querySelector('.like-btn__label').textContent = liked
        ? `Descurtir. ${likes} curtida${likes === 1 ? '' : 's'}`
        : `Curtir. ${likes} curtida${likes === 1 ? '' : 's'}`;
}

export function bindLikeButton(button) {
    button.addEventListener('click', async () => {
        const wasLiked = button.getAttribute('aria-pressed') === 'true';
        const likes = Number(button.dataset.likes);
        const articleId = button.dataset.articleId;

        // Show the result at once and undo it if the server refuses.
        renderLikeState(button, { liked: !wasLiked, likes: likes + (wasLiked ? -1 : 1) });
        button.disabled = true;

        try {
            const result = wasLiked ? await API.unlike(articleId) : await API.like(articleId);
            renderLikeState(button, result);
        } catch (error) {
            console.error(error);
            renderLikeState(button, { liked: wasLiked, likes });
            showToast('Não foi possível registrar a curtida. Tente de novo.', { type: 'error' });
        } finally {
            button.disabled = false;
        }
    });
}

export function createLikeButton(article) {
    const button = el(
        'button',
        { class: 'like-btn', type: 'button', dataset: { articleId: article.article_id } },
        icon('heart'),
        el('span', { class: 'like-btn__count', 'aria-hidden': 'true' }),
        el('span', { class: 'like-btn__label visually-hidden' }),
    );

    renderLikeState(button, { liked: article.liked, likes: article.likes });
    bindLikeButton(button);
    return button;
}
