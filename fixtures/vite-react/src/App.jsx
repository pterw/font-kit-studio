import React, { useState } from 'react';

export default function App() {
  const [count, setCount] = useState(0);
  return (
    <main>
      <h1 data-design-id="vite.hero.title">Type that fits the page</h1>
      <p data-design-id="vite.hero.lead">
        Pick fonts against the real page, then keep the CSS that Studio writes.
      </p>
      <button data-design-id="vite.hero.cta" onClick={() => setCount(count + 1)}>
        Clicked {count} times
      </button>
    </main>
  );
}
