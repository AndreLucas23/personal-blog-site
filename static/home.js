// Função para carregamento dos artigos armazenados
async function loadArticles(articles=[]) {
    const articlesList = document.getElementById('articles-list');
    
    articlesList.innerHTML = '';

    if (!articles.length) {
        const noArticle = document.createElement('p');
        noArticle.textContent = 'Nenhum artigo encontrado!'
        noArticle.style.margin = '0 auto';

        articlesList.innerHTML = '';
        articlesList.appendChild(noArticle);
    } else {
        articles.forEach(article => {
            localDate = new Date(article['publish-date']).toLocaleDateString()

            const newArticle = document.createElement('li');

            const newId = document.createElement('p');
            newId.textContent = `ID: ${article['article-id']}`;
            newId.setAttribute('class', 'article-id');
            newArticle.appendChild(newId);

            const newTitleLink = document.createElement('a');
            const url = `/open/${article['article-id']}`;
            newTitleLink.setAttribute('href', url);

            const newTitle = document.createElement('h4');
            newTitle.textContent = article['article-title'];
            newTitleLink.appendChild(newTitle);

            const newDate = document.createElement('p');
            newDate.textContent = `Data de publicação: ${localDate}`;

            newArticle.appendChild(newId);
            newArticle.appendChild(newTitleLink);
            newArticle.appendChild(newDate);

            articlesList.appendChild(newArticle);
        })
    }
}

function searchArticles(event, articles, searchForm) {
    event.preventDefault();

    const searchContent = searchForm.querySelector('input').value;
    const searchSelect = searchForm.querySelector('select').value;
    let url;

    if (!searchContent.length) {
        loadArticles(articles);
    } else {
        if (searchSelect === 'title') {
            url = `/articles/title/${searchContent}`
        } else if (searchSelect === 'id') {
            url = `/articles/id/${searchContent}`
        }

    fetch(url, {
            method: 'GET',
    })
    .then(res => res.json())
    .then(articlesRes => {
        loadArticles(articlesRes);
    })
    .catch(error => console.error('Erro na filtragem dos artigos pelo ID: ' + error));
    }
}

// Procedimento a partir do carregamento do DOM
document.addEventListener('DOMContentLoaded', async () => {
    let articles = await fetch('/articles', {
        method: 'GET',
    })
    .catch(error => {
        console.error('Erro no carregamento dos artigos: ' + error)
    })

    articles = await articles.json();
    loadArticles(articles);

    const addButton = document.getElementById('add-button');
    const removeButton = document.getElementById('remove-button');
    const addOverlay = document.getElementById('add-popup-overlay');
    const removeOverlay = document.getElementById('remove-popup-overlay');
    const addForm = document.getElementById('add-form');
    const removeForm = document.getElementById('remove-form');
    const searchForm = document.getElementById('search-form');

    const cancelButtons = document.getElementsByClassName('cancel-button');
    const searchButton = document.getElementById('search-button');
    const popups = document.getElementsByClassName('popup');

    // Função para abertura do pop-up de adição de artigo
    addButton.addEventListener('click', () => {
        addOverlay.style.display = 'flex'
    });

    // Função para abertura do pop-up de remoção de artigo
    removeButton.addEventListener('click', () => {
        removeOverlay.style.display = 'flex';
    })

    // Função para fechamento dos pop-ups
    Array.from(cancelButtons).forEach(button => {
        button.addEventListener('click', () => {
            button.parentElement.parentElement.style.display = 'none';
        })
    })

    Array.from(popups).forEach(popup => {
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') popup.parentElement.style.display = 'none';
        })
    })
    
    searchButton.addEventListener('click', () => {
        if (searchButton.parentElement.style.marginLeft === '0rem') {
            searchButton.parentElement.style.marginLeft = '31rem';
        } else {
            searchButton.parentElement.style.marginLeft = '0rem';
        }
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
        })
        .catch(error => {
            console.error('Erro: ', error);
            alert('Erro ao enviar o formulário: ' + error.message);
        })

        addOverlay.style.display = 'none';
    })

    // Função para remoção de artigo do banco de dados
    removeForm.addEventListener('submit', async (event) => {
        event.preventDefault();

        const articleId = document.getElementById('remove-input').value;
        const url = `/articles/${articleId}`;

        await fetch(url, {
            method: 'DELETE',
        })
        .then(res => {
            if (!res.ok) throw new Error('Erro na remoção de artigo: ' + res.statusText);

            return res.json();
        })
        .then(async data => {
            console.log('Sucesso: ', data);
            removeForm.reset();
            articles = await (await fetch('/articles')).json();
            loadArticles(articles);
        })
        .catch(error => {
            console.error('Erro: ', error);
            console.log('Erro ao excluir o artigo: ', error.message);
            removeOverlay.style.display = 'none';
        })

        removeOverlay.style.display = 'none';
    })

    searchForm.querySelector('input')
    .addEventListener('input', (event) => searchArticles(event, articles, searchForm));
    searchForm.querySelector('select')
    .addEventListener('input', (event) => searchArticles(event, articles, searchForm));
})
