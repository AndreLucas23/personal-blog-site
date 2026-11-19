import { API } from '../api.js';
import { showArticles, showLoadError, showSkeletons } from '../components/article-feed.js';

const feed = document.getElementById('profile-feed');
const { username, own } = feed.dataset;

async function loadArticles() {
    showSkeletons(feed, 2);

    try {
        const articles = await API.fetchArticlesBy(username);
        showArticles(feed, articles, own === 'true'
            ? { title: 'Você ainda não publicou', text: 'Seus artigos aparecem aqui.' }
            : { title: 'Nenhum artigo publicado ainda' });
    } catch (error) {
        console.error(error);
        showLoadError(feed);
    }
}

loadArticles();
