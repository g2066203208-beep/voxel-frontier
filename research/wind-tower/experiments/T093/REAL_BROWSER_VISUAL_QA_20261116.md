# T093｜论文工作室真实浏览器视觉、PDF全文及手机阅读验收

**2026-11-16 · 唯一工作室**：`https://g2066203208-beep.github.io/voxel-frontier/thesis-studio/`。此报告是网站测试，不是任何Abaqus或学位论文物理算例验收。

## 真正执行过的浏览器测试

### 第一轮：未通过（不能用Pages部署SUCCESS代替视觉验收）

- Chromium Actions `43840135928`，最终CANCELLED；run日志 `scripts/qa-jiayu-browser.cjs:82` PDF全文等待60s超时。
- 真实附件 artifact `14214070190` 内6张原PNG由网页GPT实际取回本会话容器逐张查看：`jiayu-home-desktop.png`、`jiayu-era5-original-data.png`、`jiayu-real-esm-3component-original.png`、`jiayu-six-chapter-thesis-inline.png`、`jiayu-research-source-inline.png`、`jiayu-full-licensed-paper-page.png`。
- 可视观察：网站总体分组/配色学术简洁，ERA5数据卡片/ESM三分量真实质控图/研究TSV原表/合法完整期刊页视觉可读；**首页精选图全页快照时存在懒加载空白，论文第三章的LaTeX公式尚未真正数学排版**。第一轮没有拍到79份档案的完整PDF实际阅读截图。
- 源码确诊：`full-references.js`引了不存在的`./vendor/pdf.mjs`；后又发现 `pump().finally(... )()`错误调用，真实JavaScript抛出`...finally(...) is not a function`。**已修复并重新测试，不修改原始PDF文件。**

### 第二轮：PDF、手机、原始源图大范围通过，但整套QA仍失败

- Chromium Actions `43847974558`，最后`failure`，但详细日志已有明确原生验证：
  - `REAL_ORIGINAL_PDF_STATUS PDF.js已读取真实原始PDF · 9页`，L040原版`Parameter calculation and verification of concrete plastic damage model of ABAQUS`第一页实际Canvas解码截图，全部9页按需渲染序列存在；不是给一个PDF链接或图片假的占位符。
  - `FULL_REFERENCE_CORPUS_OK`：81 PDF目录、79可选原件入口、163条书目、395原始来源页全部DOM上屏。
  - `INLINE_ATLAS_OK`：5期刊出版来源图、24篇干缝专题文献条目、541研究归档图全部上屏，首张许可图真实解码。
  - 真实KaTeX MathML公式得到浏览器断言，网站六章正文可读。
  - 390px移动端文献、论文、ERA5视图的整页横向滚动宽度检查通过、输出3张手机版原PNG截图。
- 已取回并实际查看14张Chromium截图，对比桌面原始PDF第一页、真实地震图、期刊完整页、移动端文献/论文/数据页面；移动端布局无遮挡，分组清晰、页间距与按钮可读。
- 该轮仍`FAIL`的真实原因：旧`reader.js`在切换何泽瑜文献后，搜索目录DOM可能删除原`#reader-search-results`，但`select`仍直接对空节点调用`replaceChildren`，造成PAGE_ERROR，进而出现“标题显示何泽瑜论文，仍残留旧嘉鱼政府公文第2/3页”的错配截图。**没有将此问题隐瞒或计为通过。**
- 修复：旧PDF reader检查DOM是否还存在，切换时清空旧Canvas并隐藏其内容，等新PDF实际字节及页画布渲染后才显示；`reader-stage.dataset.documentId`仅于对应PDF成功载入时赋值。QA要求何泽瑜原文真正载入、至少20页、源身份匹配、渲染完成，拒绝旧公文残影。错误日志改为记录浏览器堆栈。

### 自托管授权程序与网站视觉修复

- 通过GitHub Actions `T093 Pin Local PDF Reader Assets`正式归档 Apache-2.0 PDF.js v5.4.530 的`pdf.mjs`及`pdf.worker.mjs`，取消对外部CDN的强依赖，原文不从本机下载才能读。
- `T093 Pin Professional Formula Renderer`通过Actions成功归档 MIT KaTeX v0.16.25，包括站内公式JS/CSS/字库，论文LaTeX转为可读MathML与视觉公式，保留原始论文Markdown内容字节不修改。
- 首页原图通过既有`Jiayu Research Library QA`对全部541图做**原Git Blob SHA+字节长度**一致性检查，395来源页均在541图中。首页第一轮截图空白主要是截屏早于3张精选图懒加载完成；新的QA等待原图卡片后再拍照。
- 最新正式版本`v1.9.1`，main针对旧PDF源切换与公式排版的最终Pages/Chromium综合验收应按最新GitHub Action实际结果**另行登记**，不能因上一轮大范围PASS就宣称全站完全无错。

## 验收边界与仍待证明的事项

- 79份原PDF是索引中`indexed`的文件数，当前成功打开/解码的代表性原文和旧gov文书**不等于79个PDF全部逐一解码验收**。另2份档案缺实际原件，163条参考文献中90条无可关联全文，不能伪造。
- 论文40张合法开放授权期刊页图归档，另76份GitHub仓库原PDF不意味着可以向新公众镜像全部受版权限制出版内容；网站不额外转载非授权出版版。
- 视觉审美评价属于可观察的专业布局判断，不是数值式客观通过；移动端宽度和PDF/图片渲染等必须用可重放浏览器断言。
- T093没有创建、运行、调试或派发任何Abaqus/CAE任务；正式论文研究关卡维持原状态。

### 可公开核对的具体工作流

- 第一轮附件：`https://github.com/g2066203208-beep/voxel-frontier/actions/runs/43840135928/artifacts/14214070190`
- 第二轮附件：`https://github.com/g2066203208-beep/voxel-frontier/actions/runs/43847974558/artifacts/14217045313`
- GitHub Code：`public/thesis-studio/full-references.js`、`reader.js`、`math-typeset.js`、`thesis-inline.js`、`styles.css`、`scripts/qa-jiayu-browser.cjs`。

## 最终一轮独立验收：PASS（2026-11-16）

- **生产部署**：`Deploy Paper Studio to Pages` run `43848813144` `SUCCESS`，main `eca7899790d5f1fbefffdd65b83434f10ae33ef9`，网站版本 `v1.9.1`；同源 `Paper Studio CI` run `43848813163` SUCCESS，`Jiayu Research Library QA` run `43848813124` SUCCESS。全部541张已归档原图及395张文献来源页原始字节SHA/长度可溯源。
- **实际Chromium完整浏览器QA**：`Jiayu Academic UI Browser QA` run `43849107797` **SUCCESS**，job `133236757982`；日志明确 `JIAYU_BROWSER_QA_PASS`，不再有PAGE_ERROR。
- 实际源码原件：`L040`原始期刊`Parameter calculation and verification of concrete plastic damage model of ABAQUS`共9页，站内PDF.js真实第一页Canvas渲染成功、全部页数连续占位；原Springer期刊许可图实际PNG解码，Jonscher整页原图实际阅读；主图集541图DOM存在；81PDF/163书目/395来源页未漏项。
- 旧PDF文档切换回归：先嘉鱼政府公文3页（目录/放大/文字阅读），再切换**何泽瑜2024硕士论文真实90页PDF**，明确校验`reader-stage.dataset.documentId=he-thesis`、真实90页计数、成功解码画布后才拍照。旧行政文书残留/空节点BUG修复生效，避免再把他文页面误写为何泽瑜原文。
- **手机端**：Chromium `390×844`对首页、`#literature`、`#thesis`、`#evidence`截图并检查document横向溢出不超过7px，全部通过；网站自托管KaTeX工程公式存在浏览器实际`.katex`渲染节点、非仅静态CSS声明。
- **截图实物**：QA run `43849107797` artifact `14216317869`共14张PNG，已使用GitHub artifact下载在当前会话容器并实际目视复核，包括`jiayu-81-archived-papers-inline.png`（原文9页PDF真实第一页）、`jiayu-reader-desktop.png`（湖南大学何泽瑜90页原论文真实封面）、`jiayu-literature-mobile.png`、`jiayu-thesis-mobile.png`、`jiayu-evidence-mobile.png`、ERA5/ESM及40页授权刊物截图。PDF源码属于原作者文献，不伪造新测试图片。
- **结论分级**：以上构成具有截图与自动断言的**典型完整工作流可用性验收PASS**。不等于79份独立原PDF逐份/逐页在全部浏览器及网速下100%验证；2份受限档案仍无PDF、163书目中90条无可关联全文、气象/地震真实科学证据HOLD仍存在。不能将学术网站的体验测试当作整塔计算或论文送审完成。

**本期网站T093视觉功能回归结果：PASS（Chromium桌面1440×900＋手机390×844，14张实际截图）；全量79份每个PDF逐一打开和跨浏览器测试：NOT RUN。**
