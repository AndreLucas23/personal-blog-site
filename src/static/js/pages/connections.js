import { API } from '../api.js';
import { createEmptyState } from '../components/article-card.js';
import { createLoadMore } from '../components/load-more.js';
import { createMemberRow } from '../components/member-row.js';
import { el } from '../ui/dom.js';

const list = document.getElementById('member-list');
const { username, name, kind, viewer, loginUrl } = list.dataset;
const own = viewer === username;

const fetchPage = (cursor) => (kind === 'followers'
    ? API.fetchFollowers(username, cursor)
    : API.fetchFollowing(username, cursor));

// On your own lists every follow changes how many people you follow.
const followingCount = own ? document.getElementById('following-count') : null;

function rowFor(member) {
    let shown = member.followed;
    const countFollow = ({ followed }) => {
        if (followed === shown) return;
        followingCount.textContent = Number(followingCount.textContent) + (followed ? 1 : -1);
        shown = followed;
    };
    return createMemberRow(member, { viewer, loginUrl, onFollowChange: followingCount ? countFollow : null });
}

const rowsFor = (members) => members.map(rowFor);

const more = createLoadMore(document.getElementById('members-more'), {
    fetchPage,
    add({ members }) {
        const rows = rowsFor(members);
        list.append(...rows);
        return rows[0]?.querySelector('.member-row__name') ?? null;
    },
    failure: 'Não foi possível carregar mais pessoas. Tente de novo.',
});

function emptyState() {
    if (kind === 'followers') {
        return own
            ? { iconName: 'users', title: 'Você ainda não tem seguidores', text: 'Quem seguir você aparece aqui.' }
            : { iconName: 'users', title: `Ninguém segue ${name} ainda` };
    }
    return own
        ? { iconName: 'user-plus', title: 'Você ainda não segue ninguém', text: 'Siga pessoas para acompanhar o que elas publicam.' }
        : { iconName: 'user-plus', title: `${name} ainda não segue ninguém` };
}

async function load() {
    try {
        const page = await fetchPage(null);
        list.replaceChildren(...(page.members.length
            ? rowsFor(page.members)
            : [el('li', {}, createEmptyState(emptyState()))]));
        more.start(page.next_cursor);
    } catch (error) {
        console.error(error);
        list.replaceChildren(el('li', {}, createEmptyState({
            iconName: 'alert',
            title: 'Não foi possível carregar a lista',
            text: 'Verifique sua conexão e recarregue a página.',
        })));
    } finally {
        list.removeAttribute('aria-busy');
    }
}

load();
