// Função para carregamento dos artigos armazenados
function loadArticles() {
    const articlesList = document.getElementById('articles-list');

    articlesList.innerHTML = '';

    fetch('/articles')
    .then(res => res.json())
    .then(articlesRes => {
        articlesRes.forEach(article => {
            localDate = new Date(article['publish-date']).toLocaleString()

            let newArticle = document.createElement('li');
            newArticle.textContent = `ID: ${article['article-id']}, 
            Título: ${article['article-title']},
            Data de publicação: ${localDate}`;
            articlesList.appendChild(newArticle);
        })
    })
    .catch(error => console.error('Erro: ', error));
}

// Procedimento a partir do carregamento do DOM
document.addEventListener('DOMContentLoaded', () => {
    loadArticles();

    const addButton = document.getElementById('add-button');
    const removeButton = document.getElementById('remove-button');
    const addOverlay = document.getElementById('add-popup-overlay');
    const removeOverlay = document.getElementById('remove-popup-overlay');
    const addForm = document.getElementById('add-form');
    const removeForm = document.getElementById('remove-form');
    const cancelButtons = document.getElementsByClassName('cancel-button');
    const popups = document.getElementsByClassName('popup');

    // Função para abertura do pop-up de adição de artigo
    addButton.addEventListener('click', () => addOverlay.style.display = 'flex');

    // Função para abertura do pop-up de remoção de artigo
    removeButton.addEventListener('click', () => removeOverlay.style.display = 'flex');
    
    // Função para fechamento dos pop-ups
    Array.from(cancelButtons).forEach(button => 
        button.addEventListener('click', () => 
            button.parentElement.parentElement.style.display = 'none'));
    
    Array.from(popups).forEach(popup => {
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') popup.parentElement.style.display = 'none';
        })
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
        .then(data => {
            console.log('Sucesso: ', data);
            addForm.reset();
        })
        .catch(error => {
            console.error('Erro: ', error);
            alert('Erro ao enviar o formulário: ' + error.message);
        })

        loadArticles();
        addOverlay.style.display = 'none';
    })

    // Função para remoção de artigo do banco de dados
    removeForm.addEventListener('submit', async (event) => {
        event.preventDefault();

        const articleId = document.getElementById('remove-input').value
        const url = `/articles/${articleId}`

        await fetch(url, {
            method: 'DELETE',
        })
        .then(res => {
            if (!res.ok) throw new Error('Erro na remoção de artigo: ' + res.statusText);

            return res.json();
        })
        .then(data => {
            console.log('Sucesso: ', data);
            removeForm.reset();
        })
        .catch(error => {
            console.error('Erro: ', error);
            console.log('Erro ao excluir o artigo: ', error.message);
            removeOverlay.style.display = 'none';
        })

        loadArticles();
        removeOverlay.style.display = 'none';
    })
})
