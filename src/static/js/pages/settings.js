import { API, ApiError } from '../api.js';
import { avatar } from '../ui/avatar.js';
import { el, icon } from '../ui/dom.js';
import { bindCounter, setFieldError } from '../ui/forms.js';
import { showToast } from '../ui/toast.js';

const FIELDS = ['display_name', 'username', 'headline', 'location', 'website', 'bio'];

const PROFILE_ERRORS = {
    name_required: 'Informe seu nome.',
    name_too_long: 'O nome pode ter até 50 caracteres.',
    username_required: 'Escolha um nome de usuário.',
    username_too_short: 'O nome de usuário precisa ter pelo menos 3 caracteres.',
    username_too_long: 'O nome de usuário pode ter até 30 caracteres.',
    username_invalid: 'Use só letras minúsculas sem acento, números e _.',
    username_reserved: 'Este nome de usuário não está disponível.',
    username_taken: 'Este nome de usuário já está em uso.',
    headline_too_long: 'O título pode ter até 120 caracteres.',
    bio_too_long: 'O texto pode ter até 500 caracteres.',
    location_too_long: 'A localização pode ter até 80 caracteres.',
    website_too_long: 'O endereço pode ter até 200 caracteres.',
    website_invalid: 'Informe um endereço como seusite.com.br ou https://seusite.com.br.',
    invalid: 'Confira este campo.',
};

// The server sets the limit, so this page reads it instead of keeping a copy.
const MAX_IMAGE_BYTES = Number(document.getElementById('avatar-input').dataset.maxBytes);

const IMAGE_ERRORS = {
    image_missing: 'Escolha uma imagem.',
    image_invalid: 'Não foi possível ler essa imagem. Tente outro arquivo.',
    image_format: 'Use uma imagem JPEG, PNG ou WebP.',
    image_too_large: `A imagem pode ter até ${Math.floor(MAX_IMAGE_BYTES / (1024 * 1024))} MB.`,
};

const form = document.getElementById('profile-form');
const submitButton = document.getElementById('profile-submit');
const inputs = Object.fromEntries(FIELDS.map((field) => [field, form.elements[field]]));

let currentName = inputs.display_name.value;
let currentAvatarUrl = document.querySelector('#avatar-current img')?.getAttribute('src') ?? null;

// Pieces of the page that show the signed-in member, kept in step after a change.
function showIdentity({ display_name: name, username, avatar_url: avatarUrl }) {
    const nameChanged = name !== undefined && name !== currentName;
    const photoChanged = avatarUrl !== undefined && avatarUrl !== currentAvatarUrl;

    if (nameChanged) {
        currentName = name;
        document.querySelectorAll('[data-me-name]').forEach((node) => { node.textContent = name; });
    }
    if (username !== undefined) {
        document.querySelectorAll('[data-me-username]').forEach((node) => { node.textContent = `@${username}`; });
        document.querySelectorAll('[data-me-profile-link]').forEach((link) => { link.href = `/@${username}`; });
    }
    if (photoChanged) currentAvatarUrl = avatarUrl;

    // Initials come from the name, so a new name only matters while there is no photo.
    if (photoChanged || (nameChanged && !currentAvatarUrl)) {
        document.querySelectorAll('[data-me-avatar]').forEach((slot) => {
            slot.replaceChildren(avatar(currentName, slot.dataset.meAvatar, currentAvatarUrl, { eager: true }));
        });
    }
}

function fillForm(profile) {
    FIELDS.forEach((field) => {
        inputs[field].value = profile[field] ?? '';
        inputs[field].dispatchEvent(new Event('input'));
    });
}

function setUpProfileForm() {
    form.querySelectorAll('[maxlength]').forEach((input) => {
        const counter = document.getElementById(`${input.id}-counter`);
        if (counter) bindCounter(input, counter);
    });

    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        FIELDS.forEach((field) => setFieldError(inputs[field], ''));

        submitButton.classList.add('is-loading');
        submitButton.disabled = true;

        try {
            const profile = await API.updateProfile(
                Object.fromEntries(FIELDS.map((field) => [field, inputs[field].value])),
            );
            fillForm(profile);
            showIdentity(profile);
            showToast('Perfil atualizado.', { type: 'success' });
        } catch (error) {
            const invalid = error instanceof ApiError ? Object.entries(error.errors || {}) : [];
            if (!invalid.length) {
                console.error(error);
                showToast('Não foi possível salvar o perfil. Tente de novo.', { type: 'error' });
                return;
            }
            invalid.forEach(([field, code]) => {
                if (inputs[field]) setFieldError(inputs[field], PROFILE_ERRORS[code] || PROFILE_ERRORS.invalid);
            });
            inputs[invalid[0][0]]?.focus();
        } finally {
            submitButton.classList.remove('is-loading');
            submitButton.disabled = false;
        }
    });
}

function setUpPhoto() {
    const pickButton = document.getElementById('avatar-pick');
    const removeButton = document.getElementById('avatar-remove');
    const fileInput = document.getElementById('avatar-input');
    const errorEl = document.getElementById('avatar-error');

    const showPhotoState = () => {
        removeButton.hidden = !currentAvatarUrl;
        pickButton.replaceChildren(
            icon('upload', 'icon--sm'),
            el('span', { text: currentAvatarUrl ? 'Trocar foto' : 'Enviar foto' }),
        );
    };

    const busy = (button, isBusy) => {
        button.classList.toggle('is-loading', isBusy);
        pickButton.disabled = isBusy;
        removeButton.disabled = isBusy;
    };

    pickButton.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', async () => {
        const [file] = fileInput.files;
        fileInput.value = '';
        if (!file) return;

        errorEl.textContent = '';
        // Checked here too, so a large photo is refused before it is sent.
        if (file.size > MAX_IMAGE_BYTES) {
            errorEl.textContent = IMAGE_ERRORS.image_too_large;
            return;
        }

        busy(pickButton, true);
        try {
            const { avatar_url: avatarUrl } = await API.uploadAvatar(file);
            showIdentity({ avatar_url: avatarUrl });
            showPhotoState();
            showToast('Foto atualizada.', { type: 'success' });
        } catch (error) {
            const code = error instanceof ApiError ? error.errors?.avatar : null;
            if (!code) console.error(error);
            errorEl.textContent = IMAGE_ERRORS[code] || 'Não foi possível enviar a foto. Tente de novo.';
        } finally {
            busy(pickButton, false);
            // The button was disabled while sending, which took the focus away from it.
            pickButton.focus();
        }
    });

    removeButton.addEventListener('click', async () => {
        errorEl.textContent = '';
        busy(removeButton, true);
        try {
            await API.removeAvatar();
            showIdentity({ avatar_url: null });
            showPhotoState();
            showToast('Foto removida.', { type: 'success' });
        } catch (error) {
            console.error(error);
            errorEl.textContent = 'Não foi possível remover a foto. Tente de novo.';
        } finally {
            busy(removeButton, false);
            // The remove button hides once the photo is gone.
            pickButton.focus();
        }
    });
}

setUpProfileForm();
setUpPhoto();
