const content = document.querySelector('#route-content');
const copies = {
  home: ['SPA home evidence', 'SPA home paragraph'],
  detail: ['SPA detail evidence', 'SPA detail paragraph'],
  note: ['SPA NOTE EVIDENCE', 'SPA note paragraph'],
  hash: ['section evidence', 'SPA section paragraph'],
  delayed: ['Delayed evidence', 'Delayed paragraph'],
  same: ['Same URL evidence', 'Same URL paragraph']
};
function currentView() {
  if (history.state?.view === 'same') return 'same';
  if (location.hash === '#section') return 'hash';
  const route = new URL(location.href).searchParams.get('route');
  return Object.hasOwn(copies, route) ? route : 'home';
}
function render(view) {
  const title = document.createElement('h1');
  title.className = 'shared-title';
  title.dataset.designId = 'route.title';
  title.textContent = copies[view][0];
  const paragraph = document.createElement('p');
  paragraph.className = 'route-body';
  paragraph.dataset.designId = 'route.body';
  paragraph.textContent = copies[view][1];
  content.dataset.view = view;
  content.dataset.renderState = 'settled';
  content.setAttribute('aria-busy', 'false');
  document.querySelector('#resolve-delayed').hidden = true;
  content.replaceChildren(title, paragraph);
}
document.querySelector('#push-detail').addEventListener('click', () => {
  history.pushState({view: 'detail'}, '', 'spa.html?route=detail');
  render('detail');
});
document.querySelector('#replace-note').addEventListener('click', () => {
  history.replaceState({view: 'note'}, '', 'spa.html?route=note');
  render('note');
});
document.querySelector('#back').addEventListener('click', () => history.back());
document.querySelector('#forward').addEventListener('click', () => history.forward());
document.querySelector('#replace-same').addEventListener('click', () => {
  history.replaceState({view: 'same'}, '', location.href);
  render('same');
});
document.querySelector('#load-delayed').addEventListener('click', () => {
  history.pushState({view: 'delayed'}, '', 'spa.html?route=delayed');
  content.dataset.renderState = 'pending';
  content.setAttribute('aria-busy', 'true');
  document.querySelector('#resolve-delayed').hidden = false;
});
// A local UI event resolves the deferred content; rAF performs the asynchronous render.
document.querySelector('#resolve-delayed').addEventListener('click', () => {
  requestAnimationFrame(() => render('delayed'));
});
window.addEventListener('popstate', () => render(currentView()));
window.addEventListener('hashchange', () => render(currentView()));
render(currentView());
