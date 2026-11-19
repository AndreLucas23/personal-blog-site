import { ApiError, API } from '../api.js';
import { foundLabel, newestFirst } from '../articles.js';
import { createArticleCard, createArticleSkeleton, createEmptyState } from '../components/article-card.js';

const SEARCH_DELAY_MS = 250;
const SKELETONS = 3;

const feed = document.getElementById('feed');
const searchInput = document.getElementById('feed-search');
const statusEl = document.getElementById('feed-status');

let searchTimer = null;
// Every load and search takes a number. Only the latest one may draw the feed.
let currentRun = 0;

function render(articles, emptyState) {
    feed.replaceChildren(...(articles.length
        ? newestFirst(articles).map(createArticleCard)
        : [createEmptyState(emptyState)]));
}

async function loadArticles() {
    const run = ++currentRun;
    statusEl.textContent = '';
    feed.setAttribute('aria-busy', 'true');
    feed.replaceChildren(...Array.from({ length: SKELETONS }, createArticleSkeleton));

    try {
        const articles = await API.fetchAll();
        if (run !== currentRun) return;
        render(articles, {
            title: 'Nenhum artigo por aqui ainda',
            text: 'Quando alguém publicar, os artigos aparecem aqui.',
        });
    } catch (error) {
        console.error(error);
        if (run !== currentRun) return;
        feed.replaceChildren(createEmptyState({
            iconName: 'alert',
            title: 'Não foi possível carregar os artigos',
            text: 'Verifique sua conexão e recarregue a página.',
        }));
    } finally {
        if (run === currentRun) feed.removeAttribute('aria-busy');
    }
}

async function search(query) {
    // An empty search shows the full list again, with likes made in the meantime.
    if (!query) {
        loadArticles();
        return;
    }

    const run = ++currentRun;
    const noResults = {
        iconName: 'search',
        title: 'Nenhum artigo encontrado',
        text: `Nenhum título contém “${query}”.`,
    };

    try {
        const results = await API.searchByTitle(query);
        if (run !== currentRun) return;
        statusEl.textContent = results.length ? foundLabel(results.length) : '';
        render(results, noResults);
    } catch (error) {
        if (run !== currentRun) return;
        // The search route answers 404 for queries it cannot take, such as one with a slash.
        if (error instanceof ApiError && error.status === 404) {
            statusEl.textContent = '';
            render([], noResults);
            return;
        }
        console.error(error);
        statusEl.textContent = 'Não foi possível buscar agora. Tente de novo em instantes.';
    } finally {
        if (run === currentRun) feed.removeAttribute('aria-busy');
    }
}

searchInput.addEventListener('input', () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => search(searchInput.value.trim()), SEARCH_DELAY_MS);
});

loadArticles();
