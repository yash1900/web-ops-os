// Web-Ops OS headless production smoke.
// Loads each site in a real Chrome at 375 / 768 / 1440 px and reports what a visitor hits:
// horizontal overflow, uncaught exceptions, CSP blocks, failed same-origin requests,
// rendered <h1> / <img alt>, and broken internal links found in the rendered DOM.
//
//   node site_smoke.js --site isaan-tea=https://isaantea.com [--site ...]
//
// Prints one JSON line on stdout as the last line: {"results":[...]} or {"skipped":"why"}.
// Exit 1 = a FAIL row, 3 = could not run (no puppeteer-core or no Chrome).
// Uses system Chrome (CHROME_PATH, or the usual install paths) — no browser download.

const fs = require('fs');

const VIEWPORTS = [
  { name: 'mobile', width: 375, height: 812, isMobile: true, hasTouch: true },
  { name: 'tablet', width: 768, height: 1024, isMobile: true, hasTouch: true },
  { name: 'desktop', width: 1440, height: 900 },
];
const MAX_LINKS = 40;
const NAV_TIMEOUT = 45000;

function emit(obj, code) {
  process.stdout.write('\n' + JSON.stringify(obj) + '\n');
  process.exit(code);
}

let puppeteer;
try {
  puppeteer = require('puppeteer-core');
} catch (e) {
  emit({ skipped: 'puppeteer-core not installed (run npm ci in web-ops-os/browser)' }, 3);
}

function chromePath() {
  const candidates = [
    process.env.CHROME_PATH,
    'C:/Program Files/Google/Chrome/Application/chrome.exe',
    'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
    '/usr/bin/google-chrome',
    '/usr/bin/google-chrome-stable',
    '/usr/bin/chromium-browser',
    '/usr/bin/chromium',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  ];
  return candidates.find((p) => p && fs.existsSync(p));
}

function parseSites(argv) {
  const sites = [];
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--site' && argv[i + 1]) {
      const [id, ...rest] = argv[++i].split('=');
      sites.push({ id, url: rest.join('=') });
    }
  }
  return sites;
}

const row = (site, check, level, detail) => ({ site_id: site, check, level, detail });
const bareHost = (u) => { try { return new URL(u).hostname.replace(/^www\./, ''); } catch { return ''; } };

async function visit(browser, site, vp) {
  const page = await browser.newPage();
  const host = bareHost(site.url);
  const pageErrors = [], cspBlocks = [], consoleErrors = [], badSameOrigin = [], badThirdParty = [];

  page.on('pageerror', (e) => pageErrors.push(String(e.message || e).slice(0, 160)));
  page.on('console', (m) => {
    if (m.type() !== 'error') return;
    const t = m.text();
    if (/Content Security Policy|Refused to (load|connect|execute|apply)/i.test(t)) cspBlocks.push(t.slice(0, 200));
    else consoleErrors.push(t.slice(0, 160));
  });
  page.on('response', (res) => {
    if (res.status() < 400) return;
    const entry = `${res.status()} ${res.url().slice(0, 140)}`;
    // Chrome asks every page for /favicon.ico on its own; a missing one is cosmetic.
    if (new URL(res.url()).pathname === '/favicon.ico') return badThirdParty.push(`no favicon: ${entry}`);
    (bareHost(res.url()) === host ? badSameOrigin : badThirdParty).push(entry);
  });
  page.on('requestfailed', (req) => {
    const why = (req.failure() && req.failure().errorText) || 'failed';
    if (/ERR_ABORTED|ERR_BLOCKED_BY_CLIENT/.test(why)) return; // cancelled prefetch/media, not a fault
    const entry = `${why} ${req.url().slice(0, 140)}`;
    (bareHost(req.url()) === host ? badSameOrigin : badThirdParty).push(entry);
  });

  await page.setViewport({ width: vp.width, height: vp.height, isMobile: !!vp.isMobile, hasTouch: !!vp.hasTouch });
  const out = [];
  const label = (c) => `${c}@${vp.name}`;
  let status = 0, idle = true;
  try {
    const res = await page.goto(site.url, { waitUntil: 'networkidle2', timeout: NAV_TIMEOUT });
    status = res ? res.status() : 0;
  } catch (e) {
    idle = false;
    if (!/timeout/i.test(String(e.message))) {
      await page.close();
      return { rows: [row(site.id, label('load'), 'FAIL', String(e.message).slice(0, 200))], links: [] };
    }
  }
  await new Promise((r) => setTimeout(r, 1500)); // let entrance animations settle

  const dom = await page.evaluate(() => {
    const de = document.documentElement;
    const vw = de.clientWidth;
    const overflow = Math.max(de.scrollWidth, document.body ? document.body.scrollWidth : 0) - vw;
    const offenders = [];
    if (overflow > 1) {
      for (const el of document.querySelectorAll('body *')) {
        const r = el.getBoundingClientRect();
        if (r.width && r.right > vw + 1) {
          offenders.push(`${el.tagName.toLowerCase()}${el.id ? '#' + el.id : ''}${typeof el.className === 'string' && el.className ? '.' + el.className.trim().split(/\s+/).slice(0, 2).join('.') : ''} (right ${Math.round(r.right)}px)`);
          if (offenders.length >= 3) break;
        }
      }
    }
    return {
      overflow,
      offenders,
      h1: document.querySelectorAll('h1').length,
      noAlt: [...document.querySelectorAll('img')].filter((i) => !i.hasAttribute('alt')).map((i) => (i.currentSrc || i.src || '').slice(-60)),
      links: [...document.querySelectorAll('a[href]')].map((a) => a.href),
      textLen: (document.body && document.body.innerText || '').trim().length,
    };
  });

  if (status && status >= 400) out.push(row(site.id, label('load'), 'FAIL', `HTTP ${status}`));
  if (!idle) out.push(row(site.id, label('network-idle'), 'WARN', `network still busy after ${NAV_TIMEOUT / 1000}s`));
  out.push(row(site.id, label('content'), dom.textLen > 50 ? 'PASS' : 'FAIL', `${dom.textLen} chars of visible text`));
  // A few px over makes phones zoom out ~1% (barely visible); more than 8px is a real sideways scroll.
  out.push(row(site.id, label('overflow'), dom.overflow > 8 ? 'FAIL' : dom.overflow > 1 ? 'WARN' : 'PASS',
    dom.overflow > 1 ? `page is ${dom.overflow}px wider than the screen; ${dom.offenders.join(', ') || 'offender not found'}` : 'no horizontal scroll'));
  out.push(row(site.id, label('js-exceptions'), pageErrors.length ? 'FAIL' : 'PASS', pageErrors.slice(0, 3).join(' | ') || 'none'));
  out.push(row(site.id, label('csp-blocks'), cspBlocks.length ? 'FAIL' : 'PASS', cspBlocks.slice(0, 2).join(' | ') || 'none'));
  out.push(row(site.id, label('same-origin-requests'), badSameOrigin.length ? 'FAIL' : 'PASS', badSameOrigin.slice(0, 4).join(' | ') || 'none failed'));
  if (badThirdParty.length) out.push(row(site.id, label('third-party-requests'), 'WARN', badThirdParty.slice(0, 4).join(' | ')));
  if (consoleErrors.length) out.push(row(site.id, label('console-errors'), 'WARN', consoleErrors.slice(0, 3).join(' | ')));
  if (vp.name === 'desktop') {
    out.push(row(site.id, 'rendered-h1', dom.h1 >= 1 ? 'PASS' : 'WARN', `${dom.h1} <h1> in rendered page`));
    out.push(row(site.id, 'rendered-img-alt', dom.noAlt.length ? 'WARN' : 'PASS',
      dom.noAlt.length ? `${dom.noAlt.length} <img> without alt: ${dom.noAlt.slice(0, 3).join(', ')}` : 'every <img> has alt'));
  }
  await page.close();
  return { rows: out, links: vp.name === 'desktop' ? dom.links : [] };
}

async function checkLinks(site, hrefs) {
  const host = bareHost(site.url);
  const urls = [...new Set(hrefs.map((h) => h.split('#')[0]).filter((h) => /^https?:/.test(h) && bareHost(h) === host))];
  const step = Math.max(1, Math.ceil(urls.length / MAX_LINKS));
  const sample = urls.filter((_, i) => i % step === 0).slice(0, MAX_LINKS);
  const broken = [];
  for (const u of sample) {
    try {
      const r = await fetch(u, { redirect: 'follow', headers: { 'User-Agent': 'Mozilla/5.0 (Web-Ops OS site smoke)' }, signal: AbortSignal.timeout(20000) });
      if (r.status >= 400) broken.push(`${u} -> ${r.status}`);
    } catch (e) {
      broken.push(`${u} -> ${e.name}`);
    }
  }
  const detail = `${sample.length} checked of ${urls.length} rendered internal links`;
  return row(site.id, 'links-rendered', broken.length ? 'FAIL' : 'PASS', broken.length ? `${broken.length} broken of ${detail}: ${broken.slice(0, 5).join('; ')}` : detail);
}

(async () => {
  const sites = parseSites(process.argv.slice(2));
  if (!sites.length) emit({ skipped: 'no --site id=url given' }, 3);
  const exe = chromePath();
  if (!exe) emit({ skipped: 'no Chrome found (set CHROME_PATH)' }, 3);

  let browser;
  try {
    browser = await puppeteer.launch({ executablePath: exe, headless: true, args: ['--no-sandbox', '--disable-dev-shm-usage'] });
  } catch (e) {
    emit({ skipped: `Chrome failed to start: ${String(e.message).slice(0, 200)}` }, 3);
  }

  const results = [];
  for (const site of sites) {
    let links = [];
    for (const vp of VIEWPORTS) {
      try {
        const v = await visit(browser, site, vp);
        results.push(...v.rows);
        links = links.concat(v.links);
      } catch (e) {
        results.push(row(site.id, `visit@${vp.name}`, 'FAIL', String(e.message).slice(0, 200)));
      }
    }
    if (links.length) results.push(await checkLinks(site, links));
  }
  await browser.close();
  emit({ results }, results.some((r) => r.level === 'FAIL') ? 1 : 0);
})().catch((e) => emit({ skipped: `smoke crashed: ${String(e.message).slice(0, 200)}` }, 3));
