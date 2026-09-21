export const API = {
    async _fetch(endpoint, options = {}) {
        const res = await fetch(endpoint, options);
        if (!res.ok) {
            throw new Error(`Erro na API: ${res.status} ${res.statusText}`);
        }
        return res.json();
    },

    async fetchAll() {
        return this._fetch('/api/articles', { method: 'GET' });
    },

    async add(data) {
        return this._fetch('/api/articles', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
    },

    async remove(articleId) {
        return this._fetch(`/api/articles/${articleId}`, { method: 'DELETE' });
    },

    async update(articleId, data) {
        return this._fetch(`/api/articles/${articleId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
    },

    async searchByTitle(query) {
        return this._fetch(`/api/articles/title/${encodeURIComponent(query)}`);
    },

    async searchById(query) {
        return this._fetch(`/api/articles/id/${encodeURIComponent(query)}`);
    }
};
