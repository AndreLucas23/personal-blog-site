import { API } from '../api.js';
import { bindLikeButton } from '../components/like-button.js';
import { confirmDialog } from '../ui/dialog.js';
import { isLaterDay } from '../ui/format.js';
import { showToast, showToastAfterLeaving } from '../ui/toast.js';

const article = document.querySelector('.article');

// The server tells a later day in UTC; the dates on the page are in the reader's zone.
const updatedNote = article.querySelector('[data-updated-after]');
if (updatedNote) {
    const updated = updatedNote.querySelector('time').dateTime;
    updatedNote.hidden = !isLaterDay(updated, updatedNote.dataset.updatedAfter);
}

const likeButton = article.querySelector('.like-btn');
if (likeButton) bindLikeButton(likeButton);

// The author deletes; an admin removes for moderation. Both go through the same request.
const deleteButton = article.querySelector('[data-delete-article]');
if (deleteButton) {
    deleteButton.addEventListener('click', async () => {
        const { confirmTitle, confirmMessage, confirmLabel, doneMessage, next } = deleteButton.dataset;
        const confirmed = await confirmDialog({
            title: confirmTitle,
            message: confirmMessage,
            confirmLabel,
            danger: true,
        });
        if (!confirmed) return;

        deleteButton.disabled = true;
        try {
            await API.deleteArticle(article.dataset.articleId);
            showToastAfterLeaving(doneMessage, { type: 'success' });
            window.location.assign(next);
        } catch (error) {
            console.error(error);
            showToast('Não foi possível excluir o artigo. Tente de novo.', { type: 'error' });
            deleteButton.disabled = false;
        }
    });
}
