import snapshot from '../research/wind-tower/models/CURRENT_TOWER_SETTINGS_20261114.json';

const escapeHtml = (value: unknown): string => String(value ?? '').replace(/[&<>"']/g, char => (
  { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' } as Record<string, string>
)[char]);

const sourceTag = (level: string): string => level === 'HISTORICAL_REPORTED'
  ? '原修复工程 · 历史结果'
  : level === 'CURRENT_AND_HISTORICAL_MIXED' ? '当前设置 / 历史结果' : '当前工程 · 报告设置';

export function currentModelPage(): string {
  const sections = snapshot.sections.map(section =>
    '<section class="panel tower-section" id="tower-' + escapeHtml(section.id) + '" data-tower-section>' +
      '<header class="tower-section-heading"><div><span class="tower-section-type">' + escapeHtml(sourceTag(section.evidence)) + '</span>' +
      '<h2>' + escapeHtml(section.title) + '</h2></div><span class="tower-section-count">' + section.rows.length + ' 项</span></header>' +
      '<div class="tower-table-wrap"><table class="tower-parameter-table"><thead><tr><th scope="col">项目</th><th scope="col">配置 / 数值</th><th scope="col">边界与说明</th></tr></thead>' +
      '<tbody>' + section.rows.map(row =>
        '<tr data-tower-row><th scope="row">' + escapeHtml(row.parameter) + '</th><td>' + escapeHtml(row.value) + '</td><td>' + escapeHtml(row.qualification || '—') + '</td></tr>'
      ).join('') + '</tbody></table></div></section>'
  ).join('');

  return '<div class="tower-snapshot">' +
    '<header class="tower-snapshot-header"><div class="eyebrow">MODEL CONFIGURATION / DOCUMENTED SNAPSHOT</div>' +
    '<h1>158 m混合塔架 · 当前工程配置</h1>' +
    '<p class="tower-snapshot-subtitle">TOWER_AND_FOUNDATION_SEPARATE.cae / DTU158_HybridTower_Global_RNA_OFFICIAL_RP</p>' +
    '<div class="tower-snapshot-meta"><span>报告时间　' + escapeHtml(snapshot.report_timestamp) + '</span>' +
    '<span>来源　Codex本机Abaqus MCP读取确认</span><span>本助手二次原件复核　未进行</span></div></header>' +
    '<section class="tower-metrics" aria-label="关键参数">' + snapshot.kpis.map(metric =>
      '<div class="tower-metric"><span>' + escapeHtml(metric.label) + '</span><strong>' +
      escapeHtml(metric.value) + '</strong><small>' + escapeHtml(metric.detail) + '</small></div>'
    ).join('') + '</section>' +
    '<section class="tower-evidence"><h2>版本与证据边界</h2>' +
    '<p>以下92项由Codex原生MCP实际读取确认、用户转交完整报告，本助手按原文结构化归档；本助手未再次读取本机CAE / ODB / 原始JSON。当前双模型工程没有Job；已求解的重力、模态、PT反力来自独立修复工程。页面下列数值不代表本次新增物理计算或独立验收。</p>' +
    '<p>现有三维查看器使用历史T070参考数据，不是这份当前双模型工程的实时渲染；两者不可混称。</p></section>' +
    '<div class="tower-index"><label for="tower-config-search">检索模型设置</label><input id="tower-config-search" type="search" autocomplete="off" placeholder="搜索材料、BF1、环筋、地震、反力…"/>' +
    '<span id="tower-config-count" role="status">92 / 92 项</span></div>' +
    '<div id="tower-config-results">' + sections + '</div><p id="tower-config-empty" class="tower-empty" hidden>没有匹配的参数。</p>' +
    '<section class="panel tower-holds"><h2>未闭合事项</h2><ol>' +
    snapshot.holds.map(item => '<li>' + escapeHtml(item) + '</li>').join('') + '</ol>' +
    '<p class="tower-cross-version">' + escapeHtml(snapshot.cross_version_warning) + '</p></section>' +
    '<section class="tower-source-footer"><h2>本机原始记录位置</h2>' +
    '<p>当前配置：<code>' + escapeHtml(snapshot.provenance.original_configuration_report_windows_path) + '</code></p>' +
    '<p>历史验收：<code>' + escapeHtml(snapshot.provenance.historical_validation_report_windows_path) + '</code></p>' +
    '<p>以上为报告中列出的本机路径，工作室不具备读取这些文件的权限。当前代码记录在研究分支PR #42，未合并main、未部署为正式Pages。</p></section>' +
    '</div>';
}

export function mountCurrentModel(root: HTMLElement): void {
  const input = root.querySelector<HTMLInputElement>('#tower-config-search');
  const count = root.querySelector<HTMLElement>('#tower-config-count');
  const empty = root.querySelector<HTMLElement>('#tower-config-empty');
  if (!input || !count || !empty) return;
  const sections = Array.from(root.querySelectorAll<HTMLElement>('[data-tower-section]'));
  const allRows = Array.from(root.querySelectorAll<HTMLTableRowElement>('[data-tower-row]'));
  input.addEventListener('input', () => {
    const query = input.value.trim().toLocaleLowerCase('zh-CN');
    let shown = 0;
    for (const section of sections) {
      let sectionRows = 0;
      const rows = section.querySelectorAll<HTMLTableRowElement>('[data-tower-row]');
      rows.forEach(row => {
        const match = (row.textContent || '').toLocaleLowerCase('zh-CN').includes(query);
        row.hidden = !match;
        if (match) { shown++; sectionRows++; }
      });
      section.hidden = sectionRows === 0;
    }
    count.textContent = shown + ' / ' + allRows.length + ' 项';
    empty.hidden = shown > 0;
  });
}
