import { avatar } from '../ui/avatar.js';
import { el, icon } from '../ui/dom.js';
import { formatDateTime, isoString, timeAgo } from '../ui/format.js';
import { createLikeButton } from './like-button.js';


export function profileUrl(username) {
    return `/@${encodeURIComponent(username)}`;
}

function createTime(article) {
    // A draft has no publication date yet; what matters is when it was last touched.
    if (article.status === 'draft') {
        const edited = article.updated_at || article.created_at;
        return el('span', { class: 'post__time', text: `Rascunho · editado ${timeAgo(edited)}` });
    }
    return el('time', {
        class: 'post__time',
        datetime: isoString(article.publish_date),
        title: formatDateTime(article.publish_date),
        text: timeAgo(article.publish_date),
    });
}

function createTags(tags) {
    if (!tags?.length) return null;
    return el(
        'ul',
        { class: 'post__tags', 'aria-label': 'Tags' },
        ...tags.map((tag) => el('li', { class: 'chip', text: tag })),
    );
}

function createAuthor(article) {
    const url = profileUrl(article.author_username);

    return el(
        'header',
        { class: 'post__header' },
        // The name is the link people use; the photo repeats it for the pointer only.
        el(
            'a',
            { href: url, tabindex: '-1', 'aria-hidden': 'true' },
            avatar(article.author, 'md', article.author_avatar_url),
        ),
        el(
            'div',
            { class: 'post__meta' },
            el('a', { class: 'post__author', href: url, text: article.author }),
            createTime(article),
        ),
    );
}

export function createArticleCard(article) {
    const isDraft = article.status === 'draft';
    // A draft card leads back to the editor; nobody else can like or read it yet.
    const url = isDraft ? `/write/${article.article_id}` : article.url;
    const titleId = `article-title-${article.article_id}`;

    return el(
        'article',
        { class: 'card post', 'aria-labelledby': titleId },
        createAuthor(article),
        el(
            'a',
            { class: 'post__link', href: url },
            el('h2', { class: 'post__title', id: titleId, text: article.article_title }),
            article.excerpt ? el('p', { class: 'post__excerpt', text: article.excerpt }) : null,
        ),
        createTags(article.tags),
        el(
            'footer',
            { class: 'post__footer' },
            el('div', { class: 'post__actions' }, isDraft ? null : createLikeButton(article)),
            el(
                'a',
                { class: 'btn btn--ghost btn--sm', href: url },
                el('span', { text: isDraft ? 'Continuar editando' : 'Ler artigo' }),
                icon(isDraft ? 'pen' : 'arrow-right', 'icon--sm'),
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
