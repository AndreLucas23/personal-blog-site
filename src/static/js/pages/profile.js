import { API } from '../api.js';
import { appendArticles, showArticles, showLoadError, showSkeletons } from '../components/article-feed.js';
import { bindFollowButton } from '../components/follow-button.js';
import { createLoadMore } from '../components/load-more.js';

const feed = document.getElementById('profile-feed');
const publishedPanel = document.getElementById('published-panel');
const draftsFeed = document.getElementById('drafts-feed');
const publishedTab = document.getElementById('tab-published');
const draftsTab = document.getElementById('tab-drafts');
const { username, own } = feed.dataset;

let draftsLoaded = false;

const followButton = document.querySelector('.profile button[data-follow]');
if (followButton) {
    const followersCount = document.getElementById('profile-followers');
    const followersLabel = document.getElementById('profile-followers-label');
    const showFollowers = (count) => {
        followersCount.textContent = count;
        followersLabel.textContent = count === 1 ? 'seguidor' : 'seguidores';
    };
    // The last count the server gave, and whether the viewer followed at that point.
    let confirmed = {
        followers: Number(followersCount.textContent),
        followed: followButton.dataset.followed === 'true',
    };

    bindFollowButton(followButton, {
        onChange({ followed, followers }) {
            if (followers === null) {
                // The count moves with the button, until the server gives the real one.
                showFollowers(confirmed.followers + Number(followed) - Number(confirmed.followed));
                return;
            }
            confirmed = { followers, followed };
            showFollowers(followers);
        },
    });
}

const more = createLoadMore(document.getElementById('profile-more'), {
    fetchPage: (cursor) => API.fetchArticlesBy(username, cursor),
    add: ({ articles }) => appendArticles(feed, articles),
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
