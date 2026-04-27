/* Secure Tours & Travel — Main JS */

(function () {
  'use strict';

  /* ── Language Management ── */
  const DEFAULT_LANG = 'en';
  let currentLang = localStorage.getItem('st_lang') || DEFAULT_LANG;

  function setLang(lang) {
    currentLang = lang;
    localStorage.setItem('st_lang', lang);
    document.documentElement.lang = lang === 'zh' ? 'zh-CN' : 'en';
    document.body.classList.toggle('zh-content', lang === 'zh');
    renderTranslations();
    updateLangButtons();
  }

  function t(key) {
    const d = TRANSLATIONS[currentLang] || TRANSLATIONS[DEFAULT_LANG];
    return d[key] || TRANSLATIONS[DEFAULT_LANG][key] || key;
  }

  function renderTranslations() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      const val = t(key);
      if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
        el.placeholder = val;
      } else {
        el.innerHTML = val;
      }
    });

    document.querySelectorAll('[data-i18n-attr]').forEach(el => {
      try {
        const pairs = JSON.parse(el.getAttribute('data-i18n-attr'));
        Object.entries(pairs).forEach(([attr, key]) => {
          el.setAttribute(attr, t(key));
        });
      } catch (e) {}
    });
  }

  function updateLangButtons() {
    document.querySelectorAll('.lang-btn').forEach(btn => {
      btn.classList.toggle('active', btn.getAttribute('data-lang') === currentLang);
    });
  }

  /* ── Navigation ── */
  function initNav() {
    const nav = document.querySelector('.site-nav');
    const toggle = document.querySelector('.nav-toggle');
    const links = document.querySelector('.nav-links');

    // Scroll state
    window.addEventListener('scroll', () => {
      nav?.classList.toggle('scrolled', window.scrollY > 30);
    }, { passive: true });

    // Mobile toggle
    toggle?.addEventListener('click', () => {
      links?.classList.toggle('open');
      const expanded = links?.classList.contains('open');
      toggle.setAttribute('aria-expanded', String(expanded));
    });

    // Mobile dropdown toggles
    document.querySelectorAll('.nav-links > li > a').forEach(a => {
      if (a.nextElementSibling?.classList.contains('nav-dropdown')) {
        a.addEventListener('click', e => {
          if (window.innerWidth <= 900) {
            e.preventDefault();
            a.parentElement.classList.toggle('open');
          }
        });
      }
    });

    // Close mobile nav on outside click
    document.addEventListener('click', e => {
      if (!nav?.contains(e.target)) {
        links?.classList.remove('open');
      }
    });

    // Language buttons
    document.querySelectorAll('.lang-btn').forEach(btn => {
      btn.addEventListener('click', () => setLang(btn.getAttribute('data-lang')));
    });

    // Active nav link
    const path = window.location.pathname;
    document.querySelectorAll('.nav-links a').forEach(a => {
      const href = a.getAttribute('href');
      if (href && path.endsWith(href.replace('../', '').replace('./', ''))) {
        a.classList.add('active');
      }
    });
  }

  /* ── Contact Form ── */
  // DEPLOY NOTE: Replace FORMSPREE_FORM_ID with your actual Formspree form ID.
  // Get one free at https://formspree.io — create a form, copy the 8-char ID from the endpoint URL.
  const FORMSPREE_ENDPOINT = 'https://formspree.io/f/FORMSPREE_FORM_ID';

  function initContactForm() {
    const form = document.getElementById('contact-form');
    if (!form) return;

    form.addEventListener('submit', async e => {
      e.preventDefault();
      const btn = form.querySelector('button[type="submit"]');
      const originalText = btn.textContent;
      btn.textContent = currentLang === 'zh' ? '发送中…' : 'Sending…';
      btn.disabled = true;

      const data = new FormData(form);
      // Pass language so Formspree notifications include it
      data.append('_language', currentLang);

      try {
        const res = await fetch(FORMSPREE_ENDPOINT, {
          method: 'POST',
          body: data,
          headers: { Accept: 'application/json' }
        });

        if (res.ok) {
          const msg = document.getElementById('form-success');
          if (msg) {
            form.style.display = 'none';
            msg.style.display = 'block';
          } else {
            btn.textContent = currentLang === 'zh' ? '已发送 ✓' : 'Sent ✓';
          }
        } else {
          throw new Error('submission failed');
        }
      } catch {
        btn.textContent = originalText;
        btn.disabled = false;
        alert(currentLang === 'zh'
          ? '提交失败，请稍后重试或直接发送电子邮件。'
          : 'Submission failed — please try again or email us directly.');
      }
    });
  }

  /* ── Scroll Animations ── */
  function initScrollAnimations() {
    if (!window.IntersectionObserver) return;

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });

    document.querySelectorAll('.service-card, .why-item, .stat-item, .feature-list li').forEach(el => {
      el.classList.add('reveal');
      observer.observe(el);
    });
  }

  /* ── Init ── */
  document.addEventListener('DOMContentLoaded', () => {
    initNav();
    initContactForm();
    initScrollAnimations();
    setLang(currentLang);
  });

  // Expose setLang globally for inline usage
  window.setLang = setLang;
  window.t = t;

})();
