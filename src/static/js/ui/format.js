const LOCALE = 'pt-BR';

const relativeFormat = new Intl.RelativeTimeFormat(LOCALE, { numeric: 'auto' });
const dateFormat = new Intl.DateTimeFormat(LOCALE, { day: 'numeric', month: 'short', year: 'numeric' });
const dateTimeFormat = new Intl.DateTimeFormat(LOCALE, { dateStyle: 'long', timeStyle: 'short' });
const countFormat = new Intl.NumberFormat(LOCALE, { notation: 'compact', maximumFractionDigits: 1 });

const UNITS = [
    ['second', 60],
    ['minute', 60],
    ['hour', 24],
    ['day', 7],
];

// Older dates read better as a date than as "5 weeks ago".
const RELATIVE_LIMIT_DAYS = 7;

export function toDate(value) {
    return value instanceof Date ? value : new Date(value);
}

function isValid(date) {
    return !Number.isNaN(date.getTime());
}

/** The date in ISO 8601, or null when the value is not a date. */
export function isoString(value) {
    const date = toDate(value);
    return isValid(date) ? date.toISOString() : null;
}

export function timeAgo(value) {
    const date = toDate(value);
    if (!isValid(date)) return '';

    let amount = (date.getTime() - Date.now()) / 1000;

    if (Math.abs(amount) >= RELATIVE_LIMIT_DAYS * 24 * 60 * 60) {
        return dateFormat.format(date);
    }

    for (const [unit, size] of UNITS) {
        if (Math.abs(amount) < size) {
            return relativeFormat.format(Math.round(amount), unit);
        }
        amount /= size;
    }
    return dateFormat.format(date);
}

export function formatDate(value) {
    const date = toDate(value);
    return isValid(date) ? dateFormat.format(date) : '';
}

export function formatDateTime(value) {
    const date = toDate(value);
    return isValid(date) ? dateTimeFormat.format(date) : '';
}

/** Whether a date falls on a later day than another, in the reader's time zone. */
export function isLaterDay(value, other) {
    const day = (date) => date.getFullYear() * 10000 + date.getMonth() * 100 + date.getDate();
    const date = toDate(value);
    const otherDate = toDate(other);
    return isValid(date) && isValid(otherDate) && day(date) > day(otherDate);
}

export function formatCount(value) {
    return countFormat.format(value);
}
