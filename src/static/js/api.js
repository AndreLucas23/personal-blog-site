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
        // After signing in, the member comes back to this page.
        const login = new URL(body.login_url || '/auth/login', window.location.origin);
        login.searchParams.set('next', `${window.location.pathname}${window.location.search}`);
        window.location.assign(login.href);
        // The page is leaving, so callers must not react as if the request failed.
        return new Promise(() => {});
    }
    if (!res.ok) {
        throw new ApiError(res.status, body.message || `Erro ${res.status}`, body.errors);
    }
    return body;
}

function pageQuery(params) {
    const query = new URLSearchParams(Object.entries(params).filter(([, value]) => value != null)).toString();
    return query ? `?${query}` : '';
}

export const API = {
    /** A page of articles, newest first: {articles, next_cursor}. */
    fetchAll(cursor = null) {
        return request(`/api/articles${pageQuery({ cursor })}`);
    },

    fetchArticlesBy(username, cursor = null) {
        return request(`/api/articles${pageQuery({ author: username, cursor })}`);
    },

    fetchDrafts() {
        return request('/api/users/me/drafts');
    },

    createArticle(fields) {
        return request('/api/articles', { method: 'POST', json: fields });
    },

    updateArticle(articleId, fields) {
        return request(`/api/articles/${articleId}`, { method: 'PATCH', json: fields });
    },

    deleteArticle(articleId) {
        return request(`/api/articles/${articleId}`, { method: 'DELETE' });
    },

    preview(content) {
        return request('/api/previews', { method: 'POST', json: { content } });
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

    follow(username) {
        return request(`/api/users/${encodeURIComponent(username)}/follow`, { method: 'PUT' });
    },

    unfollow(username) {
        return request(`/api/users/${encodeURIComponent(username)}/follow`, { method: 'DELETE' });
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

    uploadCover(articleId, file) {
        const formData = new FormData();
        formData.append('cover', file);
        return request(`/api/articles/${articleId}/cover`, { method: 'PUT', formData });
    },

    removeCover(articleId) {
        return request(`/api/articles/${articleId}/cover`, { method: 'DELETE' });
    },
};
