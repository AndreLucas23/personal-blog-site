// What members read when an image they chose cannot be used.

/** The message for each error code of an image upload, with the size limit of the server. */
export function imageErrors(maxBytes) {
    return {
        image_missing: 'Escolha uma imagem.',
        image_invalid: 'Não foi possível ler essa imagem. Tente outro arquivo.',
        image_format: 'Use uma imagem JPEG, PNG ou WebP.',
        image_too_large: `A imagem pode ter até ${Math.floor(maxBytes / (1024 * 1024))} MB.`,
    };
}
