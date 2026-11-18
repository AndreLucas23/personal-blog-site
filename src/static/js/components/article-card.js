import { avatar } from '../ui/avatar.js';
import { el, icon } from '../ui/dom.js';
import { excerpt, formatDateTime, timeAgo } from '../ui/format.js';
import { createLikeButton } from './like-button.js';

export function articleUrl(article) {
    return `/open/${article.article_id}`;
}

export function createArticleCard(article) {
    const author = article.author || 'Membro removido';
    const url = articleUrl(article);
    const titleId = `article-title-${article.article_id}`;

    return el(
        'article',
        { class: 'card post', 'aria-labelledby': titleId },
        el(
            'header',
            { class: 'post__header' },
            avatar(author, 'md'),
            el(
                'div',
                { class: 'post__meta' },
                el('span', { class: 'post__author', text: author }),
                el('time', {
                    class: 'post__time',
                    datetime: new Date(article.publish_date).toISOString(),
                    title: formatDateTime(article.publish_date),
                    text: timeAgo(article.publish_date),
                }),
            ),
        ),
        el(
            'a',
            { class: 'post__link', href: url },
            el('h2', { class: 'post__title', id: titleId, text: article.article_title }),
            el('p', { class: 'post__excerpt', text: excerpt(article.article_content) }),
        ),
        el(
            'footer',
            { class: 'post__footer' },
            el('div', { class: 'post__actions' }, createLikeButton(article)),
            el(
                'a',
                { class: 'btn btn--ghost btn--sm', href: url },
                el('span', { text: 'Ler artigo' }),
                icon('arrow-right', 'icon--sm'),
            ),
        ),
    );
}

export function createArticleSkeleton() {
    return el(
        'div',
        { class: 'card post-skeleton', 'aria-hidden': 'true' },
        el(
            'div',
            { class: 'post-skeleton__header' },
            el('div', { class: 'skeleton skeleton--circle' }),
            el(
                'div',
                { class: 'post-skeleton__lines' },
                el('div', { class: 'skeleton skeleton--line' }),
                el('div', { class: 'skeleton skeleton--line' }),
            ),
        ),
        el('div', { class: 'skeleton skeleton--title' }),
        el('div', { class: 'skeleton skeleton--line' }),
        el('div', { class: 'skeleton skeleton--line' }),
    );
}

export function createEmptyState({ iconName = 'file-text', title, text }) {
    return el(
        'div',
        { class: 'card empty-state' },
        icon(iconName),
        el('p', { class: 'empty-state__title', text: title }),
        text ? el('p', { class: 'empty-state__text', text }) : null,
    );
}
