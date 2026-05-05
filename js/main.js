/* Secure Tours & Travel — Main JS */

(function () {
  'use strict';

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
      btn.textContent = 'Sending…';
      btn.disabled = true;

      const data = new FormData(form);

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
            btn.textContent = 'Sent ✓';
          }
        } else {
          throw new Error('submission failed');
        }
      } catch {
        btn.textContent = originalText;
        btn.disabled = false;
        alert('Submission failed — please try again or email us directly.');
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

    // Add reveal class to standard home-page elements
    document.querySelectorAll('.service-card, .why-item, .stat-item, .feature-list li').forEach(el => {
      el.classList.add('reveal');
    });

    // Observe all elements that carry the reveal class (including those set in HTML)
    document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
  }

  /* ── i18n ── */
  function applyTranslations(lang) {
    if (typeof TRANSLATIONS === 'undefined') return;
    const t = TRANSLATIONS[lang] || TRANSLATIONS.en;
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      if (t[key] !== undefined) el.innerHTML = t[key];
    });
  }

  /* ── Init ── */
  document.addEventListener('DOMContentLoaded', () => {
    applyTranslations('en');
    initNav();
    initContactForm();
    initScrollAnimations();
  });

})();
