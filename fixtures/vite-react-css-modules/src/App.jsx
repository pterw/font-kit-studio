import React, { useState } from 'react';
import styles from './App.module.css';

// Vite injects updated CSS; stable module names let existing React nodes keep it.
// Accept only the stylesheet dependency, without claiming React Fast Refresh.
if (import.meta.hot) import.meta.hot.accept('./App.module.css', () => {});

export default function App() {
  const [generation, setGeneration] = useState(0);
  return (
    <main>
      {/* Changing this key exercises real React replacement, not just a text update. */}
      <section key={generation}>
        <h1 className={styles.title} data-design-role="display" data-design-id="modules.title">Module title {generation}</h1>
        <p className={styles.body} data-design-role="body" data-design-id="modules.body.first">Body copy {generation}</p>
        <p className={styles.body} data-design-role="body" data-design-id="modules.body.second">Secondary body copy</p>
      </section>
      <aside><p className={styles.hashOnly}>Hash only copy</p></aside>
      <p className="stable-copy">Stable class comparison</p>
      <button className={styles.action} type="button" data-design-id="modules.replace"
        onClick={() => setGeneration(value => value + 1)}>Replace text</button>
    </main>
  );
}
