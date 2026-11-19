import { API } from '../api.js';
import { appendArticles, showArticles, showLoadError, showSkeletons } from '../components/article-feed.js';
import { createLoadMore } from '../components/load-more.js';

const feed = document.getElementById('profile-feed');
const publishedPanel = document.getElementById('published-panel');
const draftsFeed = document.getElementById('drafts-feed');
const publishedTab = document.getElementById('tab-published');
const draftsTab = document.getElementById('tab-drafts');
const { username, own } = feed.dataset;

let draftsLoaded = false;

const more = createLoadMore(document.getElementById('profile-more'), {
    fetchPage: (cursor) => API.fetchArticlesBy(username, cursor),
    add: (articles) => appendArticles(feed, articles),
});

async function loadArticles() {
    showSkeletons(feed, 2);

    try {
        const { articles, next_cursor: nextCursor } = await API.fetchArticlesBy(username);
        showArticles(feed, articles, own === 'true'
            ? { title: 'Você ainda não publicou', text: 'Seus artigos aparecem aqui.' }
            : { title: 'Nenhum artigo publicado ainda' }, { keepOrder: true });
        more.start(nextCursor);
    } catch (error) {
        console.error(error);
        showLoadError(feed);
    }
}

async function loadDrafts() {
    draftsLoaded = true;
    showSkeletons(draftsFeed, 2);

    try {
        const drafts = await API.fetchDrafts();
        // Drafts keep their own order: the most recently edited first.
        showArticles(draftsFeed, drafts, {
            iconName: 'pen',
            title: 'Nenhum rascunho',
            text: 'Os artigos que você salvar sem publicar aparecem aqui.',
        }, { keepOrder: true });
    } catch (error) {
        draftsLoaded = false;
        console.error(error);
        showLoadError(draftsFeed);
    }
}

function showTab(tab) {
    const drafts = tab === draftsTab;
    publishedTab.setAttribute('aria-selected', String(!drafts));
    draftsTab.setAttribute('aria-selected', String(drafts));
    publishedTab.tabIndex = drafts ? -1 : 0;
    draftsTab.tabIndex = drafts ? 0 : -1;
    publishedPanel.hidden = drafts;
    draftsFeed.hidden = !drafts;
    if (drafts && !draftsLoaded) loadDrafts();
}

if (draftsTab) {
    [publishedTab, draftsTab].forEach((tab) => {
        tab.addEventListener('click', () => showTab(tab));
        tab.addEventListener('keydown', (event) => {
            if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return;
            const other = tab === publishedTab ? draftsTab : publishedTab;
            showTab(other);
            other.focus();
        });
    });
}

loadArticles();
