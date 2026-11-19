import { ApiError, API } from '../api.js';
import { foundLabel } from '../articles.js';
import { appendArticles, showArticles, showLoadError, showSkeletons } from '../components/article-feed.js';
import { createLoadMore } from '../components/load-more.js';

const SEARCH_DELAY_MS = 250;

const feed = document.getElementById('feed');
const searchInput = document.getElementById('feed-search');
const statusEl = document.getElementById('feed-status');
const more = createLoadMore(document.getElementById('feed-more'), {
    fetchPage: (cursor) => API.fetchAll(cursor),
    add: (articles) => appendArticles(feed, articles),
});

let searchTimer = null;
// Every load and search takes a number. Only the latest one may draw the feed.
let currentRun = 0;

async function loadArticles() {
    const run = ++currentRun;
    statusEl.textContent = '';
    more.setVisible(false);
    showSkeletons(feed);

    try {
        const { articles, next_cursor: nextCursor } = await API.fetchAll();
        if (run !== currentRun) return;
        showArticles(feed, articles, {
            title: 'Nenhum artigo por aqui ainda',
            text: 'Quando alguém publicar, os artigos aparecem aqui.',
        }, { keepOrder: true });
        more.start(nextCursor);
    } catch (error) {
        console.error(error);
        if (run === currentRun) showLoadError(feed);
    }
}

async function search(query) {
    // An empty search shows the full list again, with likes made in the meantime.
    if (!query) {
        loadArticles();
        return;
    }

    const run = ++currentRun;
    // The results are the whole answer, so they have no pages to follow.
    more.setVisible(false);
    const noResults = {
        iconName: 'search',
        title: 'Nenhum artigo encontrado',
        text: `Nenhum título contém “${query}”.`,
    };

    try {
        const results = await API.searchByTitle(query);
        if (run !== currentRun) return;
        statusEl.textContent = results.length ? foundLabel(results.length) : '';
        showArticles(feed, results, noResults);
    } catch (error) {
        if (run !== currentRun) return;
        // The search route answers 404 for queries it cannot take, such as one with a slash.
        if (error instanceof ApiError && error.status === 404) {
            statusEl.textContent = '';
            showArticles(feed, [], noResults);
            return;
        }
        console.error(error);
        statusEl.textContent = 'Não foi possível buscar agora. Tente de novo em instantes.';
        feed.removeAttribute('aria-busy');
    }
}

searchInput.addEventListener('input', () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => search(searchInput.value.trim()), SEARCH_DELAY_MS);
});

loadArticles();
