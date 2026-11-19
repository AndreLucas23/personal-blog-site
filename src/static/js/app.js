// Behavior shared by every page. Each page adds its own module from js/pages/.
import { formatDate } from './ui/format.js';
import { initMenus } from './ui/menu.js';
import { initThemePicker } from './ui/theme-picker.js';
import { showPendingToast } from './ui/toast.js';

// Pages print dates in UTC; the reader's own time zone may be on another day.
document.querySelectorAll('time[data-local-date]').forEach((time) => {
    time.textContent = formatDate(time.dateTime);
});

initMenus();
initThemePicker();
showPendingToast();
