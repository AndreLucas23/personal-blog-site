const SAFE_METHODS = ['GET', 'HEAD'];

export class ApiError extends Error {
    constructor(status, message) {
        super(message);
        this.name = 'ApiError';
        this.status = status;
    }
}

function csrfToken() {
    return document.querySelector('meta[name="csrf-token"]').content;
}

async function request(endpoint, { method = 'GET', json } = {}) {
    const headers = {};
    if (!SAFE_METHODS.includes(method)) headers['X-CSRF-Token'] = csrfToken();
    if (json !== undefined) headers['Content-Type'] = 'application/json';

    const res = await fetch(endpoint, {
        method,
        headers,
        body: json === undefined ? undefined : JSON.stringify(json),
    });
    const body = await res.json().catch(() => ({}));

    if (res.status === 401) {
        window.location.assign(body.login_url || '/auth/login');
    }
    if (!res.ok) {
        throw new ApiError(res.status, body.message || `Erro ${res.status}`);
    }
    return body;
}

export const API = {
    fetchAll() {
        return request('/api/articles');
    },

    add(data) {
        return request('/api/articles', { method: 'POST', json: data });
    },

    remove(articleId) {
        return request(`/api/articles/${articleId}`, { method: 'DELETE' });
    },

    update(articleId, data) {
        return request(`/api/articles/${articleId}`, { method: 'PATCH', json: data });
    },

    like(articleId) {
        return request(`/api/articles/${articleId}/likes`, { method: 'POST' });
    },

    unlike(articleId) {
        return request(`/api/articles/${articleId}/likes`, { method: 'DELETE' });
    },

    searchByTitle(query) {
        return request(`/api/articles/title/${encodeURIComponent(query)}`);
    },

    searchById(query) {
        return request(`/api/articles/id/${encodeURIComponent(query)}`);
    },
};
