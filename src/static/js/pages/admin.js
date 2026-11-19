import { API } from '../api.js';
import { foundLabel, newestFirst, readArticleFields } from '../articles.js';
import { createEmptyState } from '../components/article-card.js';
import { bindDialog, confirmDialog } from '../ui/dialog.js';
import { el, icon } from '../ui/dom.js';
import { formatDate } from '../ui/format.js';
import { bindCounter } from '../ui/forms.js';
import { showToast } from '../ui/toast.js';

const SEARCH_DELAY_MS = 250;

const list = document.getElementById('admin-list');
const statusEl = document.getElementById('admin-status');
const searchInput = document.getElementById('admin-search');
const searchType = document.getElementById('admin-search-type');

let articles = [];
let searchTimer = null;
// Every load and search takes a number. Only the latest one may draw the list.
let currentRun = 0;

function createRow(article) {
    const { url } = article;

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
            el(
                'button',
                {
                    class: 'icon-btn icon-btn--danger',
                    type: 'button',
                    'aria-label': `Remover o artigo “${article.article_title}”`,
                    onClick: () => removeArticle(article),
                },
                icon('trash'),
            ),
        ),
    );
}

function render(items, emptyState) {
    list.replaceChildren(...(items.length
        ? newestFirst(items).map(createRow)
        : [el('li', {}, createEmptyState(emptyState))]));
}

function showLoadError() {
    statusEl.textContent = '';
    list.replaceChildren(el('li', {}, createEmptyState({
        iconName: 'alert',
        title: 'Não foi possível carregar os artigos',
        text: 'Verifique sua conexão e recarregue a página.',
    })));
}

function renderAll() {
    statusEl.textContent = '';
    render(articles, {
        title: 'Nenhum artigo publicado',
        text: 'Use o botão Novo artigo para publicar o primeiro.',
    });
}

async function loadArticles() {
    const run = ++currentRun;

    try {
        const loaded = await API.fetchAll();
        if (run !== currentRun) return;
        articles = loaded;
        // A search typed while loading stays on screen.
        if (searchInput.value.trim()) runSearch();
        else renderAll();
    } catch (error) {
        console.error(error);
        if (run === currentRun) showLoadError();
    } finally {
        list.removeAttribute('aria-busy');
    }
}

async function runSearch() {
    const query = searchInput.value.trim();
    const type = searchType.value;
    const run = ++currentRun;
    const noResults = { iconName: 'search', title: 'Nenhum artigo encontrado' };

    if (!query) {
        renderAll();
        return;
    }

    if (type === 'id' && !/^\d+$/.test(query)) {
        statusEl.textContent = 'O ID tem apenas números.';
        render([], noResults);
        return;
    }

    try {
        const results = type === 'title' ? await API.searchByTitle(query) : await API.searchById(query);
        if (run !== currentRun) return;
        statusEl.textContent = foundLabel(results.length);
        render(results, noResults);
    } catch (error) {
        if (run !== currentRun) return;
        console.error(error);
        if (error.status === 404) {
            statusEl.textContent = foundLabel(0);
            render([], noResults);
        } else {
            statusEl.textContent = 'Não foi possível buscar agora. Tente de novo em instantes.';
        }
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
        await API.deleteArticle(article.article_id);
    } catch (error) {
        console.error(error);
        showToast('Não foi possível remover o artigo. Tente de novo.', { type: 'error' });
        return;
    }

    showToast('Artigo removido.', { type: 'success' });
    loadArticles();
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

        const fields = readArticleFields(titleInput, contentInput);
        if (!fields) return;

        submitButton.classList.add('is-loading');
        submitButton.disabled = true;

        try {
            await API.createArticle({ title: fields.title, content: fields.content });
        } catch (error) {
            console.error(error);
            showToast('Não foi possível publicar o artigo. Tente de novo.', { type: 'error' });
            return;
        } finally {
            submitButton.classList.remove('is-loading');
            submitButton.disabled = false;
        }

        form.reset();
        updateTitleCounter();
        updateContentCounter();
        dialog.close();
        showToast('Artigo publicado.', { type: 'success' });
        // A failure here only affects the list, which shows its own error.
        loadArticles();
    });
}

searchInput.addEventListener('input', () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(runSearch, SEARCH_DELAY_MS);
});
searchType.addEventListener('change', runSearch);

setUpNewArticle();
loadArticles();
