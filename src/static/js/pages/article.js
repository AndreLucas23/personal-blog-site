import { API } from '../api.js';
import { bindLikeButton } from '../components/like-button.js';
import { confirmDialog } from '../ui/dialog.js';
import { showToast, showToastAfterLeaving } from '../ui/toast.js';

const article = document.querySelector('.article');

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
