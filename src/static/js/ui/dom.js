const SVG_NAMESPACE = 'http://www.w3.org/2000/svg';
const ICON_SPRITE = '/static/imgs/icons.svg';

/**
 * Create an element. Text always goes through textContent, so content from
 * members can never become markup.
 */
export function el(tag, props = {}, ...children) {
    const node = document.createElement(tag);

    for (const [key, value] of Object.entries(props)) {
        if (value === null || value === undefined || value === false) continue;

        if (key === 'class') node.className = value;
        else if (key === 'text') node.textContent = value;
        else if (key === 'dataset') Object.assign(node.dataset, value);
        else if (key.startsWith('on') && typeof value === 'function') {
            node.addEventListener(key.slice(2).toLowerCase(), value);
        } else node.setAttribute(key, value === true ? '' : value);
    }

    node.append(...children.filter((child) => child !== null && child !== undefined && child !== false));
    return node;
}

export function icon(name, ...classNames) {
    const svg = document.createElementNS(SVG_NAMESPACE, 'svg');
    svg.classList.add('icon', ...classNames);
    svg.setAttribute('aria-hidden', 'true');
    svg.setAttribute('focusable', 'false');

    const use = document.createElementNS(SVG_NAMESPACE, 'use');
    use.setAttribute('href', `${ICON_SPRITE}#${name}`);
    svg.append(use);
    return svg;
}
