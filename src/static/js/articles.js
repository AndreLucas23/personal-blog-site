// Rules shared by the pages that list articles.

export function newestFirst(articles) {
    return [...articles].sort((a, b) => new Date(b.publish_date) - new Date(a.publish_date)
        || b.article_id - a.article_id);
}

export function foundLabel(count) {
    const plural = count === 1 ? '' : 's';
    return `${count} artigo${plural} encontrado${plural}.`;
}
