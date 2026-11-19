"""Turning the Markdown members write into HTML that is safe to show."""
from markdown_it import MarkdownIt
from markupsafe import Markup

# Links in members' text lead to sites nobody here vouches for.
LINK_REL = 'nofollow ugc noopener noreferrer'
WORDS_PER_MINUTE = 200
EXCERPT_LENGTH = 220


def _demote_headings(state) -> None:
    """The page title is the only h1, so the headings of the text start at h2."""
    for token in state.tokens:
        if token.type in ('heading_open', 'heading_close'):
            token.tag = f'h{min(int(token.tag[1]) + 1, 6)}'


def _link_open(self, tokens, index, options, env) -> str:
    tokens[index].attrSet('rel', LINK_REL)
    return self.renderToken(tokens, index, options, env)


def _create_markdown() -> MarkdownIt:
    # Without raw HTML, and with the link targets markdown-it already refuses, such as
    # javascript: and data:, the output is safe to put in a page.
    markdown = MarkdownIt('commonmark', {'html': False})
    markdown.enable(['table', 'strikethrough'])
    # Remote images would tell other sites who reads what, and the page policy blocks them.
    markdown.disable('image')
    markdown.core.ruler.push('demote_headings', _demote_headings)
    markdown.add_render_rule('link_open', _link_open)
    return markdown


_markdown = _create_markdown()


def render(text: str) -> Markup:
    return Markup(_markdown.render(text or ''))


def plain_text(text: str) -> str:
    """The words of a Markdown text without its formatting, on one line."""
    blocks = []
    for token in _markdown.parse(text or ''):
        if token.type == 'inline' and token.children:
            # Pieces of one paragraph touch each other, as in "código." after a code span.
            blocks.append(''.join(
                child.content if child.type in ('text', 'code_inline') else ' '
                for child in token.children
                if child.type in ('text', 'code_inline', 'softbreak', 'hardbreak')
            ))
        elif token.type in ('code_block', 'fence'):
            blocks.append(token.content)
    return ' '.join(' '.join(blocks).split())


def excerpt(text: str, length: int = EXCERPT_LENGTH) -> str:
    """The start of the text, cut at a word, for cards and page descriptions."""
    plain = plain_text(text)
    if len(plain) <= length:
        return plain
    return plain[:length].rsplit(' ', 1)[0] + '…'


def reading_minutes(text: str) -> int:
    return max(1, round(len(plain_text(text).split()) / WORDS_PER_MINUTE))
