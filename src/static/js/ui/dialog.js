import { el, icon } from './dom.js';

/** Close a dialog from its close buttons and from a click on the backdrop. */
export function bindDialog(dialog) {
    dialog.addEventListener('click', (event) => {
        // The panel fills the dialog, so a click on the dialog itself landed on the backdrop.
        if (event.target === dialog) dialog.close();
    });

    dialog.querySelectorAll('[data-dialog-close]').forEach((button) => {
        button.addEventListener('click', () => dialog.close());
    });
}

/** Ask for confirmation. Resolves to true only when the member confirms. */
export function confirmDialog({ title, message, confirmLabel = 'Confirmar', danger = false }) {
    return new Promise((resolve) => {
        const confirmButton = el('button', {
            class: `btn ${danger ? 'btn--danger' : 'btn--primary'}`,
            type: 'button',
            text: confirmLabel,
        });
        const cancelButton = el('button', { class: 'btn btn--ghost', type: 'button', text: 'Cancelar' });
        const titleId = `confirm-title-${Date.now()}`;

        const dialog = el(
            'dialog',
            { class: 'dialog dialog--sm', 'aria-labelledby': titleId },
            el(
                'div',
                { class: 'dialog__panel' },
                el(
                    'div',
                    { class: 'dialog__header' },
                    el('h2', { class: 'dialog__title', id: titleId, text: title }),
                    el(
                        'button',
                        { class: 'icon-btn', type: 'button', 'aria-label': 'Fechar', 'data-dialog-close': true },
                        icon('close'),
                    ),
                ),
                el('div', { class: 'dialog__body' }, el('p', { text: message })),
                el('div', { class: 'dialog__footer' }, cancelButton, confirmButton),
            ),
        );

        let confirmed = false;
        confirmButton.addEventListener('click', () => {
            confirmed = true;
            dialog.close();
        });
        cancelButton.addEventListener('click', () => dialog.close());
        dialog.addEventListener('close', () => {
            dialog.remove();
            resolve(confirmed);
        });

        bindDialog(dialog);
        document.body.append(dialog);
        dialog.showModal();
        cancelButton.focus();
    });
}
