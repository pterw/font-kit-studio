// The permanent setup a user adds; imported by path so the fixture needs no install of
// the package. `vite build` must leave it out entirely (apply: 'serve').
import { fontkitStudio } from '../../packages/fontkitstudio/src/vite-plugin.js';

export default { plugins: [fontkitStudio()] };
