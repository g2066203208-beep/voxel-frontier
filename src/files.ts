export interface Attachment {
  id: string;
  projectId: string;
  recordId: string;
  name: string;
  type: string;
  size: number;
  createdAt: string;
  blob: Blob;
}

export interface AttachmentBackup {
  id: string;
  projectId: string;
  recordId: string;
  name: string;
  type: string;
  size: number;
  createdAt: string;
  data: string;
}

export const MAX_ATTACHMENT_SIZE = 20 * 1024 * 1024;
export const MAX_TOTAL_ATTACHMENT_SIZE = 200 * 1024 * 1024;
const STORE = 'attachments';
let database: Promise<IDBDatabase> | undefined;

function openDatabase(): Promise<IDBDatabase> {
  if (typeof indexedDB === 'undefined') return Promise.reject(new Error('当前环境不支持本地附件存储，请使用支持 IndexedDB 的浏览器。'));
  if (!database) {
    database = new Promise<IDBDatabase>((resolve, reject) => {
      let blocked = false;
      const request = indexedDB.open('paper-studio-assets', 1);
      request.onupgradeneeded = () => {
        const db = request.result;
        if (!db.objectStoreNames.contains(STORE)) {
          const store = db.createObjectStore(STORE, { keyPath: 'id' });
          store.createIndex('projectId', 'projectId');
          store.createIndex('recordId', 'recordId');
        }
      };
      request.onsuccess = () => {
        const db = request.result;
        if (blocked) { db.close(); return; }
        db.onversionchange = () => { db.close(); database = undefined; };
        resolve(db);
      };
      request.onerror = () => reject(request.error ?? new Error('无法打开本地附件库。'));
      request.onblocked = () => { blocked = true; reject(new Error('附件库被其他页面占用，请关闭旧页面后重试。')); };
    }).catch(error => { database = undefined; throw error; });
  }
  return database;
}

async function readAll(): Promise<Attachment[]> {
  const db = await openDatabase();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(STORE, 'readonly');
    const request = transaction.objectStore(STORE).getAll();
    transaction.oncomplete = () => resolve(request.result as Attachment[]);
    transaction.onerror = () => reject(transaction.error ?? request.error ?? new Error('读取附件失败。'));
    transaction.onabort = () => reject(transaction.error ?? new Error('读取附件被中止。'));
  });
}

// Keep the read and subsequent writes in one transaction so concurrent tabs cannot exceed the quota.
async function mutate<T>(operation: (store: IDBObjectStore, current: Attachment[]) => T): Promise<T> {
  const db = await openDatabase();
  return new Promise<T>((resolve, reject) => {
    const transaction = db.transaction(STORE, 'readwrite');
    const store = transaction.objectStore(STORE);
    const request = store.getAll();
    let value: T;
    let operationError: unknown;
    request.onsuccess = () => {
      try { value = operation(store, request.result as Attachment[]); }
      catch (error) { operationError = error; transaction.abort(); }
    };
    transaction.oncomplete = () => resolve(value);
    // Report a failed write only after the abort has finished rolling back all requests.
    transaction.onerror = () => { operationError ??= transaction.error; };
    transaction.onabort = () => reject(operationError ?? transaction.error ?? new Error('保存附件被中止，原有附件已保留。'));
  });
}

function validString(value: unknown, label: string, maxLength: number, allowEmpty = false): string {
  if (typeof value !== 'string' || (!allowEmpty && !value.trim()) || value.length > maxLength || /[\u0000-\u001f\u007f]/.test(value)) {
    throw new Error(`附件${label}不合法。`);
  }
  return value;
}

function validType(value: unknown): string {
  const type = validString(value, '类型', 127, true);
  if (type && !/^[a-z0-9!#$&^_.+-]+\/[a-z0-9!#$&^_.+-]+$/i.test(type)) throw new Error('附件 MIME 类型不合法。');
  return type;
}

export async function addAttachment(projectId: string, recordId: string, file: File): Promise<Attachment> {
  validString(projectId, '项目编号', 128);
  validString(recordId, '记录编号', 128);
  if (!(file instanceof Blob)) throw new Error('请选择有效的文件。');
  const name = validString(file.name, '名称', 255);
  const type = validType(file.type);
  if (file.size > MAX_ATTACHMENT_SIZE) throw new Error('单个附件最大为 20 MB。');
  const attachment: Attachment = {
    id: typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function' ? crypto.randomUUID() : `asset-${Date.now()}-${Math.random().toString(36).slice(2)}`,
    projectId, recordId, name, type, size: file.size, createdAt: new Date().toISOString(), blob: file,
  };
  return mutate((store, current) => {
    if (current.reduce((total, item) => total + item.size, 0) + file.size > MAX_TOTAL_ATTACHMENT_SIZE) throw new Error('附件总容量最大为 200 MB，请先删除不需要的附件。');
    store.add(attachment);
    return attachment;
  });
}

export async function getAttachment(id: string): Promise<Attachment | undefined> {
  const db = await openDatabase();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(STORE, 'readonly');
    const request = transaction.objectStore(STORE).get(id);
    transaction.oncomplete = () => resolve(request.result as Attachment | undefined);
    transaction.onerror = () => reject(transaction.error ?? request.error ?? new Error('读取附件失败。'));
    transaction.onabort = () => reject(transaction.error ?? new Error('读取附件被中止。'));
  });
}

export async function listAttachments(projectId: string, recordId?: string): Promise<Attachment[]> {
  return (await readAll()).filter(item => item.projectId === projectId && (recordId === undefined || item.recordId === recordId)).sort((a, b) => a.createdAt.localeCompare(b.createdAt));
}

export async function deleteAttachment(id: string): Promise<void> {
  await mutate(store => { store.delete(id); });
}

export async function deleteProjectAttachments(projectId: string): Promise<void> {
  await mutate((store, current) => { for (const item of current) if (item.projectId === projectId) store.delete(item.id); });
}

function encodeBase64(bytes: Uint8Array): string {
  let binary = '';
  for (let offset = 0; offset < bytes.length; offset += 8192) binary += String.fromCharCode(...bytes.subarray(offset, offset + 8192));
  return btoa(binary);
}

export async function exportAttachments(): Promise<AttachmentBackup[]> {
  const result: AttachmentBackup[] = [];
  for (const item of await readAll()) {
    const { blob, ...metadata } = item;
    result.push({ ...metadata, data: encodeBase64(new Uint8Array(await blob.arrayBuffer())) });
  }
  return result;
}

/** Pure validation, also usable when importing this module outside the browser. */
export function validateAttachmentBackups(items: unknown, allowedProjects: string[]): Attachment[] {
  if (!Array.isArray(items) || items.length > 10000) throw new Error('附件备份必须是数组，且最多包含 10000 个附件。');
  const projects = new Set(allowedProjects);
  const ids = new Set<string>();
  let totalSize = 0;
  const metadata = items.map((item: unknown): AttachmentBackup => {
    if (!item || typeof item !== 'object' || Array.isArray(item)) throw new Error('附件备份格式不合法。');
    const source = item as Record<string, unknown>;
    const id = validString(source.id, '编号', 128);
    if (ids.has(id)) throw new Error('附件备份包含重复编号。');
    ids.add(id);
    const projectId = validString(source.projectId, '项目编号', 128);
    if (!projects.has(projectId)) throw new Error('附件不属于备份中的项目。');
    const recordId = validString(source.recordId, '记录编号', 128);
    const name = validString(source.name, '名称', 255);
    const type = validType(source.type);
    const createdAt = validString(source.createdAt, '日期', 32);
    const parsedDate = new Date(createdAt);
    if (!Number.isFinite(parsedDate.getTime()) || parsedDate.toISOString() !== createdAt) throw new Error('附件日期必须是有效的 ISO 时间。');
    const size = source.size;
    if (typeof size !== 'number' || !Number.isSafeInteger(size) || size < 0 || size > MAX_ATTACHMENT_SIZE) throw new Error('附件大小不合法，单个附件最大为 20 MB。');
    totalSize += size;
    if (totalSize > MAX_TOTAL_ATTACHMENT_SIZE) throw new Error('附件备份总容量超过 200 MB。');
    if (typeof source.data !== 'string') throw new Error('附件数据不是有效的 Base64。');
    return { id, projectId, recordId, name, type, size, createdAt, data: source.data };
  });
  // Validate all encoded lengths before allocating binary buffers for any file.
  for (const item of metadata) {
    const { data, size } = item;
    if (data.length > Math.ceil(MAX_ATTACHMENT_SIZE / 3) * 4 || data.length % 4 !== 0 || !/^[A-Za-z0-9+/]*={0,2}$/.test(data)) throw new Error('附件数据不是有效的 Base64。');
    const decodedSize = data.length / 4 * 3 - (data.endsWith('==') ? 2 : data.endsWith('=') ? 1 : 0);
    if (decodedSize !== size) throw new Error('附件数据与声明的大小不一致。');
  }
  return metadata.map(item => {
    const { data, ...fields } = item;
    const binary = atob(data);
    // Reject noncanonical pad bits too, rather than silently accepting corrupt backups.
    if (btoa(binary) !== data) throw new Error('附件 Base64 编码不规范。');
    const bytes = new Uint8Array(binary.length);
    for (let index = 0; index < binary.length; index++) bytes[index] = binary.charCodeAt(index);
    return { ...fields, blob: new Blob([bytes], { type: fields.type }) };
  });
}

export async function importAttachments(items: unknown, allowedProjects: string[], beforeCommit?: () => void): Promise<void> {
  // No database changes happen until every attachment has passed validation.
  const validated = validateAttachmentBackups(items, allowedProjects);
  await mutate(store => {
    store.clear();
    for (const item of validated) store.add(item);
    beforeCommit?.();
  });
}

function csvDelimiter(text: string): ',' | '\t' {
  let quoted = false;
  let commas = 0;
  let tabs = 0;
  for (let index = 0; index < text.length; index++) {
    const char = text[index];
    if (char === '"') {
      if (quoted && text[index + 1] === '"') { index++; continue; }
      quoted = !quoted;
    } else if (!quoted) {
      if (char === '\n' || char === '\r') break;
      if (char === ',') commas++;
      if (char === '\t') tabs++;
    }
  }
  return tabs > commas ? '\t' : ',';
}

function parseCsvRows(source: string, maxRows = Infinity, maxColumns = Infinity, maxCellLength = Infinity): string[][] {
  const text = source.replace(/^\uFEFF/, '');
  if (!text) return [];
  const delimiter = csvDelimiter(text);
  const rows: string[][] = [];
  let row: string[] = [];
  let value = '';
  let quoted = false;
  let afterQuote = false;
  let fieldStarted = false;
  let rowStarted = false;
  const append = (char: string) => { if (value.length < maxCellLength && row.length < maxColumns) value += char; };
  const finishField = () => {
    if (row.length < maxColumns) row.push(value);
    value = ''; afterQuote = false; fieldStarted = false;
  };
  const finishRow = () => { finishField(); rows.push(row); row = []; rowStarted = false; };
  for (let index = 0; index < text.length; index++) {
    const char = text[index];
    if (quoted) {
      if (char === '"') {
        if (text[index + 1] === '"') { append('"'); index++; }
        else { quoted = false; afterQuote = true; }
      } else append(char);
      continue;
    }
    if (char === delimiter) { finishField(); rowStarted = true; continue; }
    if (char === '\n' || char === '\r') {
      if (char === '\r' && text[index + 1] === '\n') index++;
      finishRow();
      if (rows.length >= maxRows) return rows;
      continue;
    }
    if (afterQuote) {
      if (char === ' ' || (char === '\t' && delimiter !== '\t')) continue;
      throw new Error('CSV 格式错误：引号闭合后应为分隔符或换行。');
    }
    if (char === '"') {
      if (fieldStarted) throw new Error('CSV 格式错误：未加引号的字段中包含引号。');
      quoted = true; fieldStarted = true; rowStarted = true;
    } else { append(char); fieldStarted = true; rowStarted = true; }
  }
  if (quoted) throw new Error('CSV 格式错误：存在未闭合的引号。');
  if (rowStarted || row.length || fieldStarted || afterQuote) finishRow();
  return rows;
}

export function parseCsv(text: string): string[][] { return parseCsvRows(text); }

export function downloadBlob(blob: Blob, name: string): void {
  if (typeof document === 'undefined') throw new Error('下载文件需要浏览器环境。');
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = name.replace(/[<>:"/\\|?*\u0000-\u001f]/g, '-').slice(0, 255) || 'attachment';
  anchor.style.display = 'none';
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1500);
}

export async function readPreview(a: Attachment): Promise<{ kind: 'table'; rows: string[][] } | { kind: 'text'; text: string } | { kind: 'image'; url: string } | { kind: 'file'; text: string }> {
  if (/\.(csv|tsv)$/i.test(a.name) || /^(text\/csv|text\/tab-separated-values)$/i.test(a.type)) {
    return { kind: 'table', rows: parseCsvRows(await a.blob.text(), 100, 25, 4000) };
  }
  if (/^image\/(png|jpeg|gif|webp|avif|bmp)$/i.test(a.type)) return { kind: 'image', url: URL.createObjectURL(a.blob) };
  if (/^text\//i.test(a.type) || /\.(txt|md|json|yaml|yml|log|bib|xml|html|htm|svg)$/i.test(a.name) || a.type === 'application/json') {
    const limit = 100000;
    const text = await a.blob.slice(0, limit * 4).text();
    return { kind: 'text', text: text.slice(0, limit) + (text.length > limit || a.size > limit * 4 ? '\n\n……预览已截断，下载可查看完整内容。' : '') };
  }
  return { kind: 'file', text: '文件已保存在本地附件库。下载后可用对应软件查看；模型文件可在 Blender、CAD 等软件中打开。' };
}
