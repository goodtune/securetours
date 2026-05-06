/**
 * A/B Structural Test Suite
 * Asserts that Site B (Zensical) matches Site A (Astro) structurally.
 *
 * Run from workspace root:
 *   node tests/ab-structural.js
 */

const puppeteer = require('puppeteer-core');
const { spawn } = require('child_process');
const http = require('http');

const CHROME = '/home/paperclip/.cache/ms-playwright/chromium_headless_shell-1217/chrome-headless-shell-linux64/chrome-headless-shell';
const LIBPATH = '/tmp/deplibs/extracted/usr/lib/x86_64-linux-gnu:/tmp/deplibs/extracted/lib/x86_64-linux-gnu';

const SITE_A = 'https://securetours.staging-site.au';
const SITE_B = 'https://secure-tours-zensical-gysk6.ondigitalocean.app';

const PAGE_PAIRS = [
  { slug: 'home',         a: '/',                                         b: '/' },
  { slug: 'about',        a: '/about.html',                               b: '/about/' },
  { slug: 'services',     a: '/services/index.html',                      b: '/services/' },
  { slug: 'concierge',    a: '/services/concierge-chaperone.html',        b: '/services/concierge-chaperone/' },
  { slug: 'executive',    a: '/services/executive-guest-management.html', b: '/services/executive-guest-management/' },
  { slug: 'solo',         a: '/services/solo-traveller-assist.html',      b: '/services/solo-traveller-assist/' },
  { slug: 'articles',     a: '/articles.html',                            b: '/articles/' },
  { slug: 'contact',      a: '/contact.html',                             b: '/contact/' },
];

let portCounter = 9700;
function nextPort() { return portCounter += 2; }

function waitForPort(port, retries = 40) {
  return new Promise((resolve, reject) => {
    let attempts = 0;
    const check = () => {
      const req = http.get(`http://localhost:${port}/json/version`, res => {
        let data = '';
        res.on('data', d => data += d);
        res.on('end', () => { try { resolve(JSON.parse(data)); } catch { resolve({}); } });
      });
      req.on('error', () => {
        attempts++;
        if (attempts >= retries) reject(new Error(`Port ${port} not ready`));
        else setTimeout(check, 300);
      });
      req.setTimeout(1000, () => req.destroy());
    };
    check();
  });
}

async function extractStructure(page, url) {
  const resp = await page.goto(url, { waitUntil: 'networkidle0', timeout: 30000 });
  const status = resp ? resp.status() : 0;

  return page.evaluate(() => {
    const text = el => el ? el.textContent.trim() : null;
    const count = sel => document.querySelectorAll(sel).length;
    const all = (sel, fn) => Array.from(document.querySelectorAll(sel)).map(fn);

    // Nav links (top-level only, deduplicated by text)
    const navLinks = all('nav a, .site-nav a, .md-nav--primary > ul > li > a', el =>
      el.textContent.trim()
    ).filter(t => t.length > 0);

    // Footer columns (h4 headings)
    const footerHeadings = all(
      '.footer-col h4, .site-footer h4, .md-footer h4',
      el => el.textContent.trim()
    );

    // Dropdown items
    const dropdownItems = all(
      '.nav-dropdown a, .md-nav__item--nested a',
      el => el.textContent.trim()
    ).filter(t => t.length > 0);

    // Page h2 headings
    const h2s = all('h2', el => el.textContent.trim().replace(/\s*¶$/, ''));

    // Card counts
    const cardCount = count('.st-card, .service-card, .card');

    // Computed nav background (first nav element)
    const nav = document.querySelector('nav, .site-nav, .md-header');
    const navBg = nav ? getComputedStyle(nav).backgroundColor : null;

    // Footer background
    const footer = document.querySelector('footer, .site-footer, .md-footer');
    const footerBg = footer ? getComputedStyle(footer).backgroundColor : null;

    // Logo presence
    const hasLogo = !!(document.querySelector('.nav-logo img, .md-logo img, nav img'));

    // Hero presence
    const hasHero = !!(document.querySelector('.st-hero, .hero, [class*="hero"]'));

    return { navLinks, footerHeadings, dropdownItems, h2s, cardCount, navBg, footerBg, hasLogo, hasHero };
  });
}

function rgb(str) {
  if (!str) return null;
  const m = str.match(/(\d+),\s*(\d+),\s*(\d+)/);
  if (!m) return null;
  return [parseInt(m[1]), parseInt(m[2]), parseInt(m[3])];
}

function colorDiff(a, b) {
  const ra = rgb(a), rb = rgb(b);
  if (!ra || !rb) return 999;
  return Math.max(Math.abs(ra[0]-rb[0]), Math.abs(ra[1]-rb[1]), Math.abs(ra[2]-rb[2]));
}

function assert(label, passed, detail) {
  const icon = passed ? '✓' : '✗';
  const line = `  ${icon} ${label}`;
  if (!passed && detail) return { line: line + `\n      → ${detail}`, passed };
  return { line, passed };
}

async function testPage(browser, pair) {
  const pageA = await browser.newPage();
  const pageB = await browser.newPage();
  await pageA.setViewport({ width: 1440, height: 900 });
  await pageB.setViewport({ width: 1440, height: 900 });

  let sA, sB;
  try {
    [sA, sB] = await Promise.all([
      extractStructure(pageA, SITE_A + pair.a),
      extractStructure(pageB, SITE_B + pair.b),
    ]);
  } finally {
    await pageA.close().catch(() => {});
    await pageB.close().catch(() => {});
  }

  const results = [];

  // Nav top-level link count
  const navA = sA.navLinks.slice(0, 10);
  const navB = sB.navLinks.slice(0, 10);
  results.push(assert(
    `Nav link count  (A:${navA.length} B:${navB.length})`,
    navA.length > 0 && Math.abs(navA.length - navB.length) <= 2,
    navA.length !== navB.length ? `A=[${navA.join(', ')}] B=[${navB.join(', ')}]` : null
  ));

  // Logo
  results.push(assert('Logo present', sA.hasLogo && sB.hasLogo,
    `A:${sA.hasLogo} B:${sB.hasLogo}`));

  // Hero (home page only)
  if (pair.slug === 'home') {
    results.push(assert('Hero section present', sA.hasHero && sB.hasHero,
      `A:${sA.hasHero} B:${sB.hasHero}`));
  }

  // H2 headings
  const h2A = sA.h2s.length, h2B = sB.h2s.length;
  results.push(assert(
    `H2 heading count  (A:${h2A} B:${h2B})`,
    h2A > 0 && Math.abs(h2A - h2B) <= 1,
    h2A !== h2B ? `A=[${sA.h2s.join(' | ')}] B=[${sB.h2s.join(' | ')}]` : null
  ));

  // Card count
  results.push(assert(
    `Card count  (A:${sA.cardCount} B:${sB.cardCount})`,
    Math.abs(sA.cardCount - sB.cardCount) <= 1,
    sA.cardCount !== sB.cardCount ? `A:${sA.cardCount} B:${sB.cardCount}` : null
  ));

  // Footer columns
  const fhA = sA.footerHeadings.length, fhB = sB.footerHeadings.length;
  results.push(assert(
    `Footer columns  (A:${fhA} B:${fhB})`,
    fhA > 0 && fhA === fhB,
    fhA !== fhB ? `A=[${sA.footerHeadings.join(', ')}] B=[${sB.footerHeadings.join(', ')}]` : null
  ));

  // Nav background color — should both be light (not dark navy)
  const navDiff = colorDiff(sA.navBg, sB.navBg);
  results.push(assert(
    `Nav background matches  (diff:${navDiff})`,
    navDiff < 30,
    `A:${sA.navBg} B:${sB.navBg}`
  ));

  // Footer background — both should be dark navy
  const footDiff = colorDiff(sA.footerBg, sB.footerBg);
  results.push(assert(
    `Footer background matches  (diff:${footDiff})`,
    footDiff < 30,
    `A:${sA.footerBg} B:${sB.footerBg}`
  ));

  return results;
}

async function run() {
  const port = nextPort();
  const proc = spawn(CHROME, [
    '--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage',
    '--disable-gpu', '--headless', `--remote-debugging-port=${port}`,
    '--window-size=1440,900', '--no-first-run', '--disable-extensions', 'about:blank',
  ], {
    env: { ...process.env, LD_LIBRARY_PATH: LIBPATH, FONTCONFIG_FILE: '/tmp/fonts/fonts.conf', FONTCONFIG_PATH: '/tmp/fonts' },
    stdio: 'pipe',
  });

  let failures = 0;
  let passes = 0;

  try {
    await waitForPort(port, 40);
    const browser = await puppeteer.connect({
      browserURL: `http://localhost:${port}`,
      defaultViewport: { width: 1440, height: 900 },
    });

    for (const pair of PAGE_PAIRS) {
      console.log(`\n── ${pair.slug.toUpperCase()} (A:${pair.a}  B:${pair.b})`);
      const results = await testPage(browser, pair);
      for (const r of results) {
        console.log(r.line);
        if (r.passed) passes++; else failures++;
      }
      await new Promise(r => setTimeout(r, 400));
    }

    await browser.disconnect();
  } finally {
    proc.kill('SIGTERM');
  }

  const total = passes + failures;
  console.log(`\n══════════════════════════════════════`);
  console.log(`Results: ${passes}/${total} passed  ${failures > 0 ? `(${failures} FAILED)` : '✓ ALL PASS'}`);
  if (failures > 0) process.exit(1);
}

run().catch(e => { console.error(e); process.exit(1); });
