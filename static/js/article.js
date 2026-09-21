const articleAPI = {
    async update(articleId, data) {
        const res = await fetch(`/api/articles/${articleId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!res.ok) throw new Error(`Erro ao salvar: ${res.statusText}`);
        return res.json();
    },
};

const editPanelModule = {
    panel: null,
    overlay: null,
    form: null,
    titleInput: null,
    contentInput: null,
    titleCounter: null,
    contentCounter: null,
    titleError: null,
    submitBtn: null,
    articleId: null,

    init() {
        this.panel          = document.getElementById('edit-panel');
        this.overlay        = document.getElementById('edit-overlay');
        this.form           = document.getElementById('edit-form');
        this.titleInput     = document.getElementById('edit-input-title');
        this.contentInput   = document.getElementById('edit-input-content');
        this.titleCounter   = document.getElementById('edit-title-counter');
        this.contentCounter = document.getElementById('edit-content-counter');
        this.titleError     = document.getElementById('edit-title-error');
        this.submitBtn      = document.getElementById('edit-submit-btn');
        this.articleId      = document.querySelector('.art__main').dataset.articleId;

        const openBtn   = document.getElementById('edit-btn');
        const hideBtn   = document.getElementById('edit-panel-hide-btn');
        const cancelBtn = document.getElementById('edit-cancel-btn');

        openBtn.addEventListener('click', () => this.open());
        hideBtn.addEventListener('click', () => this.close());
        cancelBtn.addEventListener('click', () => this.close());
        this.overlay.addEventListener('click', () => this.close());

        this.titleInput.addEventListener('input', () => {
            this._updateCounter(this.titleInput, this.titleCounter, 30);
            this._clearError(this.titleError, this.titleInput.closest('.edit-panel__input-wrap'));
        });

        this.contentInput.addEventListener('input', () => {
            this._updateCounter(this.contentInput, this.contentCounter, 2500);
        });

        this.form.addEventListener('submit', (e) => this._handleSubmit(e));
    },

    open() {
        const currentTitle   = document.getElementById('view-title').textContent;
        const currentContent = document.getElementById('view-content').textContent;

        this.titleInput.value   = currentTitle;
        this.contentInput.value = currentContent;

        this._updateCounter(this.titleInput, this.titleCounter, 30);
        this._updateCounter(this.contentInput, this.contentCounter, 2500);

        this.panel.classList.add('is-open');
        this.overlay.classList.add('is-open');
        this.titleInput.focus();
    },

    close() {
        this.panel.classList.remove('is-open');
        this.overlay.classList.remove('is-open');
    },

    _updateCounter(input, counter, max) {
        const len = input.value.length;
        counter.textContent = `${len} / ${max}`;
        counter.classList.remove('is-near-limit', 'is-at-limit');
        if (len >= max)            counter.classList.add('is-at-limit');
        else if (len >= max * 0.8) counter.classList.add('is-near-limit');
    },

    _showError(el, wrap, msg) {
        el.textContent = msg;
        el.classList.add('is-visible');
        wrap.classList.add('has-error');
    },

    _clearError(el, wrap) {
        el.classList.remove('is-visible');
        wrap.classList.remove('has-error');
    },

    async _handleSubmit(e) {
        e.preventDefault();

        const titleWrap = this.titleInput.closest('.edit-panel__input-wrap');
        if (!this.titleInput.value.trim()) {
            this._showError(this.titleError, titleWrap, 'O título não pode ficar em branco.');
            this.titleInput.focus();
            return;
        }

        this.submitBtn.classList.add('is-loading');
        this.submitBtn.disabled = true;

        const payload = {
            title:   this.titleInput.value.trim(),
            content: this.contentInput.value,
        };

        try {
            await articleAPI.update(this.articleId, payload);
            document.getElementById('view-title').textContent   = payload.title;
            document.getElementById('view-content').textContent = payload.content;
            document.title = `${payload.title} — Blog Pessoal`;
            this.close();
        } catch (err) {
            console.error(err);
            alert('Erro ao salvar o artigo: ' + err.message);
        } finally {
            this.submitBtn.classList.remove('is-loading');
            this.submitBtn.disabled = false;
        }
    },
};

document.addEventListener('DOMContentLoaded', () => {
    editPanelModule.init();

    document.addEventListener('keydown', (e) => {
        if (e.key !== 'Escape') return;
        if (editPanelModule.panel.classList.contains('is-open')) {
            editPanelModule.close();
        }
    });
});

