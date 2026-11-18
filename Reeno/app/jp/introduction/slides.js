'use strict';
const slides = Array.from(document.querySelectorAll('.slide'));
const viewport = document.querySelector('#viewport');
const counter = document.querySelector('#counter');
const previous = document.querySelector('#previous');
const next = document.querySelector('#next');
const toc = document.querySelector('#toc');
const tocGrid = document.querySelector('#toc-grid');
let current = 0;

function hashIndex() {
  const match = location.hash.match(/^#slide-(\d+)$/);
  return match ? Math.max(0, Math.min(slides.length - 1, Number(match[1]) - 1)) : 0;
}
function resize() {
  const scale = Math.min(viewport.clientWidth / 1600, viewport.clientHeight / 900);
  document.documentElement.style.setProperty('--scale', String(scale));
}
function render(index, updateHash = true) {
  const last = current;
  current = Math.max(0, Math.min(slides.length - 1, index));
  if (current !== last) viewport.scrollTop = 0;
  slides.forEach((slide, i) => {
    const active = i === current;
    slide.classList.toggle('active', active);
    slide.setAttribute('aria-hidden', String(!active));
    slide.inert = !active;
    // Pause a demo if a future revision adds video to a slide.
    if (!active) slide.querySelectorAll('video,audio').forEach(media => media.pause());
  });
  const slide = slides[current];
  counter.textContent = `${current + 1} / ${slides.length}`;
  previous.disabled = current === 0;
  next.disabled = current === slides.length - 1;
  document.querySelector('#announcement').textContent = `${current + 1}枚目：${slide.dataset.title}`;
  Array.from(tocGrid.children).forEach((button, i) => button.setAttribute('aria-current', String(i === current)));
  document.documentElement.style.setProperty('--progress', `${(current + 1) / slides.length * 100}%`);
  if (updateHash && location.hash !== `#slide-${current + 1}`) location.hash = `slide-${current + 1}`;
}
slides.forEach((slide, i) => {
  slide.dataset.number = `${String(i + 1).padStart(2, '0')} / ${slides.length}`;
  slide.setAttribute('role', 'group');
  slide.setAttribute('aria-roledescription', 'スライド');
  slide.setAttribute('aria-label', `${i + 1}. ${slide.dataset.title}`);
  const button = document.createElement('button');
  button.textContent = `${String(i + 1).padStart(2, '0')}  ${slide.dataset.title}`;
  button.addEventListener('click', () => { toc.close(); render(i); });
  tocGrid.append(button);
});
previous.addEventListener('click', () => render(current - 1));
next.addEventListener('click', () => render(current + 1));
function openToc() { toc.showModal(); tocGrid.children[current].focus(); }
document.querySelector('#toc-toggle').addEventListener('click', openToc);
document.querySelector('#toc-close').addEventListener('click', () => toc.close());
document.querySelector('#print').addEventListener('click', () => window.print());
const fullscreen = document.querySelector('#fullscreen');
if (!document.fullscreenEnabled) fullscreen.hidden = true;
async function toggleFullscreen() {
  try {
    if (document.fullscreenElement) await document.exitFullscreen();
    else await document.documentElement.requestFullscreen();
  } catch {
    document.querySelector('#announcement').textContent = '全画面表示を開始できません。ブラウザの全画面メニューを使用してください。';
  }
}
fullscreen.addEventListener('click', toggleFullscreen);
document.addEventListener('fullscreenchange', () => { fullscreen.textContent = document.fullscreenElement ? '全画面を終了' : '全画面'; resize(); });
document.addEventListener('keydown', event => {
  if (event.defaultPrevented || event.altKey || event.ctrlKey || event.metaKey || toc.open) return;
  if (event.target.closest('input,select,textarea,[contenteditable]')) return;
  if (event.key === ' ' && event.target.closest('button,a')) return;
  switch (event.key) {
    case 'ArrowRight': case 'ArrowDown': case 'PageDown': case ' ': event.preventDefault(); render(current + 1); break;
    case 'ArrowLeft': case 'ArrowUp': case 'PageUp': event.preventDefault(); render(current - 1); break;
    case 'Home': event.preventDefault(); render(0); break;
    case 'End': event.preventDefault(); render(slides.length - 1); break;
    case 'o': case 'O': openToc(); break;
    case 'f': case 'F': if (document.fullscreenEnabled) toggleFullscreen(); break;
  }
});
window.addEventListener('hashchange', () => render(hashIndex(), false));
window.addEventListener('resize', resize);
new ResizeObserver(resize).observe(viewport);
render(hashIndex(), false);
resize();
