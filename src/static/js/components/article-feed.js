// Drawing a list of article cards, shared by the pages that show one.
import { newestFirst } from '../articles.js';
import { createArticleCard, createArticleSkeleton, createEmptyState } from './article-card.js';

const SKELETONS = 3;

export function showSkeletons(feed, count = SKELETONS) {
    feed.setAttribute('aria-busy', 'true');
    feed.replaceChildren(...Array.from({ length: count }, createArticleSkeleton));
}

export function showArticles(feed, articles, emptyState) {
    feed.replaceChildren(...(articles.length
        ? newestFirst(articles).map(createArticleCard)
        : [createEmptyState(emptyState)]));
    feed.removeAttribute('aria-busy');
}

export function showLoadError(feed) {
    feed.replaceChildren(createEmptyState({
        iconName: 'alert',
        title: 'Não foi possível carregar os artigos',
        text: 'Verifique sua conexão e recarregue a página.',
    }));
    feed.removeAttribute('aria-busy');
}
