import test from 'node:test';
import assert from 'node:assert/strict';
import { createDemoWorkspace, createProject, createRecord, exportMarkdown, parseBibtex, referencesToBibtex, validateWorkspace, loadWorkspace, saveWorkspace } from './store';

function clone<T>(value: T): T { return structuredClone(value); }

test('demo is valid, covers every research module, and marks sample results as unverified', () => {
  const workspace = validateWorkspace(createDemoWorkspace());
  const project = workspace.projects[0];
  assert.equal(project.name, '城市绿地与生活质量研究');
  for (const kind of ['reviews', 'replications', 'experiments', 'protocols', 'models', 'datasets', 'references']) {
    assert.ok(project.records.filter(record => record.kind === kind).length >= 2, kind);
  }
  assert.ok(project.records.every(record => record.tags.includes('示例') && record.tags.includes('待验证')));
  assert.ok(project.records.filter(record => record.kind === 'references').every(record => !record.fields.authors && !record.fields.year && !record.fields.doi));
  assert.match(project.description, /未开展真实实验/);
  const isolated = validateWorkspace(workspace);
  isolated.projects[0].records[0].fields.priority = 'Changed';
  assert.notEqual(workspace.projects[0].records[0].fields.priority, 'Changed');
});

test('imports reject broken identity, unsafe fields, invalid dates and excessive sizes', () => {
  const workspace = createDemoWorkspace();
  const broken: unknown[] = [null, [], { ...workspace, version: 2 }, { ...workspace, activeProjectId: 'missing' }, { ...workspace, projects: [] }];
  const duplicate = clone(workspace); duplicate.projects.push(clone(duplicate.projects[0])); broken.push(duplicate);
  const badStatus = clone(workspace); (badStatus.projects[0].records[0] as unknown as { status: string }).status = 'maybe'; broken.push(badStatus);
  const badDate = clone(workspace); badDate.projects[0].records[0].date = '2026-02-30'; broken.push(badDate);
  const badStep = clone(workspace); badStep.projects[0].records[0].steps[0].done = 'yes' as unknown as boolean; broken.push(badStep);
  const duplicateStep = clone(workspace); duplicateStep.projects[0].records[0].steps.push(clone(duplicateStep.projects[0].records[0].steps[0])); broken.push(duplicateStep);
  const badAttachment = clone(workspace); badAttachment.projects[0].records[0].attachmentIds = ['../unsafe']; broken.push(badAttachment);
  const unsafe = JSON.parse(JSON.stringify(workspace)); unsafe.projects[0].records[0].fields = JSON.parse('{"__proto__":{"polluted":true}}'); broken.push(unsafe);
  const oversized = clone(workspace); oversized.projects[0].records[0].title = 'a'.repeat(301); broken.push(oversized);
  const unknown = clone(workspace) as unknown as Record<string, unknown>; unknown.unexpected = true; broken.push(unknown);
  for (const value of broken) assert.throws(() => validateWorkspace(value), /工作区格式错误/);
  assert.equal(({} as Record<string, unknown>).polluted, undefined);
});

test('browser storage roundtrip and quota errors are visible rather than swallowed', () => {
  const descriptor = Object.getOwnPropertyDescriptor(globalThis, 'localStorage');
  const values = new Map<string, string>();
  const storage = {
    getItem(key: string) { return values.get(key) ?? null; },
    setItem(key: string, value: string) { values.set(key, value); },
  };
  Object.defineProperty(globalThis, 'localStorage', { configurable: true, value: storage });
  try {
    const workspace = createDemoWorkspace();
    saveWorkspace(workspace);
    assert.deepEqual(loadWorkspace(), workspace);
    assert.ok(values.has('paper-studio.workspace.v1'));
    values.set('paper-studio.workspace.v1', '{bad JSON');
    assert.throws(() => loadWorkspace(), SyntaxError);
    storage.setItem = () => { throw new Error('QuotaExceededError'); };
    assert.throws(() => saveWorkspace(workspace), /QuotaExceededError/);
  } finally {
    if (descriptor) Object.defineProperty(globalThis, 'localStorage', descriptor);
    else Reflect.deleteProperty(globalThis, 'localStorage');
  }
});

test('BibTeX handles nested braces, escaped braces, comments, macros, parentheses and concatenation', () => {
  const source = String.raw`% An example supplied by the user, not a verified citation.
@string{pub = "Example " # {Journal}}
@comment{Ignore {nested} metadata}
@preamble{"Ignored"}
@article(example2026,
 title = {A {DNA} model with \{literal\} braces},
 author = {Doe, Jane and Roe, John},
 year = 2026,
 journal = pub,
 doi = {10.0000/example},
 volume = {3},
 abstract = "A quoted {protected \" word} result"
)
@book{another, title="Second title", year={2025}, publisher={Example Publisher}}
`;
  const records = parseBibtex(source);
  assert.equal(records.length, 2);
  assert.equal(records[0].title, 'A {DNA} model with {literal} braces');
  assert.equal(records[0].fields.venue, 'Example Journal');
  assert.equal(records[0].fields.authors, 'Doe, Jane and Roe, John');
  assert.equal(records[0].fields['bibtex.volume'], '3');
  assert.equal(records[1].fields.bibtexType, 'book');
  assert.equal(records[1].fields.bibtexVenueField, 'publisher');
  const roundtrip = parseBibtex(referencesToBibtex(records));
  for (let i = 0; i < records.length; i++) {
    assert.equal(roundtrip[i].title, records[i].title);
    assert.equal(roundtrip[i].summary, records[i].summary);
    for (const field of ['authors', 'year', 'venue', 'doi', 'url', 'key', 'bibtexType', 'bibtexVenueField']) assert.equal(roundtrip[i].fields[field], records[i].fields[field]);
  }
  assert.equal(roundtrip[0].fields['bibtex.volume'], '3');
});

test('BibTeX rejects malformed and duplicate entries without partial import', () => {
  for (const source of [
    '', 'No entries here', '@article{x,title={Unclosed}', '@article{x,title="Unclosed}',
    '@article{x,title={A} year=2020}', '@article{x,title={A},title={B}}',
    '@article{x,title={A}} @book{x,title={B}}', '@article{x,__proto__={unsafe}}',
  ]) assert.throws(() => parseBibtex(source));
});

test('BibTeX export safely wraps unmatched braces and assigns collision-free keys', () => {
  const record = createRecord('references');
  record.title = 'An unmatched } brace { and newline\nvalue';
  record.fields.key = 'unsafe key }';
  record.fields.authors = 'Someone';
  const duplicate = clone(record); duplicate.id = 'another';
  const bib = referencesToBibtex([record, duplicate]);
  const result = parseBibtex(bib);
  assert.equal(result[0].title, record.title);
  assert.notEqual(result[0].fields.key, result[1].fields.key);
  assert.equal(result[0].fields.authors, 'Someone');
  assert.equal(referencesToBibtex([createRecord('models')]), '');
});

test('Markdown contains manuscript, every module, field contents and step completion', () => {
  const project = createProject('Research [draft]');
  project.manuscript = '## Original draft\n\nA reproducible study.';
  const record = createRecord('experiments');
  record.title = 'First <experiment>';
  record.fields.result = 'Not yet run';
  record.steps = [{ id: 'step1', text: 'Prepare data', done: true }, { id: 'step2', text: 'Run analysis', done: false }];
  record.attachmentIds = ['attachment1'];
  project.records.push(record);
  const markdown = exportMarkdown(project);
  assert.match(markdown, /Research \\\[draft\\\]/);
  assert.match(markdown, /## Original draft/);
  assert.match(markdown, /First &lt;experiment&gt;/);
  assert.match(markdown, /\*\*结果\*\*：Not yet run/);
  assert.match(markdown, /- \[x\] Prepare data/);
  assert.match(markdown, /- \[ \] Run analysis/);
  assert.match(markdown, /附件二进制内容不包含在 Markdown/);
  for (const heading of ['论文审查', '论文复盘', '实验记录', '研究步骤', '建模与模型', '研究数据', '参考文献']) assert.ok(markdown.includes(`## ${heading}`));
});
