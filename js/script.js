(() => {
  'use strict';

  const nav = document.getElementById('mainnav');
  if (!nav) return;

  const menu = document.getElementById('menu');
  const menuIcon = document.getElementById('menuBtn');
  const panel = nav.querySelector('.panel');
  const links = nav.querySelectorAll('ul a');
  const mobile = window.matchMedia('(max-width: 799px)');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const sidebar = nav.closest('#sidebar');

  function setMenuOpen(open) {
    if (panel) panel.style.display = open ? 'block' : '';
    if (menuIcon) menuIcon.classList.toggle('close', open);
    if (menu) menu.setAttribute('aria-expanded', String(open));
  }

  if (menu && panel) {
    panel.id = panel.id || 'navigation-panel';
    menu.setAttribute('role', 'button');
    menu.setAttribute('tabindex', '0');
    menu.setAttribute('aria-label', 'Menu');
    menu.setAttribute('aria-controls', panel.id);
    menu.addEventListener('click', () => {
      setMenuOpen(menu.getAttribute('aria-expanded') !== 'true');
    });
    menu.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        menu.click();
      }
    });
    nav.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && mobile.matches) {
        setMenuOpen(false);
        menu.focus();
      }
    });
  }

  links.forEach((link) => {
    link.addEventListener('click', (event) => {
      const href = link.getAttribute('href');
      if (!href || !href.startsWith('#')) return;
      const target = document.getElementById(href.slice(1));
      if (!target) return;

      event.preventDefault();
      links.forEach((item) => item.classList.remove('active'));
      link.classList.add('active');
      if (mobile.matches) setMenuOpen(false);

      // Sidebar pages have a fixed mobile header; the portfolio has a fixed desktop header.
      const offset = sidebar
        ? (mobile.matches ? document.getElementById('sidebarWrap').offsetHeight : 20)
        : (mobile.matches ? 0 : nav.offsetHeight);
      window.scrollTo({
        top: Math.max(0, target.getBoundingClientRect().top + window.scrollY - offset),
        behavior: reducedMotion.matches ? 'instant' : 'smooth'
      });
    });
  });

  const updateNavigation = () => nav.classList.toggle('changeNav', window.scrollY > 80);
  window.addEventListener('scroll', updateNavigation, { passive: true });
  mobile.addEventListener('change', () => setMenuOpen(false));
  setMenuOpen(false);
  updateNavigation();
})();
