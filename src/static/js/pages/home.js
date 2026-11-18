import { API } from '../api.js';
import { createArticleCard, createArticleSkeleton, createEmptyState } from '../components/article-card.js';

const SEARCH_DELAY_MS = 250;
const SKELETONS = 3;

const feed = document.getElementById('feed');
const searchInput = document.getElementById('feed-search');
const statusEl = document.getElementById('feed-status');

let articles = [];
let searchTimer = null;
let searchRun = 0;

function newestFirst(list) {
    return [...list].sort((a, b) => new Date(b.publish_date) - new Date(a.publish_date)
        || b.article_id - a.article_id);
}

function render(list, emptyState) {
    feed.replaceChildren(...(list.length
        ? newestFirst(list).map(createArticleCard)
        : [createEmptyState(emptyState)]));
}

function showError() {
    feed.replaceChildren(createEmptyState({
        iconName: 'alert',
        title: 'Não foi possível carregar os artigos',
        text: 'Verifique sua conexão e recarregue a página.',
    }));
}

async function loadArticles() {
    feed.replaceChildren(...Array.from({ length: SKELETONS }, createArticleSkeleton));

    try {
        articles = await API.fetchAll();
        render(articles, {
            title: 'Nenhum artigo por aqui ainda',
            text: 'Quando alguém publicar, os artigos aparecem aqui.',
        });
    } catch (error) {
        console.error(error);
        showError();
    } finally {
        feed.removeAttribute('aria-busy');
    }
}

async function search(query) {
    const run = ++searchRun;

    if (!query) {
        statusEl.textContent = '';
        render(articles, { title: 'Nenhum artigo por aqui ainda' });
        return;
    }

    try {
        const results = await API.searchByTitle(query);
        // A slower answer to an older query must not replace the current one.
        if (run !== searchRun) return;

        statusEl.textContent = results.length
            ? `${results.length} artigo${results.length > 1 ? 's' : ''} encontrado${results.length > 1 ? 's' : ''}.`
            : '';
        render(results, {
            iconName: 'search',
            title: 'Nenhum artigo encontrado',
            text: `Nenhum título contém “${query}”.`,
        });
    } catch (error) {
        console.error(error);
        if (run === searchRun) showError();
    }
}

searchInput.addEventListener('input', () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => search(searchInput.value.trim()), SEARCH_DELAY_MS);
});

loadArticles();
