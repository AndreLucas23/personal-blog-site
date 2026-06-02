// Função para carregamento dos artigos armazenados
function loadArticles(articles=[]) {
    const articlesList = document.getElementById('mini-grid');
    
    articlesList.innerHTML = '';

    if (!articles.length) {
        const emptyState = document.createElement('li');
        emptyState.classList.add('articles__empty');
        emptyState.innerHTML = `
            <svg class="articles__empty-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640" aria-hidden="true">
                <path d="M32 176C32 134.5 63.6 100.4 104 96.4L104 96L384 96C437 96 480 139 480 192L480 368L304 368C264.2 368 232 400.2 232 440L232 500C232 524.3 212.3 544 188 544C163.7 544 144 524.3 144 500L144 272L80 272C53.5 272 32 250.5 32 224L32 176zM268.8 544C275.9 530.9 280 515.9 280 500L280 440C280 426.7 290.7 416 304 416L552 416C565.3 416 576 426.7 576 440L576 464C576 508.2 540.2 544 496 544L268.8 544zM112 144C94.3 144 80 158.3 80 176L80 224L144 224L144 176C144 158.3 129.7 144 112 144z"/>
            </svg>
            <span>Nenhum artigo encontrado.</span>
        `;
        articlesList.appendChild(emptyState);
    } else {
        let bgDef = 1;

        articles.forEach(article => {
            const newArticle = document.createElement('li');
            newArticle.classList.add('mini');
            
            newArticle.style.backgroundImage = `url('./static/imgs/mini_${bgDef}.svg')`
            bgDef === 3 ? bgDef = 1 : bgDef += 1;

            const newLink = document.createElement('a');
            const url = `/open/${article['article_id']}`;
            newLink.setAttribute('href', url);
            newLink.classList.add('mini__link', 'u-flex-center');

            const newId = document.createElement('p');
            newId.textContent = `ID: ${article['article_id']}`;
            newId.classList.add('mini__id');

            const newRemove = document.createElement('button');
            newRemove.classList.add('mini__rmv');
            newRemove.setAttribute('aria-label', 'Remover artigo');

            newRemove.addEventListener('click', (event) => {
                const url = `/articles/${article['article_id']}`

                fetch(url, {
                    method: 'DELETE'
                })
                .then(() => {
                    articles.forEach((deleteArticle, index) => {
                        if (deleteArticle['article_id'] === article['article_id']) {
                            articles.splice(index, 1);
                        }
                    })

                    loadArticles(articles);
                })
                .catch(error => {
                    console.log('Erro na exclusão de artigo: ', error);
                })
            })

            const removeSvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            removeSvg.setAttribute('viewBox', '0 0 640 640');
            removeSvg.classList.add('mini__rmv-icon');
            newRemove.appendChild(removeSvg);

            const removePath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            removePath.setAttribute('d', 'M232.7 69.9C237.1 56.8 249.3 48 263.1 48L377 48C390.8 48 403 56.8 407.4 69.9L416 96L512 96C529.7 96 544 110.3 544 128C544 145.7 529.7 160 512 160L128 160C110.3 160 96 145.7 96 128C96 110.3 110.3 96 128 96L224 96L232.7 69.9zM128 208L512 208L512 512C512 547.3 483.3 576 448 576L192 576C156.7 576 128 547.3 128 512L128 208zM216 272C202.7 272 192 282.7 192 296L192 488C192 501.3 202.7 512 216 512C229.3 512 240 501.3 240 488L240 296C240 282.7 229.3 272 216 272zM320 272C306.7 272 296 282.7 296 296L296 488C296 501.3 306.7 512 320 512C333.3 512 344 501.3 344 488L344 296C344 282.7 333.3 272 320 272zM424 272C410.7 272 400 282.7 400 296L400 488C400 501.3 410.7 512 424 512C437.3 512 448 501.3 448 488L448 296C448 282.7 437.3 272 424 272z');
            removeSvg.appendChild(removePath);

            const newTitle = document.createElement('h3');
            newTitle.textContent = article['article_title'];
            newTitle.classList.add('mini__title');

            const localDate = new Date(article['publish_date']).toLocaleDateString()
            const newDate = document.createElement('p');
            newDate.textContent = `Publicado em: ${localDate}`;
            newDate.classList.add('mini__date');

            newArticle.appendChild(newLink);
            newArticle.appendChild(newRemove);
            newLink.appendChild(newId);
            newLink.appendChild(newTitle);
            newLink.appendChild(newDate);

            articlesList.appendChild(newArticle);
        })
    }
}


// Procedimento a partir do carregamento do DOM
document.addEventListener('DOMContentLoaded', async () => {
    let articles = await fetch('/articles', {
        method: 'GET',
    })
    .catch(error => {
        console.error('Erro no carregamento dos artigos: ', error)
    })

    articles = await articles.json();
    loadArticles(articles);

    const addButton = document.getElementById('add-btn');
    const addMenu = document.getElementById('add-menu');
    const addOverlay = document.getElementById('add-menu-overlay');
    const addForm = document.getElementById('add-form');

    const hideButton = document.getElementById('add-menu-hide-btn');
    const cancelButton = document.getElementById('add-menu-cancel-btn');
    const submitBtn = document.getElementById('add-submit-btn');

    // Elementos do filter-menu
    const filterButton = document.getElementById('filter-btn');
    const filterMenu = document.getElementById('filter-menu');
    const filterOverlay = document.getElementById('filter-menu-overlay');
    const filterForm = document.getElementById('filter-form');
    const filterInput = document.getElementById('filter-input');
    const filterSelect = document.getElementById('filter-select');
    const filterStatus = document.getElementById('filter-status');
    const filterHideBtn = document.getElementById('filter-menu-hide-btn');
    const filterClearBtn = document.getElementById('filter-clear-btn');
    const filterClearInputBtn = document.getElementById('filter-clear-input-btn');

    // Contadores de caracteres
    const titleInput = document.getElementById('add-input-title');
    const contentInput = document.getElementById('add-input-content');
    const titleCounter = document.getElementById('title-counter');
    const contentCounter = document.getElementById('content-counter');
    const titleError = document.getElementById('title-error');

    function showError(el, wrap, msg) {
        el.textContent = msg;
        el.classList.add('is-visible');
        wrap.classList.add('has-error');
    }

    function clearError(el, wrap) {
        el.classList.remove('is-visible');
        wrap.classList.remove('has-error');
    }

    function updateCounter(input, counter, max) {
        const len = input.value.length;
        counter.textContent = `${len} / ${max}`;
        counter.classList.remove('is-near-limit', 'is-at-limit');
        if (len >= max) {
            counter.classList.add('is-at-limit');
        } else if (len >= max * 0.8) {
            counter.classList.add('is-near-limit');
        }
    }

    titleInput.addEventListener('input', () => {
        updateCounter(titleInput, titleCounter, 30);
        clearError(titleError, titleInput.closest('.add-menu__input-wrap'));
    });
    contentInput.addEventListener('input', () => updateCounter(contentInput, contentCounter, 2500));

    // Helpers de abertura / fechamento
    function openMenu() {
        addMenu.classList.add('is-open');
        addOverlay.classList.add('is-open');
        titleInput.focus();
    }

    function closeMenu() {
        addMenu.classList.remove('is-open');
        addOverlay.classList.remove('is-open');
    }

    // Função para abertura do menu de adição de artigo
    addButton.addEventListener('click', openMenu);

    // Função para fechamento do menu
    hideButton.addEventListener('click', closeMenu);
    cancelButton.addEventListener('click', closeMenu);
    addOverlay.addEventListener('click', closeMenu);

    document.addEventListener('keydown', (event) => {
        if (addMenu.classList.contains('is-open') && event.key === 'Escape') {
            closeMenu();
        }
    });

    // Função para adição de artigo no banco de dados
    addForm.addEventListener('submit', async (event) => {
        event.preventDefault();

        const titleWrap = titleInput.closest('.add-menu__input-wrap');
        if (!titleInput.value.trim()) {
            showError(titleError, titleWrap, 'O título não pode ficar em branco.');
            titleInput.focus();
            return;
        }

        submitBtn.classList.add('is-loading');
        submitBtn.disabled = true;

        const addData = new FormData(addForm);
        const data = {};
        addData.forEach((value, key) => {
            data[key] = value;
        })

        await fetch('/articles', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(res => {
            if (!res.ok) throw new Error('Erro na adição de artigo: ' + res.statusText);

            return res.json();
        })
        .then(async data => {
            console.log('Sucesso: ', data);
            addForm.reset();
            updateCounter(titleInput, titleCounter, 30);
            updateCounter(contentInput, contentCounter, 2500);
            articles = await (await fetch('/articles')).json();
            loadArticles(articles);
            closeMenu();
        })
        .catch(error => {
            console.error('Erro: ', error);
            alert('Erro ao enviar o formulário: ' + error.message);
        })
        .finally(() => {
            submitBtn.classList.remove('is-loading');
            submitBtn.disabled = false;
        });
    })

    // Helpers de abertura / fechamento do filter-menu
    function openFilterMenu() {
        filterMenu.classList.add('is-open');
        filterOverlay.classList.add('is-open');
        filterInput.focus();
    }

    function closeFilterMenu() {
        filterMenu.classList.remove('is-open');
        filterOverlay.classList.remove('is-open');
    }

    // Função de filtragem ao vivo
    function updateFilterStatus(count) {
        filterStatus.classList.remove('is-visible', 'has-results', 'no-results');
        if (filterInput.value.trim() === '') return;

        filterStatus.classList.add('is-visible');
        if (count > 0) {
            filterStatus.textContent = `${count} artigo${count > 1 ? 's' : ''} encontrado${count > 1 ? 's' : ''}.`;
            filterStatus.classList.add('has-results');
        } else {
            filterStatus.textContent = 'Nenhum artigo encontrado.';
            filterStatus.classList.add('no-results');
        }
    }

    async function runFilter() {
        const query = filterInput.value.trim();
        const type = filterSelect.value;

        if (!query) {
            loadArticles(articles);
            filterStatus.classList.remove('is-visible', 'has-results', 'no-results');
            return;
        }

        if (type === 'id' && isNaN(query)) {
            loadArticles([]);
            updateFilterStatus(0);
            return;
        }

        const url = type === 'title'
            ? `/articles/title/${encodeURIComponent(query)}`
            : `/articles/id/${encodeURIComponent(query)}`;

        try {
            const res = await fetch(url, { method: 'GET' });
            const filtered = await res.json();
            loadArticles(filtered);
            updateFilterStatus(filtered.length);
        } catch (error) {
            console.error('Erro na filtragem: ', error);
        }
    }

    // Event listeners do filter-menu
    filterButton.addEventListener('click', openFilterMenu);
    filterHideBtn.addEventListener('click', closeFilterMenu);
    filterOverlay.addEventListener('click', closeFilterMenu);

    filterClearBtn.addEventListener('click', () => {
        filterInput.value = '';
        filterSelect.value = 'title';
        filterStatus.classList.remove('is-visible', 'has-results', 'no-results');
        loadArticles(articles);
        filterInput.focus();
    });

    filterInput.addEventListener('input', () => {
        filterClearInputBtn.hidden = filterInput.value === '';
        runFilter();
    });
    filterSelect.addEventListener('change', runFilter);

    filterClearInputBtn.addEventListener('click', () => {
        filterInput.value = '';
        filterClearInputBtn.hidden = true;
        filterStatus.classList.remove('is-visible', 'has-results', 'no-results');
        loadArticles(articles);
        filterInput.focus();
    });

    document.addEventListener('keydown', (event) => {
        if (filterMenu.classList.contains('is-open') && event.key === 'Escape') {
            event.preventDefault();
            closeFilterMenu();
        }
    });
})
