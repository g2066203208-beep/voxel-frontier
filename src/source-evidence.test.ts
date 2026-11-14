import assert from 'node:assert/strict';
import test from 'node:test';
import { evidenceImageCount, sourceEvidencePage } from './source-evidence';

test('original evidence atlas displays all 85 actual GitHub screenshot sources', () => {
  const html = sourceEvidencePage();
  assert.equal(evidenceImageCount, 85);
  assert.equal((html.match(/data-source-card="/g) ?? []).length, 85);
  assert.equal((html.match(/data-evidence-open="/g) ?? []).length, 85);
  assert.equal((html.match(/loading="lazy"/g) ?? []).length, 85);
  assert.equal((html.match(/raw\.githubusercontent\.com/g) ?? []).length, 85);
  assert.ok(html.includes('何泽瑜原文（11）'));
  assert.ok(html.includes('材料疲劳原文') || html.includes('疲劳文献（30）'));
  assert.ok(html.includes('学位论文对照（6）'));
  assert.ok(html.includes('不跳转GitHub'));
  assert.ok(!html.includes('target="_blank"'));
});
