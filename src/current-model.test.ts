import assert from 'node:assert/strict';
import test from 'node:test';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import snapshot from '../research/wind-tower/models/CURRENT_TOWER_SETTINGS_20261114.json';
import { currentModelPage } from './current-model';

test('2026-11-14 current model snapshot is complete and clearly sourced', () => {
  assert.equal(snapshot.schema_version, '1.0');
  assert.equal(snapshot.sections.length, 9);
  assert.equal(snapshot.sections.reduce((sum, section) => sum + section.rows.length, 0), 92);
  assert.equal(snapshot.provenance.original_files_available_to_this_assistant, false);
  assert.equal(snapshot.provenance.independent_native_verification_this_turn, false);
  assert.equal(new Set(snapshot.sections.map(section => section.id)).size, 9);
  for (const section of snapshot.sections) {
    assert.ok(section.rows.every(row => row.parameter.trim() && row.value.trim()));
    assert.ok(new Set(section.rows.map(row => row.parameter)).size === section.rows.length);
  }
});

test('current and historical models are explicitly separated in inline studio content', () => {
  const page = currentModelPage();
  assert.ok(page.includes('TOWER_AND_FOUNDATION_SEPARATE.cae'));
  assert.ok(page.includes('DTU158_HybridTower_Global_RNA_OFFICIAL_RP'));
  assert.ok(page.includes('DTU158_ALIGNED_GM_VERIFY.odb'));
  assert.ok(page.includes('BF1'));
  assert.ok(page.includes('EARTHQUAKE') === false || page.includes('Earthquake_EONLY_REVIEW'));
  assert.ok(page.includes('Earthquake_EONLY_REVIEW'));
  assert.ok(page.includes('31个 EMB_HOOP'));
  assert.ok(page.includes('历史T070参考数据'));
  assert.ok(page.includes('Codex本机Abaqus MCP读取确认'));
  assert.ok(page.includes('本助手二次原件复核'));
  assert.equal((page.match(/data-tower-row/g) ?? []).length, 92);
  assert.equal((page.match(/data-tower-section/g) ?? []).length, 9);
  assert.ok(page.includes('完整地震时程求解'));
  assert.ok(page.includes('未运行'));
  assert.ok(page.includes('基础顶面荷载文件'));
});

test('newly authored Ch3/Ch4 research sections remain before Word exclusion fence', () => {
  const root = join(process.cwd(), 'research', 'wind-tower', 'manuscript', 'final-thesis', 'chapters');
  const get = (name: string) => readFileSync(join(root, name), 'utf8');
  const ch3 = get('03_场址风环境与整机随机风控制载荷.md');
  const ch4 = get('04_10MW混合塔架风致疲劳性能分析.md');
  const fence = '\n# 工作区证据与门禁（不进入最终Word）';
  for (const [chapter, ids] of [
    [ch3, ['### 3.5.10']],
    [ch4, ['### 4.7.27', '### 4.7.28', '### 4.7.29', '### 4.10.1']]
  ] as const) {
    const boundary = chapter.indexOf(fence);
    assert.ok(boundary > 0, 'expected workspace fence');
    for (const section of ids) {
      const i = chapter.indexOf(section);
      assert.ok(i >= 0 && i < boundary, section + ' must be part of the manuscript');
      assert.equal(chapter.indexOf(section, i + section.length), -1, 'duplicate ' + section);
    }
    assert.doesNotMatch(chapter.slice(boundary), /^### \d+\.\d+\.\d+ /gm);
  }
  assert.ok(ch3.indexOf('### 3.5.10') < ch3.indexOf('\n## 3.6 '));
  assert.ok(ch4.indexOf('### 4.7.29') < ch4.indexOf('\n## 4.8 '));
  assert.ok(ch4.indexOf('### 4.10.1') > ch4.indexOf('\n## 4.10 '));
});
