// Função para carregamento dos artigos armazenados
function loadArticles(articles=[]) {
    const articlesList = document.getElementById('articles-list');
    
    articlesList.innerHTML = '';

    if (!articles.length) {
        const noArticle = document.createElement('p');
        noArticle.textContent = 'Nenhum artigo encontrado!'

        articlesList.innerHTML = '';
        articlesList.appendChild(noArticle);
    } else {
        articles.forEach(article => {
            const localDate = new Date(article['publish_date']).toLocaleDateString()

            const newArticle = document.createElement('li');

            const newId = document.createElement('p');
            newId.textContent = `ID: ${article['article_id']}`;
            newId.setAttribute('class', 'article-id');

            const removeButton = document.createElement('button');
            removeButton.setAttribute('class', 'remove-button');

            removeButton.addEventListener('click', () => {
                const url = `/articles/${article['article_id']}`

                fetch(url, {
                    method: 'DELETE'
                })
                .then(() => {
                    articles.forEach((deleteArticle, index) => {
                        if (deleteArticle['article_id'] == article['article_id']) {
                            articles.splice(index, 1);
                        }
                    })

                    loadArticles(articles);
                })
                .catch(error => {
                    console.log('Erro na exclusão de artigo: ', error);
                })
            })

            removeButton.addEventListener('mouseover', () => {
                const svgStyle = removeButton.querySelector('svg').style;

                svgStyle.filter = 'drop-shadow(0 0 2rem #F01010)';
                svgStyle.transform = 'scale(1.05)';
            })

            removeButton.addEventListener('mouseout', () => {
                const svgStyle = removeButton.querySelector('svg').style;

                svgStyle.filter = 'none';
                svgStyle.transform = 'scale(1)';
            })

            const removeSvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            removeSvg.setAttribute('viewBox', '0 0 640 640');
            removeButton.appendChild(removeSvg);

            const removePath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            removePath.setAttribute('fill', '#F01010');
            removePath.setAttribute('d', 'M232.7 69.9C237.1 56.8 249.3 48 263.1 48L377 48C390.8 48 403 56.8 407.4 69.9L416 96L512 96C529.7 96 544 110.3 544 128C544 145.7 529.7 160 512 160L128 160C110.3 160 96 145.7 96 128C96 110.3 110.3 96 128 96L224 96L232.7 69.9zM128 208L512 208L512 512C512 547.3 483.3 576 448 576L192 576C156.7 576 128 547.3 128 512L128 208zM216 272C202.7 272 192 282.7 192 296L192 488C192 501.3 202.7 512 216 512C229.3 512 240 501.3 240 488L240 296C240 282.7 229.3 272 216 272zM320 272C306.7 272 296 282.7 296 296L296 488C296 501.3 306.7 512 320 512C333.3 512 344 501.3 344 488L344 296C344 282.7 333.3 272 320 272zM424 272C410.7 272 400 282.7 400 296L400 488C400 501.3 410.7 512 424 512C437.3 512 448 501.3 448 488L448 296C448 282.7 437.3 272 424 272z');
            removeSvg.appendChild(removePath);

            const newTitleLink = document.createElement('a');
            const url = `/open/${article['article_id']}`;
            newTitleLink.setAttribute('href', url);

            const newTitle = document.createElement('h4');
            newTitle.textContent = article['article_title'];
            newTitleLink.appendChild(newTitle);

            const newDate = document.createElement('p');
            newDate.textContent = `Data de publicação: ${localDate}`;

            newArticle.appendChild(newId);
            newArticle.appendChild(newTitleLink);
            newArticle.appendChild(newDate);
            newArticle.appendChild(removeButton);

            articlesList.appendChild(newArticle);
        })
    }
}

function filterArticles(event, articles, filterForm) {
    event.preventDefault();

    const filterContent = filterForm.querySelector('input').value;
    const filterSelect = filterForm.querySelector('select').value;
    let url;

    if (filterSelect === 'id' && isNaN(filterContent) ) {
        loadArticles([]);
    } else if (!filterContent.trim()) {
        loadArticles(articles);
    } else {
        if (filterSelect === 'title') {
            url = `/articles/title/${filterContent}`
        } else if (filterSelect === 'id') {
            url = `/articles/id/${filterContent}`
        }

        fetch(url, {
            method: 'GET',
        })
        .then(res => res.json())
        .then(articlesRes => {
            loadArticles(articlesRes);
        })
        .catch(error => console.error('Erro na filtragem dos artigos pelo ID: ', error));
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

    const addButton = document.getElementById('add-button');
    const addMenu = document.getElementById('add-menu');
    const addForm = document.getElementById('add-form');
    const filterForm = document.getElementById('filter-form');

    const cancelButton = document.getElementById('cancel-button');
    const filterButton = document.getElementById('filter-button');

    // Função para abertura do menu de adição de artigo
    addButton.addEventListener('click', () => {
        addMenu.style.opacity = '100';
        addMenu.style.pointerEvents = 'all';
    });

    // Função para fechamento dos pop-ups
    cancelButton.addEventListener('click', () => {
        addMenu.style.opacity = '0';
        addMenu.style.pointerEvents = 'none';
    })

    document.addEventListener('keydown', (event) => {
        if (addMenu.style.display == 'flex' && 
            event.key === 'Escape') addMenu.style.display = 'none';
    })

    // Função para adição de artigo no banco de dados
    addForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        
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
            articles = await (await fetch('/articles')).json();
            loadArticles(articles);
            addMenu.style.transition = 'none';
            addMenu.style.opacity = '0';
            addMenu.style.transition = 'all 0.2s ease';
            addMenu.style.pointerEvents = 'none';
        })
        .catch(error => {
            console.error('Erro: ', error);
            alert('Erro ao enviar o formulário: ' + error.message);
        })
    })

    filterForm.querySelector('input')
    .addEventListener('input', (event) => filterArticles(event, articles, filterForm));
    filterForm.querySelector('select')
    .addEventListener('input', (event) => filterArticles(event, articles, filterForm));
})
