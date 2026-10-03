export type RecordKind = 'reviews' | 'replications' | 'experiments' | 'protocols' | 'models' | 'datasets' | 'references';

export interface ResearchRecord {
  id: string;
  kind: RecordKind;
  title: string;
  summary: string;
  status: 'todo' | 'active' | 'done';
  date: string;
  tags: string[];
  fields: Record<string, string>;
  steps: { id: string; text: string; done: boolean }[];
  attachmentIds: string[];
}

export interface Project {
  id: string;
  name: string;
  description: string;
  manuscript: string;
  records: ResearchRecord[];
  updatedAt: string;
}

export interface Workspace { version: 1; activeProjectId: string; projects: Project[] }

const STORAGE_KEY = 'paper-studio.workspace.v1';
const KINDS: RecordKind[] = ['reviews', 'replications', 'experiments', 'protocols', 'models', 'datasets', 'references'];
const KIND_NAMES: Record<RecordKind, string> = {
  reviews: '论文审查', replications: '论文复盘', experiments: '实验记录', protocols: '研究步骤',
  models: '建模与模型', datasets: '研究数据', references: '参考文献',
};
const FIELD_NAMES: Record<string, string> = {
  priority: '优先级', finding: '发现', action: '处理建议', question: '研究问题', method: '复现方法',
  result: '结果', limitations: '局限', objective: '目标', materials: '材料', procedure: '操作流程',
  precautions: '注意事项', software: '软件', version: '版本', parameters: '参数', notes: '备注',
  source: '来源', variables: '变量', authors: '作者', year: '年份', venue: '期刊 / 出版物',
  doi: 'DOI', url: '链接', key: '引用键',
};
const DEFAULT_FIELDS: Record<RecordKind, Record<string, string>> = {
  reviews: { priority: '中', finding: '', action: '' },
  replications: { question: '', method: '', result: '', limitations: '' },
  experiments: { objective: '', materials: '', procedure: '', result: '' },
  protocols: { objective: '', precautions: '' },
  models: { software: '', version: '', parameters: '', notes: '' },
  datasets: { source: '', variables: '', notes: '' },
  references: { authors: '', year: '', venue: '', doi: '', url: '', key: '' },
};

export function uid(): string {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID();
  return `id-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 12)}`;
}

function today(): string { return new Date().toISOString().slice(0, 10); }

export function createRecord(kind: RecordKind): ResearchRecord {
  if (!KINDS.includes(kind)) throw new Error('未知的研究记录类型。');
  return {
    id: uid(), kind, title: `新的${KIND_NAMES[kind]}`, summary: '', status: 'todo', date: today(),
    tags: [], fields: { ...DEFAULT_FIELDS[kind] }, steps: [], attachmentIds: [],
  };
}

export function createProject(name: string): Project {
  const trimmed = name.trim();
  if (!trimmed || trimmed.length > 300) throw new Error('项目名称需要 1–300 个字符。');
  return { id: uid(), name: trimmed, description: '', manuscript: '', records: [], updatedAt: new Date().toISOString() };
}

export function createDemoWorkspace(): Workspace {
  const project = createProject('城市绿地与生活质量研究');
  project.description = '示例项目 · 所有研究安排和记录均为演示内容，未开展真实实验，结果与文献均待验证。';
  project.manuscript = '# 城市绿地与生活质量研究\n\n> 示例草稿：研究尚未开展，以下为写作框架，不能作为研究结论。\n\n## 研究问题\n城市绿地可达性与居民生活质量之间存在怎样的关联？\n\n## 方法\n计划定义绿地可达性指标、整理变量字典，并在得到合法数据后实施分析。\n\n## 结果\n待填入经验证的分析结果。\n\n## 讨论\n需讨论混杂因素、样本代表性与横断面设计的限制。\n\n## 参考文献\n待检索、核验和导入真实文献。';
  const add = (kind: RecordKind, title: string, summary: string, fields: Record<string, string>, steps: string[] = []) => {
    const record = createRecord(kind);
    Object.assign(record, { title, summary, fields: { ...record.fields, ...fields }, tags: ['示例', '待验证'] });
    record.steps = steps.map(text => ({ id: uid(), text, done: false }));
    project.records.push(record);
  };
  add('reviews', '示例：研究问题与变量定义审查', '审查设计是否能回答研究问题；以下意见为示例，不代表已有审稿结果。',
    { priority: '高', finding: '需要区分“绿地面积”与“步行可达性”，并明确生活质量量表的定义。', action: '建立变量字典，记录每个指标的单位、计算范围和来源。' }, ['核对研究问题与主要结果变量', '写明指标的操作性定义', '检查可能的混杂变量']);
  add('reviews', '示例：可重复性与伦理材料检查', '记录需要补齐的透明度材料；当前尚未获取真实参与者数据。',
    { priority: '中', finding: '分析脚本版本、排除规则和隐私处理流程尚待形成。', action: '预先记录纳入标准与缺失值策略；使用真实数据前核对授权和伦理要求。' }, ['记录数据使用依据', '注明排除规则', '保存代码版本与运行环境']);
  add('replications', '示例：绿地可达性方法复盘', '待选定并核验真实原始论文后，逐项对照其指标构建方法。',
    { question: '研究是否按步行网络而非直线距离计算可达性？', method: '计划整理原文的距离阈值、网络来源与分析单元，再对照重建。', result: '待验证；尚未运行复现。', limitations: '尚缺原论文与授权数据，不能判断结果是否一致。' }, ['绑定已核验原论文', '摘录可复现参数', '比较输出及差异原因']);
  add('replications', '示例：统计分析复盘清单', '复盘对象待确定，先记录需要从论文补充材料中提取的内容。',
    { question: '控制混杂变量后，关联方向是否稳定？', method: '计划对照模型公式、变量编码、标准误处理与敏感性分析。', result: '待验证；没有已复现的效应估计。', limitations: '不同数据、软件版本或变量口径可能造成差异。' }, ['提取模型公式', '记录软件及版本', '核对样本量与缺失值处理']);
  add('experiments', '示例：可达性指标试算', '演示实验记录模板，尚未开始试算，不包含真实实验结果。',
    { objective: '比较不同距离阈值对可达性指标的影响。', materials: '待取得授权的绿地边界、步行路网、居住单元数据。', procedure: '核对坐标系 → 清理网络 → 计算服务区 → 汇总指标 → 保存日志。', result: '待执行。' }, ['登记输入数据版本', '验证坐标与网络连通性', '保存参数和输出文件']);
  add('experiments', '示例：缺失值处理敏感性分析', '预先设计比较过程，避免在看到结果后任意调整规则。',
    { objective: '评估不同缺失值策略对分析样本和估计值的影响。', materials: '待获得且已脱敏的调查数据、变量字典与分析脚本。', procedure: '统计缺失模式 → 预先定义策略 → 分别运行分析 → 比较并记录。', result: '待执行；不存在当前分析结论。' }, ['检查缺失率', '记录预设策略', '归档每次运行的环境与输出']);
  add('protocols', '示例：从研究问题到分析方案', '一份可逐项勾选的研究流程；执行记录需依据实际情况填写。',
    { objective: '在获取数据和开始分析前明确研究方案。', precautions: '每次调整均记录原因、日期与版本，不以示例内容代替真实研究登记。' }, ['界定问题与研究对象', '检索并核验背景文献', '确定变量与数据来源', '记录主要分析与敏感性分析方案']);
  add('protocols', '示例：数据入库与核验', '将原始数据、清洗过程与分析数据分开记录，保留来源追踪。',
    { objective: '建立可追溯且可复现的数据处理流程。', precautions: '不覆盖唯一的原始数据；上传前清除不应共享的身份信息。' }, ['登记来源、许可和版本', '核对行列数与字段类型', '检查重复、异常和缺失', '保存清洗规则与处理日志']);
  add('models', '示例：绿地空间分析模型', '模型登记示例；软件版本和参数须在实际运行后补齐。',
    { software: '待选择 GIS / 网络分析工具', version: '待填写实际版本', parameters: '距离阈值、分析单元、坐标参考系均待确定。', notes: '保存输入数据标识、模型文件及运行日志；尚未建立真实模型。' }, ['确认输入数据和坐标系', '登记模型参数', '核验输出的空间范围']);
  add('models', '示例：生活质量关联分析模型', '记录统计建模方案，不提供虚构的回归结果。',
    { software: '待选择 R / Python 等分析环境', version: '待填写实际版本', parameters: '结果变量、解释变量、混杂变量与模型类型待预先确定。', notes: '记录公式、诊断方法和敏感性分析；当前没有拟合结果。' }, ['填写完整模型公式', '记录环境与依赖', '检查假设与诊断结果']);
  add('datasets', '示例：绿地与步行网络数据登记', '示例数据目录，尚未导入文件。来源和许可需要逐项核验。',
    { source: '待核验城市开放数据平台或其他获授权来源。', variables: '建议登记：绿地标识、几何类型、路段标识、长度、可步行性。', notes: '填写数据发布日期、坐标系、覆盖区域、许可和文件校验值。' }, ['核实数据许可', '记录坐标系与版本', '检查几何与拓扑有效性']);
  add('datasets', '示例：生活质量调查数据登记', '实际调查数据尚未获取；此记录仅展示数据管理结构。',
    { source: '待确认有权使用的调查数据及其伦理和授权材料。', variables: '建议登记：匿名样本编号、生活质量指标、人口学变量及缺失编码。', notes: '先核对数据字典；识别性信息不应进入共享研究资产。' }, ['登记使用依据', '核对脱敏处理', '建立变量字典']);
  add('references', '待补充：绿地可达性研究文献', '示例检索任务，尚未对应真实出版物。请导入并核验实际 BibTeX、DOI 或文献元数据。',
    { key: 'placeholder_accessibility', notes: '建议关键词：urban green space accessibility。此记录不是有效引文。' }, ['检索原始研究', '核对作者、年份与 DOI', '记录阅读笔记']);
  add('references', '待补充：生活质量测量方法文献', '示例检索任务，未编造作者、年份或期刊。正式引用前核实量表来源与适用范围。',
    { key: 'placeholder_quality_of_life', notes: '记录所选量表的原始来源及有效性证据。此记录不是有效引文。' }, ['确定测量工具', '查找并核验原始来源', '核对使用许可与适用人群']);
  return { version: 1, activeProjectId: project.id, projects: [project] };
}

function fail(path: string, message: string): never { throw new Error(`工作区格式错误：${path} ${message}`); }
function object(value: unknown, path: string, allowed?: string[]): Record<string, unknown> {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) fail(path, '必须是对象。');
  const proto = Object.getPrototypeOf(value);
  if (proto !== Object.prototype && proto !== null) fail(path, '不是普通数据对象。');
  const result = value as Record<string, unknown>;
  for (const key of Object.keys(result)) {
    if (['__proto__', 'constructor', 'prototype'].includes(key)) fail(path, '包含不安全字段。');
    if (allowed && !allowed.includes(key)) fail(path, `包含未知字段 ${key}。`);
  }
  return result;
}
function string(value: unknown, path: string, max = 20_000, nonempty = false): string {
  if (typeof value !== 'string' || value.length > max || value.includes('\0') || (nonempty && !value.trim())) {
    fail(path, `需要${nonempty ? '非空' : ''}字符串，最多 ${max} 个字符。`);
  }
  return value;
}
function identifier(value: unknown, path: string): string {
  const result = string(value, path, 128, true);
  if (!/^[A-Za-z0-9][A-Za-z0-9_.:-]*$/.test(result)) fail(path, '需要有效的标识符。');
  return result;
}
function array(value: unknown, path: string, max: number): unknown[] {
  if (!Array.isArray(value) || value.length > max) fail(path, `需要数组，最多 ${max} 项。`);
  return value;
}
function unique(values: string[], path: string): void {
  if (new Set(values).size !== values.length) fail(path, '存在重复标识符。');
}
function validDate(value: unknown, path: string): string {
  const result = string(value, path, 10);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(result) || !Number.isFinite(Date.parse(`${result}T00:00:00Z`)) || new Date(`${result}T00:00:00Z`).toISOString().slice(0, 10) !== result) fail(path, '需要有效的 YYYY-MM-DD 日期。');
  return result;
}

export function validateWorkspace(value: unknown): Workspace {
  const root = object(value, 'workspace', ['version', 'activeProjectId', 'projects']);
  if (root.version !== 1) fail('version', '仅支持版本 1。');
  const activeProjectId = identifier(root.activeProjectId, 'activeProjectId');
  let recordCount = 0;
  let textCount = 0;
  const projects = array(root.projects, 'projects', 50).map((rawProject, pi): Project => {
    const path = `projects[${pi}]`;
    const p = object(rawProject, path, ['id', 'name', 'description', 'manuscript', 'records', 'updatedAt']);
    const records = array(p.records, `${path}.records`, 1_000).map((rawRecord, ri): ResearchRecord => {
      if (++recordCount > 5_000) fail('records', '工作区最多包含 5000 条记录。');
      const rp = `${path}.records[${ri}]`;
      const r = object(rawRecord, rp, ['id', 'kind', 'title', 'summary', 'status', 'date', 'tags', 'fields', 'steps', 'attachmentIds']);
      if (!KINDS.includes(r.kind as RecordKind)) fail(`${rp}.kind`, '记录类型无效。');
      if (!['todo', 'active', 'done'].includes(r.status as string)) fail(`${rp}.status`, '状态无效。');
      const rawFields = object(r.fields, `${rp}.fields`);
      if (Object.keys(rawFields).length > 100) fail(`${rp}.fields`, '最多 100 个字段。');
      const fields: Record<string, string> = {};
      for (const [key, raw] of Object.entries(rawFields)) {
        string(key, `${rp}.fields key`, 100, true);
        fields[key] = string(raw, `${rp}.fields.${key}`, 100_000);
        textCount += fields[key].length;
      }
      const steps = array(r.steps, `${rp}.steps`, 500).map((rawStep, si) => {
        const sp = `${rp}.steps[${si}]`;
        const s = object(rawStep, sp, ['id', 'text', 'done']);
        if (typeof s.done !== 'boolean') fail(`${sp}.done`, '必须为布尔值。');
        return { id: identifier(s.id, `${sp}.id`), text: string(s.text, `${sp}.text`, 10_000), done: s.done };
      });
      unique(steps.map(s => s.id), `${rp}.steps`);
      const attachmentIds = array(r.attachmentIds, `${rp}.attachmentIds`, 100).map((id, ai) => identifier(id, `${rp}.attachmentIds[${ai}]`));
      unique(attachmentIds, `${rp}.attachmentIds`);
      const record: ResearchRecord = {
        id: identifier(r.id, `${rp}.id`), kind: r.kind as RecordKind,
        title: string(r.title, `${rp}.title`, 300, true), summary: string(r.summary, `${rp}.summary`),
        status: r.status as ResearchRecord['status'], date: validDate(r.date, `${rp}.date`),
        tags: array(r.tags, `${rp}.tags`, 50).map((tag, ti) => string(tag, `${rp}.tags[${ti}]`, 100, true)),
        fields, steps, attachmentIds,
      };
      textCount += record.title.length + record.summary.length + record.tags.join('').length + steps.reduce((n, s) => n + s.text.length, 0);
      return record;
    });
    unique(records.map(r => r.id), `${path}.records`);
    const updatedAt = string(p.updatedAt, `${path}.updatedAt`, 40);
    if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,3})?Z$/.test(updatedAt) || !Number.isFinite(Date.parse(updatedAt))) fail(`${path}.updatedAt`, '需要 UTC ISO 时间。');
    validDate(updatedAt.slice(0, 10), `${path}.updatedAt`);
    const project: Project = {
      id: identifier(p.id, `${path}.id`), name: string(p.name, `${path}.name`, 300, true),
      description: string(p.description, `${path}.description`, 4_000),
      manuscript: string(p.manuscript, `${path}.manuscript`, 2_000_000), records, updatedAt,
    };
    textCount += project.name.length + project.description.length + project.manuscript.length;
    if (textCount > 10_000_000) fail('workspace', '文本总量超过 1000 万字符，请分项目导出。');
    return project;
  });
  if (!projects.length) fail('projects', '至少需要一个项目。');
  unique(projects.map(p => p.id), 'projects');
  if (!projects.some(p => p.id === activeProjectId)) fail('activeProjectId', '未找到对应项目。');
  return { version: 1, activeProjectId, projects };
}

export function loadWorkspace(): Workspace {
  if (typeof globalThis.localStorage === 'undefined') return createDemoWorkspace();
  const saved = globalThis.localStorage.getItem(STORAGE_KEY);
  if (saved === null) return createDemoWorkspace();
  if (saved.length > 25_000_000) throw new Error('保存的工作区过大，请导出原数据后恢复。');
  return validateWorkspace(JSON.parse(saved));
}

export function saveWorkspace(workspace: Workspace): void {
  const safe = validateWorkspace(workspace);
  if (typeof globalThis.localStorage === 'undefined') throw new Error('当前环境不支持本地存储。');
  globalThis.localStorage.setItem(STORAGE_KEY, JSON.stringify(safe));
}

function markdownText(text: string): string {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/[\\`*_{}[\]()#+!|]/g, '\\$&');
}

export function exportMarkdown(project: Project): string {
  const status = { todo: '待办', active: '进行中', done: '已完成' };
  const lines = [`# ${markdownText(project.name)}`, '', project.description, '', `更新时间：${project.updatedAt}`, '', '## 论文草稿', '', project.manuscript || '（暂无草稿）'];
  for (const kind of KINDS) {
    lines.push('', `## ${KIND_NAMES[kind]}`, '');
    const records = project.records.filter(record => record.kind === kind);
    if (!records.length) lines.push('（暂无记录）');
    for (const record of records) {
      lines.push(`### ${markdownText(record.title)}`, '', `状态：${status[record.status]} · 日期：${record.date}`, '');
      if (record.tags.length) lines.push(`标签：${record.tags.map(markdownText).join('、')}`, '');
      if (record.summary) lines.push(record.summary, '');
      for (const [key, value] of Object.entries(record.fields)) {
        if (value && !key.startsWith('bibtex')) lines.push(`**${markdownText(FIELD_NAMES[key] || key)}**：${markdownText(value).replace(/\n/g, '  \n')}`, '');
      }
      for (const step of record.steps) lines.push(`- [${step.done ? 'x' : ' '}] ${markdownText(step.text).replace(/\n/g, ' ')}`);
      if (record.steps.length) lines.push('');
      if (record.attachmentIds.length) lines.push(`关联附件：${record.attachmentIds.length} 个。附件二进制内容不包含在 Markdown 中，请另行导出项目备份。`, '');
    }
  }
  return `${lines.join('\n').trim()}\n`;
}

function unescapeBraces(value: string): string { return value.replace(/\\([{}])/g, '$1'); }

export function parseBibtex(text: string): ResearchRecord[] {
  if (typeof text !== 'string' || text.length > 5_000_000) throw new Error('BibTeX 文件需要文本，最多 500 万字符。');
  let at = 0;
  const records: ResearchRecord[] = [];
  const macros = new Map<string, string>([['jan', 'January'], ['feb', 'February'], ['mar', 'March'], ['apr', 'April'], ['may', 'May'], ['jun', 'June'], ['jul', 'July'], ['aug', 'August'], ['sep', 'September'], ['oct', 'October'], ['nov', 'November'], ['dec', 'December']]);
  const keys = new Set<string>();
  const error = (message: string): never => { throw new Error(`BibTeX 第 ${at + 1} 个字符：${message}`); };
  const whitespace = () => {
    while (at < text.length) {
      if (/\s/.test(text[at])) at++;
      else if (text[at] === '%') { while (at < text.length && text[at] !== '\n') at++; }
      else break;
    }
  };
  const word = () => {
    whitespace();
    const start = at;
    while (at < text.length && /[A-Za-z0-9_:./+\-]/.test(text[at])) at++;
    if (at === start) error('需要字段名或条目类型。');
    return text.slice(start, at);
  };
  const component = (): string => {
    whitespace();
    const start = text[at];
    if (start === '{' || start === '"') {
      at++;
      let depth = 0;
      let value = '';
      while (at < text.length) {
        const ch = text[at++];
        if (ch === '\\') {
          if (at >= text.length) error('值末尾出现未完成的转义。');
          value += ch + text[at++];
          continue;
        }
        if (start === '{' && ch === '}' && depth === 0) return unescapeBraces(value);
        if (start === '"' && ch === '"' && depth === 0) return unescapeBraces(value);
        if (ch === '{') depth++;
        if (ch === '}') { if (depth === 0) error('字符串内的花括号不匹配。'); depth--; }
        value += ch;
      }
      error('字符串或花括号未闭合。');
    }
    const from = at;
    while (at < text.length && !/[\s,#})]/.test(text[at])) at++;
    if (at === from) error('缺少字段值。');
    const value = text.slice(from, at);
    return macros.get(value.toLowerCase()) ?? value;
  };
  const value = (): string => {
    let result = component();
    whitespace();
    while (text[at] === '#') { at++; result += component(); whitespace(); }
    return result;
  };
  while (at < text.length) {
    whitespace();
    if (at >= text.length) break;
    if (text[at] !== '@') { at++; continue; }
    at++;
    const type = word().toLowerCase();
    whitespace();
    const opening = text[at++];
    if (opening !== '{' && opening !== '(') error('条目需要以 { 或 ( 开始。');
    const closing = opening === '{' ? '}' : ')';
    if (type === 'comment') {
      let depth = 1;
      while (at < text.length && depth) {
        const ch = text[at++];
        if (ch === '\\') { at++; continue; }
        if (ch === opening) depth++;
        if (ch === closing) depth--;
      }
      if (depth) error('注释未闭合。');
      continue;
    }
    if (type === 'preamble') {
      value(); whitespace();
      if (text[at] === ',') { at++; whitespace(); }
      if (text[at++] !== closing) error('preamble 未正确闭合。');
      continue;
    }
    if (type === 'string') {
      const name = word().toLowerCase(); whitespace();
      if (text[at++] !== '=') error('string 需要赋值。');
      macros.set(name, value()); whitespace();
      if (text[at] === ',') { at++; whitespace(); }
      if (text[at++] !== closing) error('string 未正确闭合。');
      continue;
    }
    whitespace();
    const from = at;
    while (at < text.length && text[at] !== ',' && text[at] !== closing) at++;
    const key = text.slice(from, at).trim();
    if (!key || key.length > 200 || /[\s{}()]/.test(key)) error('引用键无效。');
    if (keys.has(key)) error(`存在重复引用键 ${key}。`);
    keys.add(key);
    const fields: Record<string, string> = {};
    if (text[at] === ',') at++;
    whitespace();
    while (at < text.length && text[at] !== closing) {
      const name = word().toLowerCase();
      if (['__proto__', 'constructor', 'prototype'].includes(name)) error('不安全的字段名。');
      if (Object.hasOwn(fields, name)) error(`重复字段 ${name}。`);
      whitespace();
      if (text[at++] !== '=') error(`字段 ${name} 缺少 =。`);
      fields[name] = value();
      if (fields[name].length > 100_000) error(`字段 ${name} 超过 10 万字符。`);
      whitespace();
      if (text[at] === ',') { at++; whitespace(); }
      else if (text[at] !== closing) error('字段之间缺少逗号。');
    }
    if (text[at++] !== closing) error('条目未闭合。');
    const record = createRecord('references');
    record.title = fields.title || key;
    if (record.title.length > 300) error('论文标题超过 300 个字符。');
    record.summary = fields.abstract || fields.note || '';
    if (record.summary.length > 20_000) error('摘要超过 2 万字符。');
    const venueField = fields.journal ? 'journal' : fields.booktitle ? 'booktitle' : fields.publisher ? 'publisher' : 'journal';
    Object.assign(record.fields, {
      authors: fields.author || fields.editor || '', year: fields.year || '', venue: fields[venueField] || '',
      doi: fields.doi || '', url: fields.url || '', key, bibtexType: type, bibtexVenueField: venueField,
    });
    for (const [name, fieldValue] of Object.entries(fields)) record.fields[`bibtex.${name}`] = fieldValue;
    record.tags = ['导入文献'];
    records.push(record);
    if (records.length > 1_000) error('单次最多导入 1000 条文献。');
  }
  if (!records.length) throw new Error('未找到有效的 BibTeX 文献条目。');
  return records;
}

function bibtexValue(text: string): string {
  const opens: number[] = [];
  const unbalanced = new Set<number>();
  for (let i = 0; i < text.length; i++) {
    if (text[i] === '\\') { i++; continue; }
    if (text[i] === '{') opens.push(i);
    if (text[i] === '}') { if (opens.length) opens.pop(); else unbalanced.add(i); }
  }
  opens.forEach(index => unbalanced.add(index));
  let escaped = '';
  for (let i = 0; i < text.length; i++) {
    if (unbalanced.has(i)) escaped += '\\';
    escaped += text[i];
  }
  let trailing = 0;
  for (let i = escaped.length - 1; i >= 0 && escaped[i] === '\\'; i--) trailing++;
  if (trailing % 2 === 1) escaped += '\\';
  return escaped;
}

export function referencesToBibtex(records: ResearchRecord[]): string {
  const seen = new Set<string>();
  return records.filter(record => record.kind === 'references').map((record, index) => {
    const requestedKey = record.fields.key || `reference_${index + 1}`;
    let key = requestedKey.replace(/[^\p{L}\p{N}_.:+/\-]/gu, '_') || `reference_${index + 1}`;
    if (key.length > 200) key = key.slice(0, 200);
    const base = key;
    let suffix = 2;
    while (seen.has(key)) key = `${base}_${suffix++}`;
    seen.add(key);
    const type = /^[a-zA-Z][a-zA-Z0-9]*$/.test(record.fields.bibtexType || '') ? record.fields.bibtexType : 'article';
    const fields: Record<string, string> = {};
    for (const [name, fieldValue] of Object.entries(record.fields)) {
      if (name.startsWith('bibtex.') && /^[A-Za-z][A-Za-z0-9_\-]*$/.test(name.slice(7)) && !['constructor', 'prototype'].includes(name.slice(7))) fields[name.slice(7)] = fieldValue;
    }
    fields.title = record.title;
    fields.author = record.fields.authors || '';
    fields.year = record.fields.year || '';
    const venueField = ['journal', 'booktitle', 'publisher'].includes(record.fields.bibtexVenueField) ? record.fields.bibtexVenueField : 'journal';
    fields[venueField] = record.fields.venue || '';
    fields.doi = record.fields.doi || '';
    fields.url = record.fields.url || '';
    if (record.summary) fields.abstract = record.summary;
    const assignments = Object.entries(fields).filter(([, fieldValue]) => fieldValue).map(([name, fieldValue]) => `  ${name} = {${bibtexValue(fieldValue)}}`);
    return `@${type}{${key},\n${assignments.join(',\n')}\n}`;
  }).join('\n\n') + (records.some(record => record.kind === 'references') ? '\n' : '');
}
