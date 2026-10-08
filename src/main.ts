import './style.css';
import { researchPage, engineeringPage, mountEngineering } from './engineering';
import { icon } from './icons';
import { createRecord, createProject, createDemoWorkspace, loadWorkspace, saveWorkspace, validateWorkspace, exportMarkdown, parseBibtex, referencesToBibtex, type Workspace, type Project, type ResearchRecord, type RecordKind } from './store';
import { addAttachment, getAttachment, deleteAttachment, deleteProjectAttachments, exportAttachments, importAttachments, validateAttachmentBackups, readPreview, downloadBlob, type AttachmentBackup } from './files';

type View = 'overview' | 'manuscript' | RecordKind | 'search' | 'workflow' | 'engineering';
const modules: Record<RecordKind, { label: string; icon: string; note: string; fields: Record<string, string> }> = {
  reviews: { label: '论文审查', icon: 'check', note: '逐项追踪问题，让每次修订都有回应。', fields: { priority: '优先级', finding: '发现的问题 / 审查意见', action: '修改方案与回应' } },
  replications: { label: '论文复盘', icon: 'book', note: '拆解研究问题、方法和证据，沉淀可复用的思路。', fields: { question: '研究问题与核心假设', method: '研究方法与复现条件', result: '主要结果 / 复现记录', limitations: '局限性与启发' } },
  experiments: { label: '实验记录', icon: 'flask', note: '记录条件、过程与结果，保留完整的实验轨迹。', fields: { objective: '实验目的', materials: '材料、设备与实验条件', procedure: '实验过程', result: '结果、异常与后续计划' } },
  protocols: { label: '操作步骤', icon: 'steps', note: '把方法写成可执行的步骤，随时检查完成情况。', fields: { objective: '适用场景与目标', precautions: '注意事项与质量控制' } },
  models: { label: '建模与模型', icon: 'cube', note: '归档模型文件、参数与版本，让模型来龙去脉清晰可查。', fields: { software: '建模软件 / 方法', version: '模型版本', parameters: '参数与边界条件', notes: '假设、验证与变更记录' } },
  datasets: { label: '研究数据', icon: 'data', note: '整理数据来源、变量与处理记录，预览 CSV 数据表。', fields: { source: '数据来源与采集方式', variables: '变量说明 / 单位', notes: '清洗、转换与分析记录' } },
  references: { label: '参考文献', icon: 'quote', note: '集中整理引文信息、阅读笔记和文献附件。', fields: { authors: '作者', year: '年份', venue: '期刊 / 出版物', doi: 'DOI', url: '链接', key: 'BibTeX 引用键' } },
};
const statusLabels = { todo: '待开始', active: '进行中', done: '已完成' };
const WORKSPACE_STORAGE_KEY = 'paper-studio.workspace.v1';
let workspace: Workspace;
let recoveryError = '';
let recoveryRaw: string | null = null;
let saveState = '示例项目 · 尚未保存';
let restoring = false;
try {
  recoveryRaw = globalThis.localStorage.getItem(WORKSPACE_STORAGE_KEY);
  workspace = loadWorkspace();
  if (recoveryRaw !== null) saveState = '已保存到本机';
} catch (error) {
  workspace = createDemoWorkspace();
  recoveryError = error instanceof Error ? error.message : String(error);
  saveState = '原数据待恢复';
}
let view: View = globalThis.location.hash === '#engineering' ? 'engineering' : 'workflow';
let disposeEngineering: (()=>void) | undefined;
let renderGeneration = 0;
let query = '';
let statusFilter = 'all';
let manuscriptPreview = false;
let savingTimer: ReturnType<typeof setTimeout> | undefined;
const app = document.querySelector<HTMLDivElement>('#app')!;
const esc = (text: unknown) => String(text ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]!));
const project = (): Project => workspace.projects.find(p => p.id === workspace.activeProjectId)!;
const kindKeys = Object.keys(modules) as RecordKind[];
const dateText = (value: string) => value ? value.slice(0, 10).replaceAll('-', '.') : '未记录';
const countChars = (text: string) => text.replace(/\s/g, '').length;
const button = (action: string, text: string, ico = '', cls = 'button', extra = '') => `<button type="button" class="${cls}" data-action="${action}" ${extra}>${ico ? icon(ico, 17) : ''}<span>${text}</span></button>`;
function persist(message?: string): boolean {
  if (recoveryError || restoring) return false;
  const p = project();
  const previousUpdatedAt = p.updatedAt;
  p.updatedAt = new Date().toISOString();
  try {
    saveWorkspace(workspace);
    saveState = '已保存到本机';
    document.querySelector('#save-state')?.replaceChildren(document.createTextNode(saveState));
    if (message) toast(message);
    return true;
  } catch (e) {
    p.updatedAt = previousUpdatedAt;
    saveState = '保存失败 · 请导出备份';
    toast(`保存失败：${errorText(e)}。当前修改尚未保存，请先导出备份。`, true);
    document.querySelector('#save-state')?.replaceChildren(document.createTextNode(saveState));
    return false;
  }
}
const errorText = (e: unknown) => e instanceof Error ? e.message : String(e);
function toast(text: string, error = false) {
  const el = document.createElement('div'); el.className = `toast ${error ? 'error' : ''}`; el.setAttribute('role', error ? 'alert' : 'status'); el.textContent = text; document.body.append(el); setTimeout(() => el.remove(), error ? 7000 : 3500);
}
function navItem(key: View, label: string, ico: string, count?: number) {
  return `<button class="nav-item ${view === key ? 'selected' : ''}" data-view="${key}" ${view === key ? 'aria-current="page"' : ''}>${icon(ico)}<span>${label}</span>${count === undefined ? '' : `<small>${count}</small>`}</button>`;
}
function render() {
  disposeEngineering?.(); disposeEngineering = undefined;
  const generation = ++renderGeneration;
  if (recoveryError) { renderRecovery(); return; }
  const p = project();
  const cloud = view === 'workflow' || view === 'engineering';
  const title = view === 'workflow' ? '研究全过程 · GitHub' : view === 'engineering' ? 'Abaqus有限元模型 · 云端' : view === 'overview' ? '项目总览' : view === 'manuscript' ? '论文写作' : view === 'search' ? '搜索结果' : modules[view].label;
  app.innerHTML = `<aside class="sidebar"><a class="brand" href="#" data-view="overview"><span class="brand-mark">${icon('paper', 25)}</span><span>论文工作室<small>PAPER STUDIO</small></span></a><div class="project-select"><label for="project-selector">当前研究项目</label><select id="project-selector" ${cloud ? 'disabled' : ''}>${cloud ? `<option value="${p.id}">10 MW风机混合塔架研究</option>` : workspace.projects.map(x => `<option value="${x.id}" ${x.id === p.id ? 'selected' : ''}>${esc(x.name)}</option>`).join('')}</select>${button('new-project', '新建项目', 'plus', 'new-project')}</div><nav aria-label="工作台导航">${navItem('workflow', '研究全过程 · GitHub', 'steps')}${navItem('engineering', 'Abaqus有限元模型', 'cube')}<a class="nav-item" href="${import.meta.env.BASE_URL}iea15.html" title="IEA15官方OpenFAST参考模型三维视图">${icon('cube')}<span>IEA 15 MW三维模型</span></a>${navItem('overview', '草稿项目总览', 'grid')}<div class="nav-label">浏览器草稿区 · 不上传正文</div>${navItem('manuscript', '论文写作', 'paper')}${kindKeys.map(k => navItem(k, modules[k].label, modules[k].icon, p.records.filter(r => r.kind === k).length)).join('')}</nav><div class="sidebar-footer"><div class="local-note"><span class="status-dot"></span><span>${cloud ? 'GitHub正式研究区<small>流程、工程与成果由仓库管理</small>' : '浏览器草稿区<small>此处笔记不会上传GitHub</small>'}</span></div>${button('help', '使用与数据说明', 'help', 'help-button')}</div></aside><div class="workspace"><header class="topbar">${button('toggle-nav', '', 'menu', 'icon-button mobile-menu', 'aria-label="展开导航"')}<div class="breadcrumb">工作空间 <span>/</span> <strong>${title}</strong></div><label class="search-box">${icon('search', 17)}<input id="global-search" placeholder="搜索项目内的记录…" aria-label="搜索项目内的记录" value="${esc(query)}"/><kbd>⌘ K</kbd></label><span class="avatar" title="本地工作区">研</span></header><main id="main" tabindex="-1">${view === 'workflow' ? researchPage() : view === 'engineering' ? engineeringPage() : view === 'overview' ? overview() : view === 'manuscript' ? manuscript() : recordsPage()}</main><footer class="workspace-footer"><span><span class="status-dot"></span><span id="save-state">已保存到本机</span></span><span>Paper Studio · 专注研究的每一步</span></footer></div>`;
  bindMain();
  if (view === 'engineering') void mountEngineering(app).then(dispose => { if (generation !== renderGeneration) dispose(); else disposeEngineering = dispose; });
  document.querySelector('#save-state')!.textContent = cloud ? '来源：GitHub · main' : saveState;
}
function renderRecovery() {
  app.innerHTML = `<main class="recovery-panel"><section class="help-copy"><h1>恢复你的研究工作区</h1><p role="alert">无法读取本地资料：${esc(recoveryError)}</p><p>自动保存已暂停，不会用示例项目覆盖原资料。你可以先导出原始文本和附件，再导入完整工作区备份；如果浏览器禁用了存储，请允许此网站保存数据后重试。</p><div class="heading-actions">${button('export-raw', '导出原始文本', 'down', 'button', recoveryRaw === null ? 'disabled' : '')}${button('export-recovery-assets', '导出原始附件', 'down')}${button('retry-storage', '重试读取', '', 'button')}${button('import-backup', '恢复完整备份', 'up', 'button primary')}</div><p>原始文本用于保留损坏的数据，不能直接作为完整备份导入。原始附件导出独立保存二进制内容与关联信息。</p></section></main>`;
}
function pageHeading(eyebrow: string, title: string, note: string, actions = '') {
  return `<div class="page-heading"><div><div class="eyebrow">${eyebrow}</div><h1>${esc(title)}</h1><p>${esc(note)}</p></div><div class="heading-actions">${actions}</div></div>`;
}
function overview() {
  const p = project(); const done = p.records.filter(r => r.status === 'done').length; const total = p.records.length; const progress = total ? Math.round(done / total * 100) : 0;
  const pending = p.records.filter(r => r.status !== 'done').slice(0, 4);
  const recent = [...p.records].sort((a, b) => b.date.localeCompare(a.date)).slice(0, 5);
  return `${pageHeading('RESEARCH WORKSPACE', '研究，从这里继续。', '写作、实验与资料，在一个项目中有序连接。', button('import-backup', '导入备份', 'up') + button('export-backup', '导出备份', 'down'))}<section class="project-hero"><div class="hero-copy"><span class="hero-tag">当前项目 <span>·</span> 本地工作区</span><h2>${esc(p.name)}</h2><p>${esc(p.description || '为这个项目记录研究目标、方法和资料。')}</p><div class="hero-actions">${button('write', '继续写作', 'arrow', 'button primary')}${button('edit-project', '项目设置', '', 'button hero-secondary')}</div></div><div class="hero-art" aria-hidden="true"><div class="art-sheet back"><i></i><i></i><i></i></div><div class="art-sheet front"><span>RESEARCH NOTES</span><b>让思考<br/>留下轨迹。</b><i></i><i></i><div class="art-circle">${icon('flask', 26)}</div></div><div class="art-dot one"></div><div class="art-dot two"></div></div></section><section class="stats" aria-label="项目统计"><div class="stat">${icon('paper', 22)}<div><span>论文正文</span><strong>${countChars(p.manuscript).toLocaleString()}<small>字</small></strong></div><span class="stat-note">随时接续灵感</span></div><div class="stat">${icon('folder', 22)}<div><span>研究记录</span><strong>${total}<small>条</small></strong></div><span class="stat-note">覆盖 ${kindKeys.filter(k => p.records.some(r => r.kind === k)).length} 个研究模块</span></div><div class="stat">${icon('check', 22)}<div><span>记录完成度</span><strong>${progress}<small>%</small></strong></div><div class="stat-progress"><span style="width:${progress}%"></span></div></div></section><div class="dashboard-columns"><section class="panel recent-panel"><div class="panel-heading"><div><h2>最近的研究记录</h2><span>把散落的思考，整理成下一步</span></div>${button('new-record', '添加记录', 'plus', 'button small')}</div><div class="record-table"><div class="table-head"><span>记录名称</span><span>模块</span><span>状态</span><span>记录日期</span></div>${recent.length ? recent.map(r => `<button class="table-row" data-open="${r.id}"><span class="row-title"><span class="row-icon">${icon(modules[r.kind].icon, 19)}</span><span>${esc(r.title)}<small>${esc(r.summary.slice(0, 45))}</small></span></span><span class="table-module">${modules[r.kind].label}</span><span class="badge ${r.status}">${statusLabels[r.status]}</span><span class="table-date">${dateText(r.date)}</span></button>`).join('') : empty('还没有研究记录', '先添加一条实验、复盘或文献记录。')}</div></section><section class="panel pending-panel"><div class="panel-heading"><div><h2>待推进事项</h2><span>一次专注一件事</span></div><span class="number-badge">${p.records.filter(r => r.status !== 'done').length}</span></div>${pending.map(r => `<button class="pending-item" data-open="${r.id}"><span class="pending-circle ${r.status}"></span><span><strong>${esc(r.title)}</strong><small>${modules[r.kind].label} <span>·</span> ${statusLabels[r.status]}</small></span>${icon('arrow', 16)}</button>`).join('') || empty('当前记录已完成', '可以开始新一轮研究。')}<div class="quiet-note">${icon('clock', 16)}<span>每一步记录，都是下一次研究的起点。</span></div></section></div><section class="module-section"><div class="section-heading"><h2>进入研究工作区</h2><span>资料彼此关联，过程清晰可追溯</span></div><div class="module-grid">${kindKeys.map(k => `<button class="module-card" data-view="${k}"><span class="module-icon ${k}">${icon(modules[k].icon, 22)}</span><strong>${modules[k].label}</strong><small>${p.records.filter(r => r.kind === k).length} 条记录</small>${icon('arrow', 16)}</button>`).join('')}</div></section>`;
}
function empty(title: string, note: string) { return `<div class="empty-state">${icon('folder', 30)}<h3>${title}</h3><p>${note}</p></div>`; }
function markdown(text: string) {
  return text.split(/\n\s*\n/).map(block => {
    if (/^#{1,3}\s/.test(block)) return block.split('\n').map(line => { const m = line.match(/^(#{1,3})\s+(.*)$/); return m ? `<h${m[1].length}>${esc(m[2])}</h${m[1].length}>` : `<p>${esc(line)}</p>`; }).join('');
    if (block.startsWith('```')) return `<pre>${esc(block.replace(/^```[^\n]*\n?/, '').replace(/```$/, ''))}</pre>`;
    return `<p>${esc(block).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br/>')}</p>`;
  }).join('');
}
function manuscript() {
  const p = project(); const headings = p.manuscript.split('\n').filter(x => /^#{1,3} /.test(x));
  return `${pageHeading('MANUSCRIPT', '论文写作', '让提纲、草稿与研究材料一起成长。', button('export-manuscript', '导出 Markdown', 'down'))}<section class="writing-shell"><aside class="outline"><div class="outline-heading">文稿提纲 <span>${headings.length}</span></div>${headings.map((h, i) => `<button data-heading="${i}" class="outline-item level-${h.match(/^#+/)![0].length}">${esc(h.replace(/^#+ /, ''))}</button>`).join('') || '<p class="muted">用 # 或 ## 标记章节标题，提纲会显示在这里。</p>'}<div class="outline-tip">${icon('link', 17)}<p>审查意见、实验记录与文献，随时在左侧工作区查看。</p></div></aside><div class="writing-main"><div class="editor-toolbar"><div class="segmented"><button data-action="edit-mode" class="${!manuscriptPreview ? 'active' : ''}">编辑</button><button data-action="preview-mode" class="${manuscriptPreview ? 'active' : ''}">阅读预览</button></div><div class="format-actions">${button('insert-heading', 'H2', '', 'format-button', manuscriptPreview ? 'disabled' : '')}${button('insert-bold', 'B', '', 'format-button', manuscriptPreview ? 'disabled' : '')}${button('insert-ref', '引文', '', 'format-button', manuscriptPreview ? 'disabled' : '')}<span id="word-count">${countChars(p.manuscript).toLocaleString()} 字</span></div></div>${manuscriptPreview ? `<article class="manuscript-preview">${markdown(p.manuscript) || empty('开始你的第一段写作', '切换到编辑模式，写下研究问题。')}</article>` : `<textarea id="manuscript-editor" spellcheck="false" aria-label="论文 Markdown 正文" placeholder="# 论文标题\n\n## 摘要\n\n从这里开始写作…">${esc(p.manuscript)}</textarea>`}<div class="editor-footnote"><span>Markdown 正文 · 自动保存</span><span>文献引用可使用 [@引用键]</span></div></div></section>`;
}
function recordsPage() {
  const isSearch = view === 'search'; const kind = isSearch ? undefined : view as RecordKind;
  const title = isSearch ? `搜索“${query}”` : modules[kind!].label;
  const records = project().records.filter(r => (!kind || r.kind === kind) && (statusFilter === 'all' || r.status === statusFilter) && (!query || `${r.title} ${r.summary} ${r.tags.join(' ')} ${Object.values(r.fields).join(' ')}`.toLowerCase().includes(query.toLowerCase())));
  return `${pageHeading(isSearch ? 'SEARCH' : 'RESEARCH / ' + kind!.toUpperCase(), title, isSearch ? '搜索当前项目的标题、笔记、标签与详细字段。' : modules[kind!].note, (!isSearch && kind === 'references' ? button('import-bibtex', '导入 BibTeX', 'up') + button('export-bibtex', '导出 BibTeX', 'down') : '') + button('new-record', '添加记录', 'plus', 'button primary', kind ? `data-kind="${kind}"` : ''))}<div class="records-toolbar"><span>共 <strong>${records.length}</strong> 条记录</span><label>状态 <select id="status-filter"><option value="all">全部状态</option>${Object.entries(statusLabels).map(([k, v]) => `<option value="${k}" ${statusFilter === k ? 'selected' : ''}>${v}</option>`).join('')}</select></label></div><div class="records-grid">${records.map(r => `<button class="research-card" data-open="${r.id}"><div class="card-top"><span class="module-icon ${r.kind}">${icon(modules[r.kind].icon, 21)}</span><span class="badge ${r.status}">${statusLabels[r.status]}</span></div><h2>${esc(r.title)}</h2><p>${esc(r.summary || '添加摘要、笔记和附件，完善这条研究记录。')}</p><div class="tags">${r.tags.map(t => `<span>${esc(t)}</span>`).join('')}</div><div class="card-footer"><span>${isSearch ? modules[r.kind].label + ' · ' : ''}${dateText(r.date)}</span><span>${r.attachmentIds.length ? icon('folder', 14) + r.attachmentIds.length + ' 附件' : r.steps.length ? `${r.steps.filter(s => s.done).length}/${r.steps.length} 步骤` : '查看记录'} ${icon('arrow', 14)}</span></div></button>`).join('') || empty(query ? '没有找到匹配记录' : '开始积累这部分研究', query ? '试试其他关键词，或清空搜索。' : '点击“添加记录”，保存笔记、步骤和附件。')}</div>`;
}
function bindMain() {
  app.querySelector<HTMLSelectElement>('#project-selector')!.addEventListener('change', e => { if (savingTimer) clearTimeout(savingTimer); persist(); workspace.activeProjectId = (e.target as HTMLSelectElement).value; query = ''; persist(); render(); });
  app.querySelector<HTMLInputElement>('#global-search')!.addEventListener('input', e => { query = (e.target as HTMLInputElement).value; view = query ? 'search' : 'overview'; statusFilter = 'all'; const start = (e.target as HTMLInputElement).selectionStart; render(); const input = app.querySelector<HTMLInputElement>('#global-search')!; input.focus(); input.setSelectionRange(start, start); });
  app.querySelector<HTMLSelectElement>('#status-filter')?.addEventListener('change', e => { statusFilter = (e.target as HTMLSelectElement).value; render(); });
  app.querySelector<HTMLTextAreaElement>('#manuscript-editor')?.addEventListener('input', e => { project().manuscript = (e.target as HTMLTextAreaElement).value; document.querySelector('#save-state')!.textContent = '正在保存…'; document.querySelector('#word-count')!.textContent = `${countChars(project().manuscript).toLocaleString()} 字`; if (savingTimer) clearTimeout(savingTimer); savingTimer = setTimeout(() => persist(), 350); });
}
function openDialog(title: string, content: string, wide = false): HTMLDialogElement {
  document.querySelectorAll('dialog').forEach(el => el.close());
  const dialog = document.createElement('dialog'); dialog.className = `dialog ${wide ? 'wide' : ''}`; dialog.innerHTML = `<div class="dialog-heading"><h2>${esc(title)}</h2>${button('close-dialog', '', 'close', 'icon-button', 'aria-label="关闭窗口"')}</div>${content}`;
  document.body.append(dialog); dialog.addEventListener('close', () => { dialog.querySelectorAll<HTMLImageElement>('img[data-object-url]').forEach(img => URL.revokeObjectURL(img.src)); dialog.remove(); }); dialog.addEventListener('click', e => { if (e.target === dialog) dialog.close(); }); dialog.showModal(); return dialog;
}
function projectDialog(isNew: boolean) {
  const p = project(); const dialog = openDialog(isNew ? '开启一个新的研究项目' : '项目设置', `<form id="project-form" class="dialog-body"><label class="field">项目名称<input name="name" required maxlength="160" value="${isNew ? '' : esc(p.name)}" placeholder="例如：风机叶片结构优化研究"/></label><label class="field">项目说明<textarea name="description" rows="4" maxlength="4000" placeholder="研究目标、对象和主要方法">${isNew ? '' : esc(p.description)}</textarea></label><div class="form-actions">${!isNew ? button('delete-project', '删除项目', 'trash', 'button danger') : ''}<button class="button primary" type="submit">${isNew ? '创建项目' : '保存设置'}</button></div></form>`);
  dialog.querySelector('form')!.addEventListener('submit', e => {
    e.preventDefault();
    const data = new FormData(e.target as HTMLFormElement);
    const name = String(data.get('name')).trim();
    if (!name) return;
    const previous = structuredClone(workspace);
    if (isNew) {
      const next = createProject(name);
      next.description = String(data.get('description')).trim();
      workspace.projects.push(next);
      workspace.activeProjectId = next.id;
    } else {
      project().name = name;
      project().description = String(data.get('description')).trim();
    }
    if (!persist('项目已保存')) { workspace = previous; return; }
    if (isNew) { view = 'overview'; query = ''; }
    dialog.close(); render();
  });
}
async function recordDialog(id?: string, newKind?: RecordKind) {
  if (!id && !newKind) { const d = openDialog('选择记录类型', `<div class="dialog-body kind-picker">${kindKeys.map(k => button('choose-kind', modules[k].label, modules[k].icon, 'button', `data-kind="${k}"`)).join('')}</div>`); d.querySelectorAll<HTMLButtonElement>('[data-kind]').forEach(b => b.addEventListener('click', () => { d.close(); void recordDialog(undefined, b.dataset.kind as RecordKind); })); return; }
  const p = project(); const original = id ? p.records.find(r => r.id === id)! : undefined; const record = original ? structuredClone(original) : createRecord(newKind!); const spec = modules[record.kind];
  const d = openDialog(original ? spec.label + ' · 编辑记录' : '添加' + spec.label, `<form id="record-form" class="dialog-body"><div class="form-row"><label class="field grow">记录标题<input name="title" required maxlength="200" value="${esc(record.title)}"/></label><label class="field">状态<select name="status">${Object.entries(statusLabels).map(([k, v]) => `<option value="${k}" ${record.status === k ? 'selected' : ''}>${v}</option>`).join('')}</select></label></div><div class="form-row"><label class="field grow">标签（逗号分隔）<input name="tags" maxlength="1000" value="${esc(record.tags.join('，'))}" placeholder="方法，版本，研究主题"/></label><label class="field">记录日期<input type="date" name="date" required value="${esc(record.date.slice(0, 10))}"/></label></div><label class="field">摘要 / 阅读笔记<textarea name="summary" rows="3" maxlength="12000">${esc(record.summary)}</textarea></label><div class="record-fields">${Object.entries(spec.fields).map(([key, label]) => `<label class="field">${label}${['year', 'doi', 'url', 'key', 'version', 'software', 'priority', 'authors', 'venue'].includes(key) ? `<input name="field:${key}" maxlength="2000" value="${esc(record.fields[key] || '')}"/>` : `<textarea name="field:${key}" rows="3" maxlength="30000">${esc(record.fields[key] || '')}</textarea>`}</label>`).join('')}</div>${record.kind !== 'references' ? `<label class="field">操作清单（每行一步，可在下方勾选完成）<textarea name="steps" rows="5" maxlength="30000" placeholder="准备材料\n[x] 校准设备\n记录结果">${esc(record.steps.map(s => (s.done ? '[x] ' : '') + s.text).join('\n'))}</textarea></label><div id="step-checklist" class="step-checklist"></div>` : ''}<section class="attachment-section"><div class="section-heading"><h3>附件与原始文件</h3><label class="button small file-label">${icon('up', 16)}添加附件<input type="file" id="attachment-input" multiple/></label></div><p class="muted">支持文献、模型、图片与数据文件；单个文件最多 20 MB。CSV 可预览表格，模型文件可归档与下载。</p><div id="attachments-list"></div></section><div class="form-actions">${original ? button('delete-record', '删除记录', 'trash', 'button danger', `data-id="${record.id}"`) : ''}<button class="button primary" type="submit">保存记录</button></div></form>`, true);
  const stepsInput = d.querySelector<HTMLTextAreaElement>('textarea[name="steps"]');
  const renderSteps = () => {
    if (!stepsInput) return;
    const lines = stepsInput.value.split('\n').filter(s => s.trim());
    d.querySelector('#step-checklist')!.innerHTML = lines.map((s, i) => `<label class="step-checkbox"><input type="checkbox" data-step="${i}" ${/^\[x\]/i.test(s) ? 'checked' : ''}/><span>${esc(s.replace(/^\[x\]\s*/i, ''))}</span></label>`).join('');
  };
  stepsInput?.addEventListener('input', renderSteps);
  d.addEventListener('change', e => {
    const checkbox = (e.target as Element).closest<HTMLInputElement>('input[data-step]');
    if (!checkbox || !stepsInput) return;
    const lines = stepsInput.value.split('\n').filter(s => s.trim());
    const index = Number(checkbox.dataset.step);
    lines[index] = (checkbox.checked ? '[x] ' : '') + lines[index].replace(/^\[x\]\s*/i, '');
    stepsInput.value = lines.join('\n'); renderSteps();
  });
  renderSteps();
  const refreshAttachments = async () => {
    const assets = (await Promise.all(record.attachmentIds.map(getAttachment))).filter(a => a !== undefined);
    if (!d.isConnected) return;
    d.querySelector('#attachments-list')!.innerHTML = assets.map(a => `<div class="attachment-row"><span>${icon('paper', 18)}<strong>${esc(a!.name)}</strong><small>${(a!.size / 1024).toFixed(1)} KB</small></span><div>${button('preview-file', '预览', '', 'text-button', `data-id="${a!.id}"`)}${button('download-file', '下载', '', 'text-button', `data-id="${a!.id}"`)}${button('remove-file', '', 'trash', 'icon-button', `data-id="${a!.id}" aria-label="移除 ${esc(a!.name)}"`)}</div></div>`).join('') || '<div class="attachment-empty">尚未添加附件</div>';
  };
  await refreshAttachments();
  let saved = false;
  let closed = false;
  let uploadTask: Promise<void> | undefined;
  const submitButton = d.querySelector<HTMLButtonElement>('button[type="submit"]')!;
  d.querySelector<HTMLInputElement>('#attachment-input')!.addEventListener('change', e => {
    const input = e.target as HTMLInputElement;
    const files = Array.from(input.files || []);
    input.disabled = true; submitButton.disabled = true;
    uploadTask = (async () => {
      for (const file of files) {
        if (closed) break;
        const a = await addAttachment(p.id, record.id, file);
        record.attachmentIds.push(a.id);
      }
      if (!closed) { await refreshAttachments(); toast('附件已保存，请保存记录以完成关联'); }
    })().catch(err => { if (!closed) toast(errorText(err), true); }).finally(() => {
      uploadTask = undefined; input.disabled = false; input.value = ''; submitButton.disabled = false;
    });
  });
  d.addEventListener('click', async e => {
    const b = (e.target as Element).closest<HTMLButtonElement>('[data-action="remove-file"]'); if (!b) return;
    const assetId = b.dataset.id!;
    try {
      // Existing attachments remain intact until the edited record is successfully saved.
      if (!original?.attachmentIds.includes(assetId)) await deleteAttachment(assetId);
      record.attachmentIds = record.attachmentIds.filter(x => x !== assetId);
      await refreshAttachments();
    } catch (err) { toast(errorText(err), true); }
  });
  d.addEventListener('close', () => {
    closed = true;
    void (async () => {
      await uploadTask;
      if (!saved) { const previous = original?.attachmentIds || []; await Promise.all(record.attachmentIds.filter(x => !previous.includes(x)).map(deleteAttachment)); }
    })().catch(e => toast(errorText(e), true));
  });
  d.querySelector('form')!.addEventListener('submit', async e => {
    if (uploadTask) { e.preventDefault(); toast('附件正在保存，请稍候'); return; }
    e.preventDefault(); const data = new FormData(e.target as HTMLFormElement); record.title = String(data.get('title')).trim(); if (!record.title) return; record.summary = String(data.get('summary')); record.date = String(data.get('date')); record.status = data.get('status') as ResearchRecord['status']; record.tags = String(data.get('tags')).split(/[,，]/).map(x => x.trim()).filter(Boolean).slice(0, 20);
    for (const key of Object.keys(spec.fields)) record.fields[key] = String(data.get(`field:${key}`) || '');
    if (data.has('steps')) record.steps = String(data.get('steps')).split('\n').filter(x => x.trim()).map((s, i) => ({ id: record.steps[i]?.id || `${record.id}-step-${i}`, text: s.replace(/^\[x\]\s*/i, '').trim(), done: /^\[x\]/i.test(s) }));
    const previousRecords = p.records.slice();
    if (original) p.records[p.records.indexOf(original)] = record; else p.records.push(record);
    if (!persist('研究记录已保存')) { p.records = previousRecords; return; }
    saved = true; d.close(); render();
    try { await Promise.all((original?.attachmentIds || []).filter(id => !record.attachmentIds.includes(id)).map(deleteAttachment)); }
    catch (error) { toast(`记录已保存，但未清理的旧附件仍占用空间：${errorText(error)}`, true); }
  });
}
async function previewFile(id: string) {
  const a = await getAttachment(id); if (!a) throw new Error('找不到附件，请重新添加。'); const preview = await readPreview(a);
  const content = preview.kind === 'table' ? `<p class="muted">显示前 100 行、25 列。原文件保留全部内容。</p><div class="data-table-scroll"><table class="data-table">${preview.rows.map((row, i) => `<tr>${row.map(cell => `<${i ? 'td' : 'th'}>${esc(cell)}</${i ? 'td' : 'th'}>`).join('')}</tr>`).join('')}</table></div>` : preview.kind === 'image' ? `<img class="file-preview-image" data-object-url src="${esc(preview.url)}" alt="${esc(a.name)}"/>` : `<pre class="file-preview-text">${esc(preview.text)}</pre>`;
  const d = document.createElement('dialog'); d.className = 'dialog wide'; d.innerHTML = `<div class="dialog-heading"><h2>${esc(a.name)}</h2>${button('close-dialog', '', 'close', 'icon-button', 'aria-label="关闭预览"')}</div><div class="dialog-body">${content}</div>`; document.body.append(d); d.addEventListener('close', () => { if (preview.kind === 'image') URL.revokeObjectURL(preview.url); d.remove(); }); d.showModal();
}
function selectFile(accept: string, handler: (file: File) => Promise<void>) { const input = document.createElement('input'); input.type = 'file'; input.accept = accept; input.addEventListener('change', async () => { if (input.files?.[0]) { try { await handler(input.files[0]); } catch (e) { toast(errorText(e), true); } } }); input.click(); }
function downloadText(text: string, name: string, type = 'text/plain;charset=utf-8') { downloadBlob(new Blob([text], { type }), name); }
function restoreStoredText(storage: Storage, previous: string | null): void {
  if (previous === null) storage.removeItem(WORKSPACE_STORAGE_KEY);
  else storage.setItem(WORKSPACE_STORAGE_KEY, previous);
}
async function restoreBackup(file: File): Promise<void> {
  if (restoring) throw new Error('正在恢复另一份备份，请等待完成。');
  if (file.size > 300 * 1024 * 1024) throw new Error('备份文件过大。');
  const raw: unknown = JSON.parse(await file.text());
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) throw new Error('工作区备份需要一个对象。');
  const backup = raw as Record<string, unknown>;
  if (backup.format !== 'paper-studio-backup' || backup.version !== 1 || Object.keys(backup).some(key => !['format', 'version', 'workspace', 'attachments'].includes(key))) throw new Error('这不是受支持的论文工作室备份。');
  const next = validateWorkspace(backup.workspace);
  if (!Array.isArray(backup.attachments)) throw new Error('备份缺少附件列表。');
  const assetFields = ['id', 'projectId', 'recordId', 'name', 'type', 'size', 'createdAt', 'data'];
  for (const item of backup.attachments) {
    if (!item || typeof item !== 'object' || Array.isArray(item) || Object.keys(item).some(key => !assetFields.includes(key))) throw new Error('附件备份包含无效或未知的元数据字段。');
  }
  const allowedProjects = next.projects.map(p => p.id);
  const validatedAssets = validateAttachmentBackups(backup.attachments, allowedProjects);
  const expected = new Map<string, { projectId: string; recordId: string }>();
  for (const p of next.projects) for (const record of p.records) for (const id of record.attachmentIds) {
    if (expected.has(id)) throw new Error('同一个附件被多个研究记录引用。');
    expected.set(id, { projectId: p.id, recordId: record.id });
  }
  if (validatedAssets.length !== expected.size) throw new Error('备份存在未关联的附件，或缺少记录需要的附件。');
  for (const asset of validatedAssets) {
    const owner = expected.get(asset.id);
    if (!owner || owner.projectId !== asset.projectId || owner.recordId !== asset.recordId) throw new Error('备份附件与研究记录的所属关系不一致。');
  }
  if (!confirm('导入将替换当前工作区及附件。建议先导出当前资料，确定继续吗？')) return;
  const storage = globalThis.localStorage;
  const previous = storage.getItem(WORKSPACE_STORAGE_KEY);
  const serialized = JSON.stringify(next);
  // Probe the actual destination key, then restore it synchronously before touching IndexedDB.
  // A second temporary key would incorrectly require space for two full workspaces.
  storage.setItem(WORKSPACE_STORAGE_KEY, serialized);
  try { restoreStoredText(storage, previous); }
  catch (error) {
    recoveryRaw = previous;
    recoveryError = `预检后无法恢复原始文本：${errorText(error)}。请先导出原始文本。`;
    render();
    throw error;
  }
  if (savingTimer) { clearTimeout(savingTimer); savingTimer = undefined; }
  restoring = true;
  const progress = openDialog('正在恢复研究资料', '<div class="dialog-body"><p role="status">正在验证和写入附件，请等待完成。关闭此页面可能中断恢复。</p></div>');
  let textWritten = false;
  try {
    await importAttachments(backup.attachments as AttachmentBackup[], allowedProjects, () => {
      // This synchronous save runs inside the attachment transaction. A quota error aborts all its writes.
      saveWorkspace(next);
      textWritten = true;
    });
    workspace = next;
    recoveryError = '';
    recoveryRaw = serialized;
    saveState = '已保存到本机';
    view = 'overview'; query = ''; statusFilter = 'all'; manuscriptPreview = false;
  } catch (error) {
    if (textWritten) {
      try { restoreStoredText(storage, previous); }
      catch (rollbackError) {
        recoveryRaw = previous;
        recoveryError = `附件恢复已中止，但文本回滚失败：${errorText(rollbackError)}。请导出原始文本后重新恢复完整备份。`;
      }
    }
    throw error;
  } finally {
    restoring = false;
    progress.close();
    render();
  }
  toast('工作区与附件已恢复');
}
async function action(name: string, b: HTMLElement) {
  if (restoring) return;
  if (name === 'export-raw') { if (recoveryRaw === null) throw new Error('未能读取原始文本，请先允许本地存储后重试。'); downloadText(recoveryRaw, '论文工作室-原始存储.json', 'application/json'); return; }
  if (name === 'export-recovery-assets') { const attachments = await exportAttachments(); downloadText(JSON.stringify({ format: 'paper-studio-attachment-recovery', version: 1, attachments }, null, 2), '论文工作室-原始附件.json', 'application/json'); toast('原始附件及关联信息已导出'); return; }
  if (name === 'retry-storage') {
    try {
      recoveryRaw = globalThis.localStorage.getItem(WORKSPACE_STORAGE_KEY);
      workspace = loadWorkspace();
      recoveryError = '';
      saveState = recoveryRaw === null ? '示例项目 · 尚未保存' : '已保存到本机';
    } catch (error) { recoveryError = errorText(error); }
    render(); return;
  }
  if (recoveryError && name !== 'import-backup' && name !== 'close-dialog') throw new Error('工作区自动保存已暂停，请先恢复原数据或导入备份。');
  if (name === 'close-dialog') { b.closest('dialog')?.close(); return; }
  if (name === 'new-project' || name === 'edit-project') { projectDialog(name === 'new-project'); return; }
  if (name === 'new-record') { await recordDialog(undefined, b.dataset.kind as RecordKind | undefined); return; }
  if (name === 'write') { view = 'manuscript'; query = ''; render(); return; }
  if (name === 'toggle-nav') { app.classList.toggle('nav-open'); return; }
  if (name === 'edit-mode' || name === 'preview-mode') { manuscriptPreview = name === 'preview-mode'; persist(); render(); return; }
  if (name.startsWith('insert-')) { const editor = app.querySelector<HTMLTextAreaElement>('#manuscript-editor'); if (!editor) return; const text = name === 'insert-heading' ? '\n## 章节标题\n' : name === 'insert-bold' ? `**${editor.value.slice(editor.selectionStart, editor.selectionEnd) || '重点内容'}**` : '[@引用键]'; editor.setRangeText(text, editor.selectionStart, editor.selectionEnd, 'end'); editor.dispatchEvent(new Event('input')); editor.focus(); return; }
  if (name === 'export-manuscript') { downloadText(exportMarkdown(project()), `${project().name}.md`, 'text/markdown;charset=utf-8'); toast('论文与研究记录已导出'); return; }
  if (name === 'export-backup') {
    const snapshot = validateWorkspace(workspace);
    const byId = new Map((await exportAttachments()).map(asset => [asset.id, asset]));
    const attachments: AttachmentBackup[] = [];
    for (const p of snapshot.projects) for (const record of p.records) for (const id of record.attachmentIds) {
      const asset = byId.get(id);
      if (!asset || asset.projectId !== p.id || asset.recordId !== record.id) throw new Error('某条记录的附件缺失或所属关系不一致，不能导出完整备份。请先修复附件关联。');
      attachments.push(asset);
    }
    const payload = { format: 'paper-studio-backup', version: 1, workspace: snapshot, attachments };
    downloadText(JSON.stringify(payload, null, 2), `论文工作室-备份-${new Date().toISOString().slice(0, 10)}.json`, 'application/json');
    toast('完整工作区备份已导出，包含附件'); return;
  }
  if (name === 'import-backup') { selectFile('.json', restoreBackup); return; }
  if (name === 'import-bibtex') {
    selectFile('.bib,.txt', async file => {
      if (file.size > 5 * 1024 * 1024) throw new Error('BibTeX 文件最多 5 MB。');
      const records = parseBibtex(await file.text());
      const p = project(); const previous = p.records.slice();
      p.records.push(...records);
      if (!persist(`已导入 ${records.length} 条文献`)) { p.records = previous; return; }
      render();
    }); return;
  }
  if (name === 'export-bibtex') { downloadText(referencesToBibtex(project().records.filter(r => r.kind === 'references')), `${project().name}-references.bib`, 'application/x-bibtex;charset=utf-8'); toast('参考文献已导出'); return; }
  if (name === 'preview-file') { await previewFile(b.dataset.id!); return; }
  if (name === 'download-file') { const a = await getAttachment(b.dataset.id!); if (a) downloadBlob(a.blob, a.name); else throw new Error('附件不存在'); return; }
  if (name === 'delete-record') {
    const p = project(); const record = p.records.find(r => r.id === b.dataset.id)!;
    if (!confirm(`删除“${record.title}”及其附件？`)) return;
    const previous = p.records;
    p.records = p.records.filter(r => r.id !== record.id);
    if (!persist('记录已删除')) { p.records = previous; return; }
    b.closest('dialog')?.close(); render();
    try { await Promise.all(record.attachmentIds.map(deleteAttachment)); }
    catch (error) { toast(`记录已删除，但旧附件尚未清理：${errorText(error)}`, true); }
    return;
  }
  if (name === 'delete-project') {
    if (workspace.projects.length < 2) throw new Error('至少保留一个项目。可先创建新项目，再删除此项目。');
    const p = project();
    if (!confirm(`删除项目“${p.name}”及其所有记录和附件？`)) return;
    const previous = workspace;
    workspace = { ...workspace, projects: workspace.projects.filter(x => x.id !== p.id) };
    workspace.activeProjectId = workspace.projects[0].id;
    if (!persist('项目已删除')) { workspace = previous; return; }
    b.closest('dialog')?.close(); view = 'overview'; render();
    try { await deleteProjectAttachments(p.id); }
    catch (error) { toast(`项目已删除，但旧附件尚未清理：${errorText(error)}`, true); }
    return;
  }
  if (name === 'help') openDialog('关于论文工作室', `<div class="dialog-body help-copy"><p>这是你的科研项目工作空间。每个项目独立管理论文正文、审查、复盘、实验、步骤、模型、数据和参考文献。</p><h3>如何开始</h3><ol><li>新建项目，填写研究目标。</li><li>进入工作区，添加结构化记录与原始文件。</li><li>在论文写作中整理 Markdown 正文，用 [@引用键] 记录引用。</li><li>定期导出完整 JSON 备份，迁移到另一台设备时导入。</li></ol><h3>数据保存</h3><p>文字自动保存在此浏览器的本地存储；附件保存在 IndexedDB。这里没有账号或云同步，清理网站数据会删除本地资料。完整 JSON 备份包含所有项目与附件，Markdown 和 BibTeX 导出方便继续使用。</p><h3>功能范围</h3><p>CSV 可预览前 100 行和 25 列。GitHub工程模型区直接展示当前 Abaqus INP 有限元网格，并可叠加原始 Abaqus RNA 表面网格；目前不会在浏览器中执行有限元求解或修改专有 CAE。论文审查与复盘由你记录和判断，不会自动生成学术结论。</p><p>初始项目中的所有内容均为演示模板，不是实测数据或已验证的研究结论。</p></div>`);
}
document.addEventListener('click', e => {
  if (restoring) { e.preventDefault(); return; }
  const target = (e.target as Element).closest<HTMLElement>('[data-view],[data-open],[data-action],[data-heading]'); if (!target) return;
  if (target.dataset.view) { e.preventDefault(); if (savingTimer) clearTimeout(savingTimer); persist(); view = target.dataset.view as View; query = ''; statusFilter = 'all'; render(); window.scrollTo(0, 0); }
  else if (target.dataset.open) void recordDialog(target.dataset.open).catch(e => toast(errorText(e), true));
  else if (target.dataset.action) void action(target.dataset.action, target).catch(e => toast(errorText(e), true));
  else if (target.dataset.heading) { const editor = app.querySelector<HTMLTextAreaElement>('#manuscript-editor'); if (!editor) return; const headings = [...editor.value.matchAll(/^#{1,3} .*$/gm)]; const start = headings[Number(target.dataset.heading)]?.index || 0; editor.focus(); editor.setSelectionRange(start, start); editor.scrollTop = Math.max(0, editor.value.slice(0, start).split('\n').length * 29 - 80); }
});
document.addEventListener('keydown', e => { if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); app.querySelector<HTMLInputElement>('#global-search')?.focus(); } if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') { e.preventDefault(); persist('已保存'); } });
window.addEventListener('pagehide', () => { if (recoveryError || restoring) return; try { saveWorkspace(workspace); } catch { /* A visible error is reported by persist during editing. */ } });
render();
