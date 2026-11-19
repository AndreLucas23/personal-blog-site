// The "Mais artigos" button after a list that comes in pages.
import { showToast } from '../ui/toast.js';

/**
 * fetchPage(cursor) answers {articles, next_cursor}. add(articles) draws them after the
 * ones shown and returns the element that takes the focus, such as the first new link.
 */
export function createLoadMore(button, { fetchPage, add }) {
    let cursor = null;
    let visible = true;
    let loading = false;
    // Every first page starts a new list, which a page that arrives late must not join.
    let list = 0;

    const update = () => { button.hidden = !cursor || !visible; };

    button.addEventListener('click', async () => {
        if (!cursor || loading) return;
        const askedFor = list;
        loading = true;
        // Not disabled, which would take the focus away from keyboard users.
        button.setAttribute('aria-disabled', 'true');
        button.classList.add('is-loading');

        try {
            const page = await fetchPage(cursor);
            if (askedFor !== list || !visible) return;
            const first = add(page.articles);
            cursor = page.next_cursor;
            update();
            // People who read with the keyboard or a screen reader go on from the new articles.
            first?.focus();
        } catch (error) {
            console.error(error);
            showToast('Não foi possível carregar mais artigos. Tente de novo.', { type: 'error' });
        } finally {
            loading = false;
            button.removeAttribute('aria-disabled');
            button.classList.remove('is-loading');
        }
    });

    return {
        /** A first page is on screen, and nextCursor continues it. */
        start(nextCursor) {
            list += 1;
            cursor = nextCursor;
            visible = true;
            update();
        },
        /** Hide the button while the list gives way to something else, such as a search. */
        setVisible(value) {
            visible = value;
            update();
        },
    };
}
