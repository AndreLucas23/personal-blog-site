import { API } from '../api.js';
import { createEmptyState } from '../components/article-card.js';
import { bindDialog, confirmDialog } from '../ui/dialog.js';
import { el, icon } from '../ui/dom.js';
import { formatDate } from '../ui/format.js';
import { bindCounter, setFieldError } from '../ui/forms.js';
import { showToast } from '../ui/toast.js';

const SEARCH_DELAY_MS = 250;

const list = document.getElementById('admin-list');
const statusEl = document.getElementById('admin-status');
const searchInput = document.getElementById('admin-search');
const searchType = document.getElementById('admin-search-type');

let articles = [];
let searchTimer = null;
let searchRun = 0;

function newestFirst(items) {
    return [...items].sort((a, b) => new Date(b.publish_date) - new Date(a.publish_date)
        || b.article_id - a.article_id);
}

function createRow(article) {
    const url = `/open/${article.article_id}`;
    const removeButton = el(
        'button',
        {
            class: 'icon-btn icon-btn--danger',
            type: 'button',
            'aria-label': `Remover o artigo “${article.article_title}”`,
        },
        icon('trash'),
    );
    removeButton.addEventListener('click', () => removeArticle(article));

    return el(
        'li',
        { class: 'admin-row' },
        el(
            'div',
            { class: 'admin-row__main' },
            el('a', { class: 'admin-row__title', href: url, text: article.article_title }),
            el(
                'div',
                { class: 'admin-row__meta' },
                el('span', { text: `#${article.article_id}` }),
                el('span', {}, icon('user', 'icon--sm'), article.author || 'Membro removido'),
                el('span', {}, icon('calendar', 'icon--sm'), formatDate(article.publish_date)),
                el('span', {}, icon('heart', 'icon--sm'), String(article.likes)),
            ),
        ),
        el(
            'div',
            { class: 'admin-row__actions' },
            el('a', { class: 'icon-btn', href: url, 'aria-label': `Abrir o artigo “${article.article_title}”` }, icon('eye')),
            removeButton,
        ),
    );
}

function render(items, emptyState) {
    list.replaceChildren(...(items.length
        ? newestFirst(items).map(createRow)
        : [el('li', {}, createEmptyState(emptyState))]));
}

function showError() {
    list.replaceChildren(el('li', {}, createEmptyState({
        iconName: 'alert',
        title: 'Não foi possível carregar os artigos',
        text: 'Verifique sua conexão e recarregue a página.',
    })));
}

async function loadArticles() {
    try {
        articles = await API.fetchAll();
        renderCurrent();
    } catch (error) {
        console.error(error);
        showError();
    } finally {
        list.removeAttribute('aria-busy');
    }
}

function renderCurrent() {
    if (searchInput.value.trim()) {
        runSearch();
        return;
    }
    statusEl.textContent = '';
    render(articles, {
        title: 'Nenhum artigo publicado',
        text: 'Use o botão Novo artigo para publicar o primeiro.',
    });
}

async function runSearch() {
    const query = searchInput.value.trim();
    const type = searchType.value;
    const run = ++searchRun;

    if (!query) {
        renderCurrent();
        return;
    }

    if (type === 'id' && !/^\d+$/.test(query)) {
        statusEl.textContent = 'O ID tem apenas números.';
        render([], { iconName: 'search', title: 'Nenhum artigo encontrado' });
        return;
    }

    try {
        const results = type === 'title' ? await API.searchByTitle(query) : await API.searchById(query);
        if (run !== searchRun) return;

        statusEl.textContent = `${results.length} artigo${results.length === 1 ? '' : 's'} encontrado${results.length === 1 ? '' : 's'}.`;
        render(results, { iconName: 'search', title: 'Nenhum artigo encontrado' });
    } catch (error) {
        console.error(error);
        if (run === searchRun) showError();
    }
}

async function removeArticle(article) {
    const confirmed = await confirmDialog({
        title: 'Remover artigo?',
        message: `“${article.article_title}” e as curtidas dele serão apagados. Essa ação não pode ser desfeita.`,
        confirmLabel: 'Remover',
        danger: true,
    });
    if (!confirmed) return;

    try {
        await API.remove(article.article_id);
        articles = articles.filter((item) => item.article_id !== article.article_id);
        renderCurrent();
        showToast('Artigo removido.', { type: 'success' });
    } catch (error) {
        console.error(error);
        showToast('Não foi possível remover o artigo. Tente de novo.', { type: 'error' });
    }
}

function setUpNewArticle() {
    const dialog = document.getElementById('new-article-dialog');
    const form = document.getElementById('new-article-form');
    const titleInput = document.getElementById('new-title');
    const contentInput = document.getElementById('new-content');
    const submitButton = document.getElementById('new-article-submit');
    const updateTitleCounter = bindCounter(titleInput, document.getElementById('new-title-counter'));
    const updateContentCounter = bindCounter(contentInput, document.getElementById('new-content-counter'));

    bindDialog(dialog);

    document.getElementById('new-article-btn').addEventListener('click', () => {
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
            await API.add({ 'new-title': title, 'new-content': content });
            form.reset();
            updateTitleCounter();
            updateContentCounter();
            dialog.close();
            showToast('Artigo publicado.', { type: 'success' });
            articles = await API.fetchAll();
            renderCurrent();
        } catch (error) {
            console.error(error);
            showToast('Não foi possível publicar o artigo. Tente de novo.', { type: 'error' });
        } finally {
            submitButton.classList.remove('is-loading');
            submitButton.disabled = false;
        }
    });
}

searchInput.addEventListener('input', () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(runSearch, SEARCH_DELAY_MS);
});
searchType.addEventListener('change', runSearch);

setUpNewArticle();
loadArticles();
