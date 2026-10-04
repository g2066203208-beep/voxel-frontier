import queueRaw from '../research/wind-tower/references/download_queue.tsv?raw';
import manifestRaw from '../research/wind-tower/references/open-access/MANIFEST.tsv?raw';

type QueueItem = {
  id: string;
  batch: string;
  priority: string;
  title: string;
  authors: string;
  year: string;
  venue: string;
  doi: string;
  alternate_url: string;
  purpose: string;
  access_hint: string;
};

type DownloadStatus = 'todo' | 'opened' | 'downloaded' | 'failed';

type ProgressEntry = {
  status: DownloadStatus;
  fileName?: string;
  sha256?: string;
  size?: number;
  verifiedAt?: string;
  doiFound?: string;
};

type ProgressMap = Record<string, ProgressEntry>;

const STORAGE_KEY = 'paper-studio.literature-download.v1';

const esc = (text: unknown) => String(text ?? '').replace(/[&<>"']/g, c => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
}[c]!));

function parseTsv(raw: string): Record<string, string>[] {
  const lines = raw.trim().split(/\r?\n/).filter(Boolean);
  if (!lines.length) return [];
  const headers = lines[0].split('\t');
  return lines.slice(1).map(line => {
    const cols = line.split('\t');
    const out: Record<string, string> = {};
    headers.forEach((h, i) => out[h] = cols[i] ?? '');
    return out;
  });
}

export const queue = parseTsv(queueRaw) as unknown as QueueItem[];

function manifestStats() {
  const rows = parseTsv(manifestRaw);
  const ok = rows.filter(r => r.status === 'ok').length;
  const notPdf = rows.filter(r => r.status === 'not-pdf').length;
  const failed = rows.filter(r => r.status === 'download-failed').length;
  return { total: rows.length, ok, notPdf, failed };
}

function loadProgress(): ProgressMap {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}') as ProgressMap;
  } catch {
    return {};
  }
}

function saveProgress(progress: ProgressMap) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(progress));
}

function doiUrl(doi: string) {
  return doi ? `https://doi.org/${encodeURIComponent(doi)}` : '';
}

function statusText(s: DownloadStatus) {
  return s === 'downloaded' ? '已下载' : s === 'opened' ? '已打开' : s === 'failed' ? '下载失败' : '待下载';
}

function fmtBytes(n = 0) {
  if (!n) return '';
  const u = ['B', 'KB', 'MB', 'GB'];
  let x = n;
  let i = 0;
  while (x >= 1024 && i < u.length - 1) { x /= 1024; i++; }
  return `${x.toFixed(i ? 1 : 0)} ${u[i]}`;
}

function normalizeDoi(raw: string) {
  return raw.trim().replace(/^https?:\/\/(?:dx\.)?doi\.org\//i, '').replace(/[),.;\]}]+$/g, '').toLowerCase();
}

function extractDoi(bytes: Uint8Array) {
  const chunk = bytes.subarray(0, Math.min(bytes.length, 6 * 1024 * 1024));
  const text = new TextDecoder('latin1').decode(chunk);
  const matches = text.match(/10\.\d{4,9}\/[A-Z0-9._;()/:+-]+/ig) || [];
  for (const match of matches) {
    const clean = normalizeDoi(match);
    if (clean.includes('/')) return clean;
  }
  return '';
}

function filenameScore(name: string, item: QueueItem) {
  const hay = name.toLowerCase().replace(/[^a-z0-9\u4e00-\u9fff]+/g, ' ');
  const words = item.title.toLowerCase().replace(/[^a-z0-9\u4e00-\u9fff]+/g, ' ')
    .split(/\s+/).filter(w => w.length >= 5).slice(0, 12);
  if (!words.length) return 0;
  return words.filter(w => hay.includes(w)).length / words.length;
}

async function hashFile(file: File) {
  const buffer = await file.arrayBuffer();
  const digest = await crypto.subtle.digest('SHA-256', buffer);
  return Array.from(new Uint8Array(digest)).map(b => b.toString(16).padStart(2, '0')).join('');
}

async function inspectFile(file: File) {
  const buffer = await file.arrayBuffer();
  const bytes = new Uint8Array(buffer);
  const header = new TextDecoder('ascii').decode(bytes.subarray(0, 5));
  if (header !== '%PDF-') throw new Error('不是有效PDF文件');
  const digest = await crypto.subtle.digest('SHA-256', buffer);
  const sha256 = Array.from(new Uint8Array(digest)).map(b => b.toString(16).padStart(2, '0')).join('');
  const doiFound = extractDoi(bytes);
  return { sha256, doiFound };
}

function exportText(name: string, text: string) {
  const blob = new Blob([text], { type: 'text/tab-separated-values;charset=utf-8' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 500);
}

function toStatusTsv(progress: ProgressMap) {
  const rows = [['id','batch','priority','status','title','doi','file_name','sha256','size_bytes','verified_at']];
  for (const item of queue) {
    const p = progress[item.id] || { status: 'todo' as DownloadStatus };
    rows.push([
      item.id, item.batch, item.priority, p.status, item.title, item.doi,
      p.fileName || '', p.sha256 || '', String(p.size || ''), p.verifiedAt || ''
    ]);
  }
  return rows.map(r => r.map(v => String(v).replaceAll('\t', ' ')).join('\t')).join('\n') + '\n';
}

export function literaturePage() {
  const stats = manifestStats();
  return `
  <div class="literature-shell">
    <section class="literature-hero">
      <div>
        <div class="eyebrow">LITERATURE ACQUISITION</div>
        <h1>文献下载助手</h1>
        <p>登录学校 CARSI 一次后，从这里按优先级逐篇打开出版社页面。下载后的 PDF 在浏览器本地核验，不上传学校账号、Cookie 或密码。</p>
      </div>
      <div class="literature-hero-stats">
        <div><strong>${queue.length}</strong><span>人工下载队列</span></div>
        <div><strong>${stats.ok}</strong><span>GitHub已缓存PDF</span></div>
        <div><strong>${stats.failed + stats.notPdf}</strong><span>自动下载未成功</span></div>
      </div>
    </section>

    <section class="literature-security">
      <strong>认证边界</strong>
      <span>本页不会读取、保存或提交武汉理工账号、密码、CARSI Cookie、ScienceDirect Cookie 或 GitHub Token。</span>
      <a href="https://carsi.whut.edu.cn/" target="_blank" rel="noopener">打开武汉理工 CARSI</a>
    </section>

    <section class="literature-toolbar">
      <div class="literature-actions">
        <button class="button primary" data-lit="open-next">打开下一篇</button>
        <button class="button" data-lit="pick-folder">扫描下载目录</button>
        <label class="button file-button">导入PDF<input id="literature-file-input" type="file" accept="application/pdf,.pdf" multiple></label>
        <button class="button" data-lit="export">导出下载状态</button>
      </div>
      <div class="literature-filters">
        <label>批次<select id="lit-batch"><option value="all">全部</option><option>A</option><option>B</option><option>C</option><option>D</option></select></label>
        <label>状态<select id="lit-status"><option value="all">全部</option><option value="todo">待下载</option><option value="opened">已打开</option><option value="downloaded">已下载</option><option value="failed">下载失败</option></select></label>
        <input id="lit-search" placeholder="搜索题名、DOI、期刊、用途…" />
      </div>
    </section>

    <section class="literature-progress-panel">
      <div><span>本机进度</span><strong id="lit-progress-text">—</strong></div>
      <div class="lit-progress-track"><i id="lit-progress-bar"></i></div>
      <button class="text-button" data-lit="reset">重置本机状态</button>
    </section>

    <section id="literature-drop-zone" class="literature-drop-zone" tabindex="0">
      <strong>把已下载 PDF 拖到这里</strong>
      <span>自动检查 %PDF、计算 SHA-256，并优先用 DOI 元数据匹配队列。匹配不确定时不会乱标。</span>
    </section>

    <section id="literature-queue" class="literature-queue"></section>
  </div>`;
}

export function mountLiterature(root: HTMLElement): () => void {
  const progress = loadProgress();
  let batch = 'all';
  let status = 'all';
  let search = '';
  const queueEl = root.querySelector<HTMLElement>('#literature-queue')!;
  const dropZone = root.querySelector<HTMLElement>('#literature-drop-zone')!;
  const fileInput = root.querySelector<HTMLInputElement>('#literature-file-input')!;

  const persist = () => {
    saveProgress(progress);
    render();
  };

  function visibleItems() {
    const q = search.toLowerCase().trim();
    return queue.filter(item => {
      const p = progress[item.id]?.status || 'todo';
      if (batch !== 'all' && item.batch !== batch) return false;
      if (status !== 'all' && p !== status) return false;
      if (!q) return true;
      return `${item.title} ${item.authors} ${item.venue} ${item.doi} ${item.purpose}`.toLowerCase().includes(q);
    });
  }

  function render() {
    const done = queue.filter(x => progress[x.id]?.status === 'downloaded').length;
    const opened = queue.filter(x => progress[x.id]?.status === 'opened').length;
    const failed = queue.filter(x => progress[x.id]?.status === 'failed').length;
    root.querySelector('#lit-progress-text')!.textContent = `${done}/${queue.length} 已下载 · ${opened} 已打开 · ${failed} 失败`;
    (root.querySelector<HTMLElement>('#lit-progress-bar')!).style.width = `${Math.round(done / queue.length * 100)}%`;

    const items = visibleItems();
    queueEl.innerHTML = items.length ? items.map(item => {
      const p = progress[item.id] || { status: 'todo' as DownloadStatus };
      const url = item.doi ? doiUrl(item.doi) : item.alternate_url;
      return `<article class="literature-card ${p.status}" data-lit-id="${esc(item.id)}">
        <div class="literature-card-head">
          <div><span class="lit-batch">批次 ${esc(item.batch)}</span><span class="lit-priority">${esc(item.priority)}</span><span class="lit-status ${p.status}">${statusText(p.status)}</span></div>
          <strong>${esc(item.id)}</strong>
        </div>
        <h2>${esc(item.title)}</h2>
        <p class="lit-meta">${esc(item.authors)} · ${esc(item.year)} · ${esc(item.venue)}</p>
        ${item.doi ? `<p class="lit-doi">DOI <code>${esc(item.doi)}</code></p>` : ''}
        <div class="lit-purpose"><b>为什么要下</b><span>${esc(item.purpose)}</span></div>
        <div class="lit-purpose"><b>访问方式</b><span>${esc(item.access_hint)}</span></div>
        ${p.fileName ? `<div class="lit-file"><b>本地PDF</b><span>${esc(p.fileName)} · ${fmtBytes(p.size)}</span><code>SHA-256 ${esc(p.sha256 || '')}</code></div>` : ''}
        <div class="literature-card-actions">
          ${url ? `<a class="button primary" href="${esc(url)}" target="_blank" rel="noopener" data-lit-open="${esc(item.id)}">打开正式入口</a>` : ''}
          ${item.alternate_url && item.doi ? `<a class="button" href="${esc(item.alternate_url)}" target="_blank" rel="noopener">备用入口</a>` : ''}
          ${item.doi ? `<button class="button" data-lit-copy="${esc(item.doi)}">复制DOI</button>` : ''}
          <label class="button file-button">关联PDF<input type="file" accept="application/pdf,.pdf" data-lit-file="${esc(item.id)}"></label>
          <button class="button quiet" data-lit-failed="${esc(item.id)}">标记失败</button>
        </div>
      </article>`;
    }).join('') : '<div class="empty-state"><h3>当前筛选没有文献</h3><p>切换批次、状态或清空搜索。</p></div>';

    queueEl.querySelectorAll<HTMLAnchorElement>('[data-lit-open]').forEach(a => {
      a.addEventListener('click', () => {
        const id = a.dataset.litOpen!;
        if (progress[id]?.status !== 'downloaded') progress[id] = { ...(progress[id] || {}), status: 'opened' };
        saveProgress(progress);
        setTimeout(render, 50);
      });
    });
    queueEl.querySelectorAll<HTMLButtonElement>('[data-lit-copy]').forEach(btn => btn.addEventListener('click', async () => {
      await navigator.clipboard.writeText(btn.dataset.litCopy || '');
      btn.textContent = '已复制';
      setTimeout(() => btn.textContent = '复制DOI', 1000);
    }));
    queueEl.querySelectorAll<HTMLInputElement>('[data-lit-file]').forEach(input => input.addEventListener('change', async () => {
      const file = input.files?.[0];
      if (file) await attachExact(input.dataset.litFile!, file);
      input.value = '';
    }));
    queueEl.querySelectorAll<HTMLButtonElement>('[data-lit-failed]').forEach(btn => btn.addEventListener('click', () => {
      progress[btn.dataset.litFailed!] = { ...(progress[btn.dataset.litFailed!] || {}), status: 'failed' };
      persist();
    }));
  }

  async function attachExact(id: string, file: File) {
    try {
      const inspected = await inspectFile(file);
      progress[id] = {
        status: 'downloaded',
        fileName: file.name,
        sha256: inspected.sha256,
        size: file.size,
        verifiedAt: new Date().toISOString(),
        doiFound: inspected.doiFound
      };
      persist();
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    }
  }

  async function attachAuto(file: File) {
    try {
      const inspected = await inspectFile(file);
      let match: QueueItem | undefined;
      if (inspected.doiFound) {
        match = queue.find(q => normalizeDoi(q.doi) === inspected.doiFound);
      }
      if (!match) {
        const candidates = queue
          .filter(q => progress[q.id]?.status !== 'downloaded')
          .map(q => ({ q, score: filenameScore(file.name, q) }))
          .sort((a, b) => b.score - a.score);
        if (candidates[0]?.score >= 0.34 && candidates[0].score > (candidates[1]?.score || 0) + 0.08) match = candidates[0].q;
      }
      if (!match) return false;
      progress[match.id] = {
        status: 'downloaded',
        fileName: file.name,
        sha256: inspected.sha256,
        size: file.size,
        verifiedAt: new Date().toISOString(),
        doiFound: inspected.doiFound
      };
      return true;
    } catch {
      return false;
    }
  }

  async function handleFiles(files: File[]) {
    let matched = 0;
    for (const file of files.filter(f => f.name.toLowerCase().endsWith('.pdf'))) {
      if (await attachAuto(file)) matched++;
    }
    saveProgress(progress);
    render();
    alert(`扫描完成：${files.length} 个文件中自动匹配 ${matched} 篇。未匹配PDF请用对应卡片的“关联PDF”。`);
  }

  root.querySelector<HTMLSelectElement>('#lit-batch')!.addEventListener('change', e => { batch = (e.target as HTMLSelectElement).value; render(); });
  root.querySelector<HTMLSelectElement>('#lit-status')!.addEventListener('change', e => { status = (e.target as HTMLSelectElement).value; render(); });
  root.querySelector<HTMLInputElement>('#lit-search')!.addEventListener('input', e => { search = (e.target as HTMLInputElement).value; render(); });

  root.querySelector('[data-lit="open-next"]')!.addEventListener('click', () => {
    const item = queue.find(q => (progress[q.id]?.status || 'todo') === 'todo');
    if (!item) return alert('下载队列已经全部处理。');
    const url = item.doi ? doiUrl(item.doi) : item.alternate_url;
    if (!url) return alert('这篇没有可直接打开的入口。');
    progress[item.id] = { ...(progress[item.id] || {}), status: 'opened' };
    saveProgress(progress);
    render();
    window.open(url, '_blank', 'noopener');
  });

  root.querySelector('[data-lit="export"]')!.addEventListener('click', () => {
    exportText(`literature-download-status-${new Date().toISOString().slice(0,10)}.tsv`, toStatusTsv(progress));
  });

  root.querySelector('[data-lit="reset"]')!.addEventListener('click', () => {
    if (!confirm('只会清除这个浏览器里的下载进度，不会删除PDF。确定重置吗？')) return;
    Object.keys(progress).forEach(k => delete progress[k]);
    persist();
  });

  fileInput.addEventListener('change', async () => {
    await handleFiles(Array.from(fileInput.files || []));
    fileInput.value = '';
  });

  root.querySelector('[data-lit="pick-folder"]')!.addEventListener('click', async () => {
    const picker = (window as unknown as { showDirectoryPicker?: () => Promise<any> }).showDirectoryPicker;
    if (!picker) {
      alert('当前浏览器不支持目录扫描。请使用最新版 Edge/Chrome，或直接拖入PDF。');
      return;
    }
    try {
      const dir = await picker();
      const files: File[] = [];
      for await (const [, handle] of dir.entries()) {
        if (handle.kind === 'file' && String(handle.name).toLowerCase().endsWith('.pdf')) {
          files.push(await handle.getFile());
        }
      }
      await handleFiles(files);
    } catch (e) {
      if ((e as DOMException)?.name !== 'AbortError') alert(`目录扫描失败：${e instanceof Error ? e.message : String(e)}`);
    }
  });

  ['dragenter','dragover'].forEach(type => dropZone.addEventListener(type, e => {
    e.preventDefault(); dropZone.classList.add('dragging');
  }));
  ['dragleave','drop'].forEach(type => dropZone.addEventListener(type, e => {
    e.preventDefault(); dropZone.classList.remove('dragging');
  }));
  dropZone.addEventListener('drop', async e => {
    const files = Array.from(e.dataTransfer?.files || []);
    await handleFiles(files);
  });

  render();
  return () => {};
}
