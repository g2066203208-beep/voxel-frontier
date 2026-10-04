(() => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const norm = s => String(s || '').replace(/\s+/g, ' ').trim().toLowerCase();

  function currentDoi() {
    const meta = document.querySelector('meta[name="dc.identifier"],meta[name="citation_doi"]');
    const m = document.body.innerText.match(/10\.1016\/j\.[a-z0-9.-]+\.\d+/i);
    const raw = (meta && meta.content) || (m && m[0]) || '';
    return raw.replace(/^doi:\s*/i, '').trim().toLowerCase();
  }

  function findPdfCandidate() {
    const anchors = Array.from(document.querySelectorAll('a[href]'));
    const scored = anchors.map(a => {
      const text = norm(a.innerText || a.getAttribute('aria-label') || a.title);
      const href = a.href || '';
      let score = 0;
      if (/\/pdfft(?:\?|$)/i.test(href)) score += 100;
      if (/download.*pdf|pdf.*download/i.test(text)) score += 80;
      if (/view pdf|查看pdf|查看 pdf|pdf/i.test(text)) score += 45;
      if (/\.pdf(?:\?|$)/i.test(href)) score += 70;
      if (/article\/pii\/.+\/pdfft/i.test(href)) score += 100;
      return { href: href, text: text, score: score };
    }).filter(x => x.score > 0).sort((a, b) => b.score - a.score);
    return scored[0] || null;
  }

  async function run() {
    await sleep(1800);
    const doi = currentDoi();
    const candidate = findPdfCandidate();
    chrome.runtime.sendMessage({
      type: 'PAGE_READY',
      doi: doi,
      title: document.title,
      url: location.href,
      pdfUrl: candidate ? candidate.href : '',
      pdfText: candidate ? candidate.text : ''
    });

    const res = await chrome.runtime.sendMessage({ type: 'GET_STATE' });
    if (!res || !res.state || !res.state.running) return;
    const item = (res.queue || []).find(x => x.id === res.state.currentId);
    if (!item) return;
    if (item.doi && doi && item.doi.toLowerCase() !== doi.toLowerCase()) return;

    if (candidate) {
      chrome.runtime.sendMessage({ type: 'PDF_CANDIDATE', doi: doi, url: candidate.href, text: candidate.text });
    } else {
      chrome.runtime.sendMessage({ type: 'PDF_NOT_FOUND', doi: doi, url: location.href });
    }
  }

  run();
})();
