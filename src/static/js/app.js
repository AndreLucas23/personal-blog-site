// Behavior shared by every page. Each page adds its own module from js/pages/.
import { initMenus } from './ui/menu.js';
import { initThemePicker } from './ui/theme-picker.js';

initMenus();
initThemePicker();
