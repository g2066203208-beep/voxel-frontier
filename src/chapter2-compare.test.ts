import { readFileSync, existsSync } from "node:fs";
import { resolve } from "node:path";
import { Script } from "node:vm";
import { test } from "node:test";
import assert from "node:assert/strict";

const dir = resolve(process.cwd(), "public", "thesis-studio");
const source = (f: string) => readFileSync(resolve(dir, f), "utf8");
const data = JSON.parse(source("data/chapter2-27-pages.json"));

test("two uploaded second chapters remain complete, ordered, page-aligned and source-labelled", () => {
  assert.equal(data.schema, 1);
  assert.equal(data.pages.ours.length, 18);
  assert.equal(data.pages.he.length, 9);
  assert.deepEqual(data.pages.ours.map((x: { page: number }) => x.page), Array.from({ length: 18 }, (_, i) => 22 + i));
  assert.deepEqual(data.pages.he.map((x: { page: number }) => x.page), Array.from({ length: 9 }, (_, i) => 18 + i));
  for (const section of [data.pages.ours, data.pages.he]) {
    for (const item of section) {
      assert.ok(item.text.length > 150, "Missing extracted text on page " + item.page);
    }
  }
  assert.match(data.pages.ours[0].text, /第二章|10 MW/);
  assert.match(data.pages.he[0].text, /环境荷载|第2章/);
  assert.equal(data.sources.ours.sha256.length, 64);
  assert.equal(data.sources.he.sha256.length, 64);
});

test("the original reference PDF exists; site does not mislabel manuscript text as an original image", () => {
  const filename = resolve(dir, "documents/He_Zeyu_2024_hybrid_tower_thesis.pdf");
  assert.ok(existsSync(filename), "Archived original PDF missing");
  const head = readFileSync(filename).subarray(0, 5).toString();
  assert.equal(head, "%PDF-");
  assert.match(data.sources.ours.presentation, /不是原版截图/);
  assert.match(source("chapter2-compare.html"), /PDF\.js原始版式渲染/);
});

test("new reader assets are parseable and linked in the existing thesis workspace", () => {
  new Script(source("chapter2-compare.js"), { filename: "chapter2-compare.js" });
  const home = source("index.html");
  assert.ok((home.match(/chapter2-compare\.html/g) ?? []).length >= 2, "Existing site has no navigation to comparison");
  assert.match(source("chapter2-compare.html"), /id="all-pages"/);
  assert.match(source("chapter2-compare.html"), /id="search-results"/);
  assert.match(source("chapter2-compare.css"), /@media\(max-width:750px\)/);
});
