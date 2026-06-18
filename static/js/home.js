const articlesAPI = {
    async fetchAll() {
        const res = await fetch('/articles', { method: 'GET' });
        if (!res.ok) throw new Error(`Erro ao carregar artigos: ${res.statusText}`);
        return res.json();
    },

    async add(data) {
        const res = await fetch('/articles', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!res.ok) throw new Error(`Erro ao adicionar artigo: ${res.statusText}`);
        return res.json();
    },

    async remove(articleId) {
        const res = await fetch(`/articles/${articleId}`, { method: 'DELETE' });
        if (!res.ok) throw new Error(`Erro ao remover artigo: ${res.statusText}`);
        return res.json();
    },

    async searchByTitle(query) {
        const res = await fetch(`/articles/title/${encodeURIComponent(query)}`);
        if (!res.ok) throw new Error(`Erro na busca por título: ${res.statusText}`);
        return res.json();
    },

    async searchById(query) {
        const res = await fetch(`/articles/id/${encodeURIComponent(query)}`);
        if (!res.ok) throw new Error(`Erro na busca por ID: ${res.statusText}`);
        return res.json();
    },
};

const articlesUI = {
    listEl: null,

    init(listElement) {
        this.listEl = listElement;
    },

    render(articles) {
        this.listEl.innerHTML = '';

        if (!articles.length) {
            this.listEl.appendChild(this._buildEmptyState());
            return;
        }

        let bgIndex = 1;
        articles.forEach(article => {
            const card = this._buildCard(article, bgIndex);
            bgIndex = bgIndex === 3 ? 1 : bgIndex + 1;
            this.listEl.appendChild(card);
        });
    },

    _buildEmptyState() {
        const li = document.createElement('li');
        li.classList.add('articles__empty');
        li.innerHTML = `
            <svg class="articles__empty-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640" aria-hidden="true">
                <path d="M32 176C32 134.5 63.6 100.4 104 96.4L104 96L384 96C437 96 480 139 480 192L480 368L304 368C264.2 368 232 400.2 232 440L232 500C232 524.3 212.3 544 188 544C163.7 544 144 524.3 144 500L144 272L80 272C53.5 272 32 250.5 32 224L32 176zM268.8 544C275.9 530.9 280 515.9 280 500L280 440C280 426.7 290.7 416 304 416L552 416C565.3 416 576 426.7 576 440L576 464C576 508.2 540.2 544 496 544L268.8 544zM112 144C94.3 144 80 158.3 80 176L80 224L144 224L144 176C144 158.3 129.7 144 112 144z"/>
            </svg>
            <span>Nenhum artigo encontrado.</span>
        `;

        return li;
    },

    _buildErrorState() {
        const li = document.createElement('li');
        li.classList.add('articles__empty');
        li.innerHTML = `
            <svg class="articles__empty-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640" aria-hidden="true">
                <path d="M32 176C32 134.5 63.6 100.4 104 96.4L104 96L384 96C437 96 480 139 480 192L480 368L304 368C264.2 368 232 400.2 232 440L232 500C232 524.3 212.3 544 188 544C163.7 544 144 524.3 144 500L144 272L80 272C53.5 272 32 250.5 32 224L32 176zM268.8 544C275.9 530.9 280 515.9 280 500L280 440C280 426.7 290.7 416 304 416L552 416C565.3 416 576 426.7 576 440L576 464C576 508.2 540.2 544 496 544L268.8 544zM112 144C94.3 144 80 158.3 80 176L80 224L144 224L144 176C144 158.3 129.7 144 112 144z"/>
            </svg>
            <span>Não foi possível carregar os artigos.<br>Verifique sua conexão e recarregue a página.</span>
        `;

        return li;
    },

    _buildCard(article, bgIndex) {
        const li = document.createElement('li');
        li.classList.add('mini');
        li.style.backgroundImage = `url('./static/imgs/mini_${bgIndex}.svg')`;

        const link = document.createElement('a');
        link.href = `/open/${article.article_id}`;
        link.classList.add('mini__link', 'u-flex-center');

        const idBadge = document.createElement('p');
        idBadge.textContent = `ID: ${article.article_id}`;
        idBadge.classList.add('mini__id');

        const title = document.createElement('h3');
        title.textContent = article.article_title;
        title.classList.add('mini__title');

        const date = document.createElement('p');
        date.textContent = `Publicado em: ${new Date(article.publish_date).toLocaleDateString()}`;
        date.classList.add('mini__date');

        link.append(idBadge, title, date);

        const removeBtn = this._buildRemoveButton(article);

        li.append(link, removeBtn);
        return li;
    },

    _buildRemoveButton(article) {
        const btn = document.createElement('button');
        btn.classList.add('mini__rmv');
        btn.setAttribute('aria-label', 'Remover artigo');

        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('viewBox', '0 0 640 640');
        svg.classList.add('mini__rmv-icon');

        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', 'M232.7 69.9C237.1 56.8 249.3 48 263.1 48L377 48C390.8 48 403 56.8 407.4 69.9L416 96L512 96C529.7 96 544 110.3 544 128C544 145.7 529.7 160 512 160L128 160C110.3 160 96 145.7 96 128C96 110.3 110.3 96 128 96L224 96L232.7 69.9zM128 208L512 208L512 512C512 547.3 483.3 576 448 576L192 576C156.7 576 128 547.3 128 512L128 208zM216 272C202.7 272 192 282.7 192 296L192 488C192 501.3 202.7 512 216 512C229.3 512 240 501.3 240 488L240 296C240 282.7 229.3 272 216 272zM320 272C306.7 272 296 282.7 296 296L296 488C296 501.3 306.7 512 320 512C333.3 512 344 501.3 344 488L344 296C344 282.7 333.3 272 320 272zM424 272C410.7 272 400 282.7 400 296L400 488C400 501.3 410.7 512 424 512C437.3 512 448 501.3 448 488L448 296C448 282.7 437.3 272 424 272z');
        svg.appendChild(path);
        btn.appendChild(svg);

        btn.addEventListener('click', () => {
            articlesAPI.remove(article.article_id)
                .then(() => {
                    const idx = appState.articles.findIndex(a => a.article_id === article.article_id);
                    if (idx !== -1) appState.articles.splice(idx, 1);
                    articlesUI.render(appState.articles);
                })
                .catch(err => console.error(err));
        });

        return btn;
    },
};

const appState = {
    articles: [],
};

const addMenuModule = {
    menu: null,
    overlay: null,
    form: null,
    titleInput: null,
    contentInput: null,
    titleCounter: null,
    contentCounter: null,
    titleError: null,
    submitBtn: null,

    init() {
        this.menu           = document.getElementById('add-menu');
        this.overlay        = document.getElementById('add-menu-overlay');
        this.form           = document.getElementById('add-form');
        this.titleInput     = document.getElementById('add-input-title');
        this.contentInput   = document.getElementById('add-input-content');
        this.titleCounter   = document.getElementById('title-counter');
        this.contentCounter = document.getElementById('content-counter');
        this.titleError     = document.getElementById('title-error');
        this.submitBtn      = document.getElementById('add-submit-btn');

        const openBtn   = document.getElementById('add-btn');
        const hideBtn   = document.getElementById('add-menu-hide-btn');
        const cancelBtn = document.getElementById('add-menu-cancel-btn');

        openBtn.addEventListener('click', () => this.open());
        hideBtn.addEventListener('click', () => this.close());
        cancelBtn.addEventListener('click', () => this.close());
        this.overlay.addEventListener('click', () => this.close());

        this.titleInput.addEventListener('input', () => {
            this._updateCounter(this.titleInput, this.titleCounter, 30);
            this._clearError(this.titleError, this.titleInput.closest('.add-menu__input-wrap'));
        });

        this.contentInput.addEventListener('input', () => {
            this._updateCounter(this.contentInput, this.contentCounter, 2500);
        });

        this.form.addEventListener('submit', (e) => this._handleSubmit(e));
    },

    open() {
        this.menu.classList.add('is-open');
        this.overlay.classList.add('is-open');
        this.titleInput.focus();
    },

    close() {
        this.menu.classList.remove('is-open');
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

        const titleWrap = this.titleInput.closest('.add-menu__input-wrap');
        if (!this.titleInput.value.trim()) {
            this._showError(this.titleError, titleWrap, 'O título não pode ficar em branco.');
            this.titleInput.focus();
            return;
        }

        this.submitBtn.classList.add('is-loading');
        this.submitBtn.disabled = true;

        const data = Object.fromEntries(new FormData(this.form).entries());

        try {
            await articlesAPI.add(data);
            this.form.reset();
            this._updateCounter(this.titleInput, this.titleCounter, 30);
            this._updateCounter(this.contentInput, this.contentCounter, 2500);
            appState.articles = await articlesAPI.fetchAll();
            articlesUI.render(appState.articles);
            this.close();
        } catch (err) {
            console.error(err);
            alert('Erro ao publicar o artigo: ' + err.message);
        } finally {
            this.submitBtn.classList.remove('is-loading');
            this.submitBtn.disabled = false;
        }
    },
};

const filterMenuModule = {
    menu: null,
    overlay: null,
    input: null,
    select: null,
    statusEl: null,

    init() {
        this.menu     = document.getElementById('filter-menu');
        this.overlay  = document.getElementById('filter-menu-overlay');
        this.input    = document.getElementById('filter-input');
        this.select   = document.getElementById('filter-select');
        this.statusEl = document.getElementById('filter-status');

        const openBtn       = document.getElementById('filter-btn');
        const hideBtn       = document.getElementById('filter-menu-hide-btn');
        const clearBtn      = document.getElementById('filter-clear-btn');
        const clearInputBtn = document.getElementById('filter-clear-input-btn');

        openBtn.addEventListener('click', () => this.open());
        hideBtn.addEventListener('click', () => this.close());
        this.overlay.addEventListener('click', () => this.close());

        clearBtn.addEventListener('click', () => {
            this.input.value = '';
            this.select.value = 'title';
            this._hideStatus();
            articlesUI.render(appState.articles);
            this.input.focus();
        });

        this.input.addEventListener('input', () => {
            clearInputBtn.hidden = this.input.value === '';
            this._runFilter();
        });

        this.select.addEventListener('change', () => this._runFilter());

        clearInputBtn.addEventListener('click', () => {
            this.input.value = '';
            clearInputBtn.hidden = true;
            this._hideStatus();
            articlesUI.render(appState.articles);
            this.input.focus();
        });
    },

    open() {
        this.menu.classList.add('is-open');
        this.overlay.classList.add('is-open');
        this.input.focus();
    },

    close() {
        this.menu.classList.remove('is-open');
        this.overlay.classList.remove('is-open');
    },

    _hideStatus() {
        this.statusEl.classList.remove('is-visible', 'has-results', 'no-results');
    },

    _updateStatus(count) {
        this._hideStatus();
        if (this.input.value.trim() === '') return;

        this.statusEl.classList.add('is-visible');
        if (count > 0) {
            this.statusEl.textContent = `${count} artigo${count > 1 ? 's' : ''} encontrado${count > 1 ? 's' : ''}.`;
            this.statusEl.classList.add('has-results');
        } else {
            this.statusEl.textContent = 'Nenhum artigo encontrado.';
            this.statusEl.classList.add('no-results');
        }
    },

    async _runFilter() {
        const query = this.input.value.trim();
        const type  = this.select.value;

        if (!query) {
            articlesUI.render(appState.articles);
            this._hideStatus();
            return;
        }

        if (type === 'id' && isNaN(query)) {
            articlesUI.render([]);
            this._updateStatus(0);
            return;
        }

        try {
            const results = type === 'title'
                ? await articlesAPI.searchByTitle(query)
                : await articlesAPI.searchById(query);
            articlesUI.render(results);
            this._updateStatus(results.length);
        } catch (err) {
            console.error(err);
        }
    },
};

document.addEventListener('DOMContentLoaded', async () => {
    const listEl = document.getElementById('mini-grid');
    articlesUI.init(listEl);

    try {
        appState.articles = await articlesAPI.fetchAll();
        articlesUI.render(appState.articles);
    } catch (err) {
        console.error(err);
        listEl.innerHTML = '';
        listEl.appendChild(articlesUI._buildErrorState());
    }

    addMenuModule.init();
    filterMenuModule.init();

    document.addEventListener('keydown', (e) => {
        if (e.key !== 'Escape') return;

        if (addMenuModule.menu.classList.contains('is-open')) {
            addMenuModule.close();
        }

        if (filterMenuModule.menu.classList.contains('is-open')) {
            e.preventDefault();
            filterMenuModule.close();
        }
    });
});
