// A member in a list: the photo, the name and the headline, with a way to follow them.
import { avatar } from '../ui/avatar.js';
import { el } from '../ui/dom.js';
import { profileUrl } from './article-card.js';
import { createFollowButton } from './follow-button.js';

/** viewer is the username of the member reading, empty for visitors, who sign in to follow. */
export function createMemberRow(member, { viewer, loginUrl }) {
    const url = profileUrl(member.username);
    let action = null;
    if (!viewer) {
        action = el(
            'a',
            { class: 'btn btn--primary btn--sm follow-btn', href: loginUrl },
            'Seguir',
            el('span', { class: 'u-visually-hidden', text: ` ${member.display_name}` }),
        );
    } else if (viewer !== member.username) {
        action = createFollowButton(member);
    }

    return el(
        'li',
        { class: 'member-row' },
        // The name is the link people use; the photo repeats it for the pointer only.
        el('a', { href: url, tabindex: '-1', 'aria-hidden': 'true' }, avatar(member.display_name, 'md', member.avatar_url)),
        el(
            'div',
            { class: 'member-row__text' },
            el('a', { class: 'member-row__name', href: url, text: member.display_name }),
            el('span', { class: 'member-row__detail', text: member.headline || `@${member.username}` }),
        ),
        action,
    );
}
