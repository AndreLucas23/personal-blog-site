import { API, ApiError } from '../api.js';
import { confirmDialog } from '../ui/dialog.js';
import { el, icon } from '../ui/dom.js';
import { bindCounter, setFieldError } from '../ui/forms.js';
import { imageErrors } from '../ui/images.js';
import { showToast, showToastAfterLeaving } from '../ui/toast.js';

const form = document.getElementById('editor');
const titleInput = document.getElementById('title');
const summaryInput = document.getElementById('summary');
const contentInput = document.getElementById('content');
const submitButton = document.getElementById('editor-submit');
const writeTab = document.getElementById('tab-write');
const previewTab = document.getElementById('tab-preview');
const writePanel = document.getElementById('panel-write');
const previewPanel = document.getElementById('panel-preview');
const draftButton = document.getElementById('editor-draft');
const unpublishButton = document.getElementById('editor-unpublish');
const statusEl = document.getElementById('editor-status');
const tagBox = document.getElementById('tag-box');
const tagList = document.getElementById('tag-list');
const tagInput = document.getElementById('tag-input');
const maxTags = Number(tagInput.dataset.max);
const minTagLength = Number(tagInput.dataset.minLength);
const maxTagLength = Number(tagInput.dataset.maxLength);
const coverInput = document.getElementById('cover-input');
const coverPreview = document.getElementById('cover-preview');
const coverPick = document.getElementById('cover-pick');
const coverRemove = document.getElementById('cover-remove');
const coverError = document.getElementById('cover-error');
const maxImageBytes = Number(coverInput.dataset.maxBytes);
const IMAGE_ERRORS = imageErrors(maxImageBytes);
let articleId = form.dataset.articleId || null;
const inputs = { title: titleInput, summary: summaryInput, content: contentInput, tags: tagInput };

const ARTICLE_ERRORS = {
    title_required: 'Dê um título ao artigo.',
    title_too_long: `O título pode ter até ${titleInput.maxLength} caracteres.`,
    summary_too_long: `O resumo pode ter até ${summaryInput.maxLength} caracteres.`,
    content_required: 'Escreva o conteúdo do artigo.',
    content_too_long: `O artigo pode ter até ${contentInput.maxLength.toLocaleString('pt-BR')} caracteres.`,
    tags_too_many: `Use até ${maxTags} tags.`,
    tag_too_short: `Cada tag precisa de pelo menos ${minTagLength} caracteres.`,
    tag_too_long: `Cada tag pode ter até ${maxTagLength} caracteres.`,
    invalid: 'Confira este campo.',
};

let dirty = false;
let saving = false;
// The cover waits for the save, like the words: a file to send, null to remove the
// cover, or undefined while it stays as it is.
let coverChange;
let coverPreviewUrl = null;
let previewedContent = null;
// Every preview request takes a number, so a slow older answer cannot replace a newer one.
let previewRun = 0;

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
        // Bubbling, so the form also learns there are unsaved changes.
        contentInput.dispatchEvent(new Event('input', { bubbles: true }));
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
    const run = ++previewRun;

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
        if (run !== previewRun) return;
        // The server renders without raw HTML and refuses unsafe links, so this markup is safe.
        previewPanel.innerHTML = html;
        previewedContent = content;
    } catch (error) {
        if (run !== previewRun) return;
        console.error(error);
        previewPanel.textContent = 'Não foi possível pré-visualizar agora. Tente de novo.';
    } finally {
        if (run === previewRun) previewPanel.removeAttribute('aria-busy');
    }
}

// Tags: the same normalization as the server, so the chips show what will be saved.
function normalizeTag(value) {
    return value.normalize('NFC').toLowerCase().trim().replace(/^#+/, '')
        .replace(/[\s_]+/g, '-')
        .replace(/[^\p{L}\p{N}\p{M}-]/gu, '')
        // Marks belong to the letter before them.
        .replace(/(^|-)\p{M}+/gu, '$1')
        .replace(/-{2,}/g, '-')
        .replace(/^-+|-+$/g, '');
}

function currentTags() {
    return [...tagList.querySelectorAll('[data-tag]')].map((chip) => chip.dataset.tag);
}

function createChip(tag) {
    return el(
        'li',
        { class: 'chip tag-input__chip', dataset: { tag } },
        tag,
        el('button', {
            class: 'tag-input__remove',
            type: 'button',
            'aria-label': `Remover a tag ${tag}`,
        }, icon('close', 'icon--sm')),
    );
}

function tagError(tag) {
    // Characters as the server counts them, not UTF-16 units.
    const length = [...tag].length;
    if (currentTags().length >= maxTags) return 'tags_too_many';
    if (length < minTagLength) return 'tag_too_short';
    if (length > maxTagLength) return 'tag_too_long';
    return null;
}

/**
 * Turn the text of the tag field into chips, with commas between tags. Unless finished,
 * the text after the last comma is still being typed and stays. A refused tag stays in
 * the field, with what follows it, and its reason. Returns false when one was refused.
 */
function addTypedTags(finished) {
    const parts = tagInput.value.split(',');
    const complete = finished ? parts.length : parts.length - 1;
    let index = 0;
    let error = null;
    for (; index < complete; index += 1) {
        const tag = normalizeTag(parts[index]);
        if (!tag || currentTags().includes(tag)) continue;
        error = tagError(tag);
        if (error) break;
        tagList.append(createChip(tag));
        dirty = true;
    }

    const left = parts.slice(index).join(',').trimStart();
    // Only when the text changed, so the caret stays where the member is fixing a tag.
    if (left !== tagInput.value) tagInput.value = left;
    setFieldError(tagInput, error ? ARTICLE_ERRORS[error] : '');
    return !error;
}

function showCover(src) {
    // The browser keeps a chosen file in memory until its address is let go.
    if (coverPreviewUrl && coverPreviewUrl !== src) {
        URL.revokeObjectURL(coverPreviewUrl);
        coverPreviewUrl = null;
    }
    coverPreview.hidden = !src;
    if (src) coverPreview.src = src;
    else coverPreview.removeAttribute('src');
    coverRemove.hidden = !src;
    coverPick.querySelector('span').textContent = src ? 'Trocar capa' : 'Adicionar capa';
}

function chooseCover(file) {
    coverError.textContent = '';
    // The server checks again; checking here tells at once, before anything is saved.
    if (!coverInput.accept.split(',').includes(file.type)) {
        coverError.textContent = IMAGE_ERRORS.image_format;
        return;
    }
    if (file.size > maxImageBytes) {
        coverError.textContent = IMAGE_ERRORS.image_too_large;
        return;
    }
    const url = URL.createObjectURL(file);
    showCover(url);
    coverPreviewUrl = url;
    coverChange = file;
    dirty = true;
}

/** Tell why the cover was not saved, when the article itself was. */
function coverNotSaved(error, article) {
    const code = error instanceof ApiError ? error.errors?.cover : null;
    if (!code) console.error(error);
    const reason = IMAGE_ERRORS[code] || 'Não foi possível enviar a capa.';

    // This editor still has the actions of a draft, so it opens again as a published one.
    if (article.status === 'published' && !unpublishButton) {
        dirty = false;
        showToastAfterLeaving(`O artigo foi publicado, mas a capa não. ${reason}`, { type: 'error' });
        window.location.assign(`/write/${article.article_id}`);
        return;
    }
    coverError.textContent = reason;
    showToast('O artigo foi salvo, mas a capa não. Confira a capa e salve de novo.', { type: 'error' });
}

function readFields() {
    return {
        title: titleInput.value.trim(),
        summary: summaryInput.value.trim(),
        content: contentInput.value,
        tags: currentTags(),
    };
}

function checkFields(fields, publishing) {
    const errors = {};
    if (!fields.title) errors.title = 'title_required';
    // A draft can wait for its text; publishing cannot.
    if (publishing && !fields.content.trim()) errors.content = 'content_required';
    return errors;
}

function savedAt() {
    return new Intl.DateTimeFormat('pt-BR', { hour: '2-digit', minute: '2-digit' }).format(new Date());
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

const actionButtons = [submitButton, draftButton, unpublishButton].filter(Boolean);

function setBusy(button, busy) {
    button.classList.toggle('is-loading', busy);
    actionButtons.forEach((other) => { other.disabled = busy; });
}

/**
 * Save with a status: 'published' opens the article afterwards, 'draft' stays here.
 * Returns the saved article, or null when nothing was saved.
 */
async function save(status, button) {
    // Ctrl+Enter does not go through the disabled buttons, so a second save waits here.
    if (saving) return null;

    Object.values(inputs).forEach((input) => setFieldError(input, ''));
    // A tag left in the field counts, and one that is refused stops the save with its reason.
    if (tagInput.value.trim() && !addTypedTags(true)) {
        tagInput.focus();
        return null;
    }
    const fields = readFields();
    const localErrors = checkFields(fields, status === 'published');
    if (Object.keys(localErrors).length) {
        showErrors(localErrors);
        return null;
    }

    saving = true;
    setBusy(button, true);

    try {
        const payload = { ...fields, status };
        let article = articleId
            ? await API.updateArticle(articleId, payload)
            : await API.createArticle(payload);
        // A new article gets its own address, so a reload or another try saves the same one.
        if (!articleId) {
            articleId = String(article.article_id);
            form.dataset.articleId = articleId;
            window.history.replaceState(null, '', `/write/${articleId}`);
        }

        if (coverChange !== undefined) {
            try {
                article = coverChange
                    ? await API.uploadCover(articleId, coverChange)
                    : await API.removeCover(articleId);
                coverChange = undefined;
            } catch (error) {
                saving = false;
                setBusy(button, false);
                coverNotSaved(error, article);
                return null;
            }
        }
        dirty = false;

        if (article.status === 'published') {
            window.location.assign(article.url);
            return article;
        }

        // The saved cover takes the place of the preview of the chosen file.
        showCover(article.cover_url);
        statusEl.textContent = `Rascunho salvo às ${savedAt()}`;
        saving = false;
        setBusy(button, false);
        return article;
    } catch (error) {
        saving = false;
        setBusy(button, false);
        if (error instanceof ApiError && error.errors && Object.keys(error.errors).length) {
            showErrors(error.errors);
            return null;
        }
        console.error(error);
        showToast('Não foi possível salvar o artigo. Tente de novo.', { type: 'error' });
        return null;
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

tagInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' || event.key === ',') {
        event.preventDefault();
        addTypedTags(true);
    } else if (event.key === 'Backspace' && !tagInput.value) {
        tagList.lastElementChild?.remove();
        dirty = true;
    }
});

// Commas also arrive in pasted text and from keyboards that do not report the key.
tagInput.addEventListener('input', (event) => {
    const arrived = event.inputType?.startsWith('insertFrom') || event.data?.includes(',');
    if (arrived && tagInput.value.includes(',')) addTypedTags(false);
});

// A tag typed and left behind still counts.
tagInput.addEventListener('blur', () => {
    if (tagInput.value.trim()) addTypedTags(true);
});

tagList.addEventListener('click', (event) => {
    const remove = event.target.closest('.tag-input__remove');
    if (!remove) return;
    remove.closest('[data-tag]').remove();
    dirty = true;
    tagInput.focus();
});

tagBox.addEventListener('click', (event) => {
    if (event.target === tagBox) tagInput.focus();
});

form.addEventListener('submit', (event) => {
    event.preventDefault();
    save('published', submitButton);
});

form.addEventListener('keydown', (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        event.preventDefault();
        save('published', submitButton);
    }
});

draftButton?.addEventListener('click', async () => {
    if (await save('draft', draftButton)) showToast('Rascunho salvo.', { type: 'success' });
});

unpublishButton?.addEventListener('click', async () => {
    const confirmed = await confirmDialog({
        title: 'Mover para rascunhos?',
        message: 'O artigo deixa de aparecer para os outros até você publicar de novo.',
        confirmLabel: 'Mover',
    });
    if (!confirmed) return;

    if (await save('draft', unpublishButton)) {
        showToastAfterLeaving('O artigo voltou para os rascunhos.', { type: 'success' });
        // The editor reopens with the actions of a draft.
        window.location.assign(`/write/${articleId}`);
    }
});

coverPick.addEventListener('click', () => coverInput.click());

coverInput.addEventListener('change', () => {
    const [file] = coverInput.files;
    // Cleared, so choosing the same file again still counts as a choice.
    coverInput.value = '';
    if (file) chooseCover(file);
});

coverRemove.addEventListener('click', () => {
    coverError.textContent = '';
    coverChange = null;
    showCover(null);
    dirty = true;
    // The remove button hides with the cover.
    coverPick.focus();
});

window.addEventListener('beforeunload', (event) => {
    if (dirty) event.preventDefault();
});
