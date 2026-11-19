// Rules shared by the pages that list and edit articles.
import { setFieldError } from './ui/forms.js';

export function newestFirst(articles) {
    return [...articles].sort((a, b) => new Date(b.publish_date) - new Date(a.publish_date)
        || b.article_id - a.article_id);
}

export function foundLabel(count) {
    const plural = count === 1 ? '' : 's';
    return `${count} artigo${plural} encontrado${plural}.`;
}

/** Check the title and content fields. Returns the values, or null after flagging the errors. */
export function readArticleFields(titleInput, contentInput) {
    const title = titleInput.value.trim();
    const content = contentInput.value;
    const invalid = [];

    if (!title) {
        setFieldError(titleInput, 'O título não pode ficar em branco.');
        invalid.push(titleInput);
    }
    if (!content.trim()) {
        setFieldError(contentInput, 'O conteúdo não pode ficar em branco.');
        invalid.push(contentInput);
    }

    if (invalid.length) {
        invalid[0].focus();
        return null;
    }
    return { title, content };
}
