const SAFE_METHODS = ['GET', 'HEAD'];

export class ApiError extends Error {
    constructor(status, message, errors = {}) {
        super(message);
        this.name = 'ApiError';
        this.status = status;
        // Error codes by field, when the API reports which fields are invalid.
        this.errors = errors;
    }
}

function csrfToken() {
    return document.querySelector('meta[name="csrf-token"]').content;
}

async function request(endpoint, { method = 'GET', json, formData } = {}) {
    const headers = {};
    if (!SAFE_METHODS.includes(method)) headers['X-CSRF-Token'] = csrfToken();
    if (json !== undefined) headers['Content-Type'] = 'application/json';

    // A FormData body sets its own multipart content type with the boundary.
    const res = await fetch(endpoint, {
        method,
        headers,
        body: formData ?? (json === undefined ? undefined : JSON.stringify(json)),
    });
    const body = await res.json().catch(() => ({}));

    if (res.status === 401) {
        window.location.assign(body.login_url || '/auth/login');
        // The page is leaving, so callers must not react as if the request failed.
        return new Promise(() => {});
    }
    if (!res.ok) {
        throw new ApiError(res.status, body.message || `Erro ${res.status}`, body.errors);
    }
    return body;
}

export const API = {
    fetchAll() {
        return request('/api/articles');
    },

    fetchArticlesBy(username) {
        return request(`/api/articles?author=${encodeURIComponent(username)}`);
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

    updateProfile(fields) {
        return request('/api/users/me', { method: 'PATCH', json: fields });
    },

    uploadAvatar(file) {
        const formData = new FormData();
        formData.append('avatar', file);
        return request('/api/users/me/avatar', { method: 'PUT', formData });
    },

    removeAvatar() {
        return request('/api/users/me/avatar', { method: 'DELETE' });
    },
};
