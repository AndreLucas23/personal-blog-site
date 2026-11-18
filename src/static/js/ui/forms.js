/** Show "length / max" next to a field and warn near the limit. Returns the update function. */
export function bindCounter(input, counter) {
    const max = Number(input.getAttribute('maxlength'));

    const update = () => {
        const length = input.value.length;
        counter.textContent = max ? `${length} / ${max}` : String(length);
        counter.classList.toggle('is-at-limit', Boolean(max) && length >= max);
        counter.classList.toggle('is-near-limit', Boolean(max) && length < max && length >= max * 0.9);
    };

    input.addEventListener('input', update);
    update();
    return update;
}

/** Show or clear the error of a field, in the element named by aria-describedby. */
export function setFieldError(input, message) {
    const errorId = (input.getAttribute('aria-describedby') || '')
        .split(' ')
        .find((id) => id.endsWith('-error'));
    const errorEl = errorId ? document.getElementById(errorId) : null;

    if (errorEl) errorEl.textContent = message;
    if (message) input.setAttribute('aria-invalid', 'true');
    else input.removeAttribute('aria-invalid');

    // The error goes away as soon as the member edits the field.
    if (message && !input.dataset.errorBound) {
        input.dataset.errorBound = 'true';
        input.addEventListener('input', () => {
            delete input.dataset.errorBound;
            setFieldError(input, '');
        }, { once: true });
    }
}
