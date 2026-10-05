import { fontkitStudio } from 'fontkitstudio/vite';

// Must not type-check: fontkitStudio() returns a Vite plugin, not a number.
const n: number = fontkitStudio();
export default n;
