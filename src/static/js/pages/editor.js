import { API, ApiError } from '../api.js';
import { bindCounter, setFieldError } from '../ui/forms.js';
import { showToast } from '../ui/toast.js';

const form = document.getElementById('editor');
const titleInput = document.getElementById('title');
const summaryInput = document.getElementById('summary');
const contentInput = document.getElementById('content');
const submitButton = document.getElementById('editor-submit');
const writeTab = document.getElementById('tab-write');
const previewTab = document.getElementById('tab-preview');
const writePanel = document.getElementById('panel-write');
const previewPanel = document.getElementById('panel-preview');
const articleId = form.dataset.articleId || null;
const inputs = { title: titleInput, summary: summaryInput, content: contentInput };

const ARTICLE_ERRORS = {
    title_required: 'Dê um título ao artigo.',
    title_too_long: `O título pode ter até ${titleInput.maxLength} caracteres.`,
    summary_too_long: `O resumo pode ter até ${summaryInput.maxLength} caracteres.`,
    content_required: 'Escreva o conteúdo do artigo.',
    content_too_long: `O artigo pode ter até ${contentInput.maxLength.toLocaleString('pt-BR')} caracteres.`,
    invalid: 'Confira este campo.',
};

let dirty = false;
let previewedContent = null;

// Title and summary are single lines that grow as they wrap.
function autosize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = `${textarea.scrollHeight}px`;
}

// Replacing through execCommand keeps the browser's undo history; setRangeText is the fallback.
function replaceSelection(text, selectStart, selectEnd) {
    const start = contentInput.selectionStart;
    contentInput.focus();
    if (!document.execCommand('insertText', false, text)) {
        contentInput.setRangeText(text, start, contentInput.selectionEnd, 'end');
        contentInput.dispatchEvent(new Event('input'));
    }
    contentInput.setSelectionRange(start + selectStart, start + selectEnd);
}

function wrapSelection(before, after, placeholder) {
    const { selectionStart, selectionEnd, value } = contentInput;
    const selected = value.slice(selectionStart, selectionEnd) || placeholder;
    replaceSelection(`${before}${selected}${after}`, before.length, before.length + selected.length);
}

function prefixLines(prefixFor) {
    const { value } = contentInput;
    const start = value.lastIndexOf('\n', contentInput.selectionStart - 1) + 1;
    const endBreak = value.indexOf('\n', contentInput.selectionEnd);
    const end = endBreak === -1 ? value.length : endBreak;
    const lines = value.slice(start, end).split('\n').map((line, index) => prefixFor(index) + line);
    const text = lines.join('\n');

    contentInput.setSelectionRange(start, end);
    replaceSelection(text, text.length, text.length);
}

const FORMATS = {
    bold: () => wrapSelection('**', '**', 'texto em negrito'),
    italic: () => wrapSelection('_', '_', 'texto em itálico'),
    heading: () => prefixLines(() => '## '),
    quote: () => prefixLines(() => '> '),
    list: () => prefixLines(() => '- '),
    ordered: () => prefixLines((index) => `${index + 1}. `),
    code: () => {
        const { selectionStart, selectionEnd, value } = contentInput;
        if (value.slice(selectionStart, selectionEnd).includes('\n')) {
            wrapSelection('```\n', '\n```', '');
        } else {
            wrapSelection('`', '`', 'código');
        }
    },
    link: () => {
        const { selectionStart, selectionEnd, value } = contentInput;
        const text = value.slice(selectionStart, selectionEnd) || 'texto do link';
        const markdown = `[${text}](https://)`;
        // Leaves the address selected, ready to be typed over.
        replaceSelection(markdown, text.length + 3, markdown.length - 1);
    },
};

function showTab(tab) {
    const previewing = tab === previewTab;
    writeTab.setAttribute('aria-selected', String(!previewing));
    previewTab.setAttribute('aria-selected', String(previewing));
    writeTab.tabIndex = previewing ? -1 : 0;
    previewTab.tabIndex = previewing ? 0 : -1;
    writePanel.hidden = previewing;
    previewPanel.hidden = !previewing;
    if (previewing) showPreview();
}

async function showPreview() {
    const content = contentInput.value;
    if (content === previewedContent) return;

    if (!content.trim()) {
        previewPanel.replaceChildren(Object.assign(document.createElement('p'), {
            className: 'editor__empty',
            textContent: 'Nada para pré-visualizar ainda.',
        }));
        previewedContent = content;
        return;
    }

    previewPanel.setAttribute('aria-busy', 'true');
    try {
        const { html } = await API.preview(content);
        // The server renders without raw HTML and refuses unsafe links, so this markup is safe.
        previewPanel.innerHTML = html;
        previewedContent = content;
    } catch (error) {
        console.error(error);
        previewPanel.textContent = 'Não foi possível pré-visualizar agora. Tente de novo.';
    } finally {
        previewPanel.removeAttribute('aria-busy');
    }
}

function readFields() {
    return {
        title: titleInput.value.trim(),
        summary: summaryInput.value.trim(),
        content: contentInput.value,
    };
}

function checkFields(fields) {
    const errors = {};
    if (!fields.title) errors.title = 'title_required';
    if (!fields.content.trim()) errors.content = 'content_required';
    return errors;
}

function showErrors(errors) {
    const entries = Object.entries(errors);
    entries.forEach(([field, code]) => {
        if (inputs[field]) setFieldError(inputs[field], ARTICLE_ERRORS[code] || ARTICLE_ERRORS.invalid);
    });
    // The content field may be behind the preview tab.
    if (errors.content) showTab(writeTab);
    inputs[entries[0][0]]?.focus();
}

async function save() {
    Object.values(inputs).forEach((input) => setFieldError(input, ''));
    const fields = readFields();
    const localErrors = checkFields(fields);
    if (Object.keys(localErrors).length) {
        showErrors(localErrors);
        return;
    }

    submitButton.classList.add('is-loading');
    submitButton.disabled = true;

    try {
        const article = articleId
            ? await API.updateArticle(articleId, fields)
            : await API.createArticle(fields);
        dirty = false;
        window.location.assign(article.url);
    } catch (error) {
        submitButton.classList.remove('is-loading');
        submitButton.disabled = false;
        if (error instanceof ApiError && error.errors && Object.keys(error.errors).length) {
            showErrors(error.errors);
            return;
        }
        console.error(error);
        showToast('Não foi possível salvar o artigo. Tente de novo.', { type: 'error' });
    }
}

[titleInput, summaryInput].forEach((textarea) => {
    autosize(textarea);
    textarea.addEventListener('input', () => autosize(textarea));
});

bindCounter(summaryInput, document.getElementById('summary-counter'));
bindCounter(contentInput, document.getElementById('content-counter'));

// The title is one line: Enter moves on to the summary instead of breaking it.
titleInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
        event.preventDefault();
        summaryInput.focus();
    }
});

form.addEventListener('input', () => { dirty = true; });

form.querySelectorAll('[data-format]').forEach((button) => {
    button.addEventListener('click', () => FORMATS[button.dataset.format]());
});

contentInput.addEventListener('keydown', (event) => {
    if (!(event.ctrlKey || event.metaKey)) return;
    const shortcut = { b: 'bold', i: 'italic', k: 'link' }[event.key.toLowerCase()];
    if (shortcut) {
        event.preventDefault();
        FORMATS[shortcut]();
    }
});

[writeTab, previewTab].forEach((tab) => {
    tab.addEventListener('click', () => showTab(tab));
    tab.addEventListener('keydown', (event) => {
        if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return;
        const other = tab === writeTab ? previewTab : writeTab;
        showTab(other);
        other.focus();
    });
});

form.addEventListener('submit', (event) => {
    event.preventDefault();
    save();
});

form.addEventListener('keydown', (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        event.preventDefault();
        save();
    }
});

window.addEventListener('beforeunload', (event) => {
    if (dirty) event.preventDefault();
});
