import test from 'node:test';
import assert from 'node:assert/strict';
import { MAX_ATTACHMENT_SIZE, parseCsv, readPreview, validateAttachmentBackups, type Attachment, type AttachmentBackup } from './files';

const backup = (extra: Partial<AttachmentBackup> = {}): AttachmentBackup => ({
  id: 'asset-1', projectId: 'project-1', recordId: 'record-1', name: '实验.csv', type: 'text/csv', size: 3,
  createdAt: '2026-10-03T08:00:00.000Z', data: 'YWJj', ...extra,
});

test('CSV preserves quoted delimiters, escaped quotes, multiline fields, CRLF and empty cells', () => {
  const source = '\uFEFFname,note,result\r\n"sample, A","said ""yes""\r\nnext line",\r\nB,,0\r\n';
  assert.deepEqual(parseCsv(source), [
    ['name', 'note', 'result'], ['sample, A', 'said "yes"\r\nnext line', ''], ['B', '', '0'],
  ]);
});

test('TSV detection ignores separators inside quoted fields', () => {
  assert.deepEqual(parseCsv('name\tnote\nA\t"one,two,three"'), [['name', 'note'], ['A', 'one,two,three']]);
  assert.deepEqual(parseCsv('"a,b,c"\td\nx\ty'), [['a,b,c', 'd'], ['x', 'y']]);
});

test('empty CSV and trailing delimiters have consistent records', () => {
  assert.deepEqual(parseCsv(''), []);
  assert.deepEqual(parseCsv('\uFEFF'), []);
  assert.deepEqual(parseCsv('a,b,'), [['a', 'b', '']]);
  assert.deepEqual(parseCsv('""'), [['']]);
  assert.deepEqual(parseCsv('\n'), [['']]);
});

test('malformed CSV is rejected instead of misrepresenting experiment values', () => {
  assert.throws(() => parseCsv('a,"unterminated'), /未闭合/);
  assert.throws(() => parseCsv('a,"closed"oops'), /引号闭合/);
  assert.throws(() => parseCsv('a,un"quoted'), /未加引号/);
});

test('backup bytes round-trip for arbitrary binary files and empty files', async () => {
  const data = btoa(String.fromCharCode(0, 128, 255));
  const records = validateAttachmentBackups([backup({ data, type: 'application/octet-stream' }), backup({ id: 'empty', data: '', size: 0 })], ['project-1']);
  assert.deepEqual(Array.from(new Uint8Array(await records[0].blob.arrayBuffer())), [0, 128, 255]);
  assert.equal(records[1].blob.size, 0);
  assert.equal(records[0].blob.type, 'application/octet-stream');
});

test('backup rejects orphan projects, duplicate IDs and malformed metadata', () => {
  assert.throws(() => validateAttachmentBackups({}, ['project-1']), /数组/);
  assert.throws(() => validateAttachmentBackups([null], ['project-1']), /格式/);
  assert.throws(() => validateAttachmentBackups([backup()], ['different-project']), /项目/);
  assert.throws(() => validateAttachmentBackups([backup(), backup()], ['project-1']), /重复/);
  for (const item of [backup({ name: '' }), backup({ id: 'bad\nvalue' }), backup({ type: 'text/html;evil' }), backup({ createdAt: '2026-02-30T08:00:00.000Z' }), backup({ size: -1 }), backup({ size: 1.5 })]) {
    assert.throws(() => validateAttachmentBackups([item], ['project-1']));
  }
});

test('backup rejects corrupt or mismatched Base64 without accessing IndexedDB', () => {
  for (const data of ['<script>', 'Y WJj', 'YWJj=', '====', 'YW', 'YR==']) {
    assert.throws(() => validateAttachmentBackups([backup({ data, size: data === 'YR==' ? 1 : 3 })], ['project-1']), /Base64|编码/);
  }
  assert.throws(() => validateAttachmentBackups([backup({ size: 2 })], ['project-1']), /大小不一致/);
  assert.throws(() => validateAttachmentBackups([backup({ size: MAX_ATTACHMENT_SIZE + 1 })], ['project-1']), /20 MB/);
  const oversizedBackup = Array.from({ length: 11 }, (_, index) => backup({ id: `large-${index}`, size: MAX_ATTACHMENT_SIZE, data: '' }));
  assert.throws(() => validateAttachmentBackups(oversizedBackup, ['project-1']), /总容量超过 200 MB/);
});

test('CSV preview caps rows and columns while text previews remain inert strings', async () => {
  const csv = Array.from({ length: 150 }, (_, row) => Array.from({ length: 30 }, (_, column) => `${row}:${column}`).join(',')).join('\n');
  const attachment: Attachment = { ...backup(), blob: new Blob([csv]), size: csv.length };
  const preview = await readPreview(attachment);
  assert.equal(preview.kind, 'table');
  if (preview.kind === 'table') {
    assert.equal(preview.rows.length, 100);
    assert.equal(preview.rows[0].length, 25);
    assert.equal(preview.rows[99][24], '99:24');
  }
  const html = '<script>alert(document.cookie)</script>';
  const unsafe = await readPreview({ ...attachment, name: 'unsafe.html', type: 'text/html', size: html.length, blob: new Blob([html]) });
  assert.deepEqual(unsafe, { kind: 'text', text: html });
});

test('model files are downloadable attachments without a fabricated 3D preview', async () => {
  const preview = await readPreview({ ...backup(), name: 'model.glb', type: 'model/gltf-binary', blob: new Blob(['abc']) });
  assert.equal(preview.kind, 'file');
});
