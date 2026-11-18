import { API } from '../api.js';
import { bindLikeButton } from '../components/like-button.js';
import { bindDialog } from '../ui/dialog.js';
import { showToast } from '../ui/toast.js';
import { bindCounter, setFieldError } from '../ui/forms.js';

const likeButton = document.querySelector('.article .like-btn');
if (likeButton) bindLikeButton(likeButton);

const editButton = document.getElementById('edit-btn');
if (editButton) setUpEditor();

function setUpEditor() {
    const dialog = document.getElementById('edit-dialog');
    const form = document.getElementById('edit-form');
    const titleInput = document.getElementById('edit-title');
    const contentInput = document.getElementById('edit-content');
    const submitButton = document.getElementById('edit-submit');
    const titleView = document.getElementById('view-title');
    const contentView = document.getElementById('view-content');
    const articleId = document.querySelector('.article').dataset.articleId;

    const updateTitleCounter = bindCounter(titleInput, document.getElementById('edit-title-counter'));
    const updateContentCounter = bindCounter(contentInput, document.getElementById('edit-content-counter'));

    bindDialog(dialog);

    editButton.addEventListener('click', () => {
        titleInput.value = titleView.textContent;
        contentInput.value = contentView.textContent;
        updateTitleCounter();
        updateContentCounter();
        setFieldError(titleInput, '');
        setFieldError(contentInput, '');
        dialog.showModal();
        titleInput.focus();
    });

    form.addEventListener('submit', async (event) => {
        event.preventDefault();

        const title = titleInput.value.trim();
        const content = contentInput.value;
        let valid = true;

        if (!title) {
            setFieldError(titleInput, 'O título não pode ficar em branco.');
            valid = false;
        }
        if (!content.trim()) {
            setFieldError(contentInput, 'O conteúdo não pode ficar em branco.');
            valid = false;
        }
        if (!valid) {
            form.querySelector('[aria-invalid="true"]').focus();
            return;
        }

        submitButton.classList.add('is-loading');
        submitButton.disabled = true;

        try {
            await API.update(articleId, { title, content });
            titleView.textContent = title;
            contentView.textContent = content;
            document.title = `${title} | Social Blog`;
            dialog.close();
            showToast('Artigo atualizado.', { type: 'success' });
        } catch (error) {
            console.error(error);
            showToast('Não foi possível salvar o artigo. Tente de novo.', { type: 'error' });
        } finally {
            submitButton.classList.remove('is-loading');
            submitButton.disabled = false;
        }
    });
}
