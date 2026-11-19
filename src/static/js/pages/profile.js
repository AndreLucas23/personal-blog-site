import { API } from '../api.js';
import { newestFirst } from '../articles.js';
import { createArticleCard, createArticleSkeleton, createEmptyState } from '../components/article-card.js';

const SKELETONS = 2;

const feed = document.getElementById('profile-feed');
const { username, own } = feed.dataset;

async function loadArticles() {
    feed.replaceChildren(...Array.from({ length: SKELETONS }, createArticleSkeleton));

    try {
        const articles = await API.fetchArticlesBy(username);
        feed.replaceChildren(...(articles.length
            ? newestFirst(articles).map(createArticleCard)
            : [createEmptyState(own === 'true'
                ? { title: 'Você ainda não publicou', text: 'Seus artigos aparecem aqui.' }
                : { title: 'Nenhum artigo publicado ainda' })]));
    } catch (error) {
        console.error(error);
        feed.replaceChildren(createEmptyState({
            iconName: 'alert',
            title: 'Não foi possível carregar os artigos',
            text: 'Verifique sua conexão e recarregue a página.',
        }));
    } finally {
        feed.removeAttribute('aria-busy');
    }
}

loadArticles();
