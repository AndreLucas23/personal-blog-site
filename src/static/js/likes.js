import { API } from "./api.js";

const SVG_NAMESPACE = 'http://www.w3.org/2000/svg';
const HEART_PATH = 'M320 560L130 372C74 316 74 224 130 168C186 112 276 116 320 184'
    + 'C364 116 454 112 510 168C566 224 566 316 510 372Z';

export function renderLikeState(button, { liked, likes }) {
    button.classList.toggle('is-liked', liked);
    button.setAttribute('aria-pressed', String(liked));
    button.setAttribute('aria-label', liked ? 'Descurtir artigo' : 'Curtir artigo');
    button.querySelector('.c-like__count').textContent = likes;
}

export function bindLikeButton(button) {
    button.addEventListener('click', async () => {
        const isLiked = button.getAttribute('aria-pressed') === 'true';
        const articleId = button.dataset.articleId;
        button.disabled = true;

        try {
            const result = isLiked ? await API.unlike(articleId) : await API.like(articleId);
            renderLikeState(button, result);
        } catch (err) {
            console.error(err);
        } finally {
            button.disabled = false;
        }
    });
}

export function createLikeButton(article, ...classNames) {
    const button = document.createElement('button');
    button.type = 'button';
    button.classList.add('c-like', ...classNames);
    button.dataset.articleId = article.article_id;

    const svg = document.createElementNS(SVG_NAMESPACE, 'svg');
    svg.setAttribute('viewBox', '0 0 640 640');
    svg.setAttribute('aria-hidden', 'true');
    svg.classList.add('c-like__icon');

    const path = document.createElementNS(SVG_NAMESPACE, 'path');
    path.setAttribute('d', HEART_PATH);
    svg.appendChild(path);

    const count = document.createElement('span');
    count.classList.add('c-like__count');

    button.append(svg, count);
    renderLikeState(button, { liked: article.liked, likes: article.likes });
    bindLikeButton(button);

    return button;
}
