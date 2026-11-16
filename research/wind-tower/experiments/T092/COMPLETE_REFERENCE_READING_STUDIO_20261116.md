# T092｜唯一论文工作室所有已归档文献原文一页一页完整阅读

**发布日期：2026-11-16，范围：网站科研资料展示（不新增任何Abaqus求解或研究物理结果）。**

## 逐条盘点：不是只有几篇

| 口径 | 已源级确认 | 是否等于完整原文 |
|---|---:|---|
| `public/thesis-studio/data/reference-index.json` PDF档案记录 | 81份 | 其中79份标注indexed、已有文件URL；2份restricted（规范元数据、LFS指针）没有实际可读原文件 |
| 同上主参考文献书目 `master` | 163条 | 只有73条标记 `accessible`；90条不能擅自称“全文在GitHub” |
| 同上已归档文献原始截图 `images` | 395张 | 来自资料原页，**不是395篇论文全文**，且已计入541张原图 |
| 原始图库 `figure-index.json` | 541张 | 含395张来源页和146张其他研究图 |
| `inline-atlas.json` 水平接缝特定竞争文献 | 24条 | 全文取得与合法重发情况须逐篇核对；24≠已全文归档 |
| `development-paper-pages.json` 已确认CC BY4.0期刊整页PDF | 2篇/40页 | Jonscher2023 18页、Dong2025 22页，是真实的整页截图 |
| `reference-index.json` 来源类型 | 30用户提供、46开放获取、4场址及官方、1标准 | 文件目录来源标记，不能代替完整版权逐份审核 |

## 已在main网站实现

- 网站 **v1.9.0** 唯一研究入口 `https://g2066203208-beep.github.io/voxel-frontier/thesis-studio/#literature`。
- 新 `public/thesis-studio/full-references.js` 从现有原始索引直接生成81份PDF全列表、163条文献无分页完整索引、395张文献原图连续直接显示；搜REF、作者、DOI、题目、主题和来源。**没有把缺失的90篇伪装为已归档全文**。
- 已存在的79份PDF使用现有本地 `pdfjs-dist@5.4.530`，用户直接点击`站内阅读全文`后同页读取原GitHub已归档PDF；按原始PDF `numPages`生成所有页面占位并由IntersectionObserver进入视口时渲染真实页。第1页、第2页直到最后一页均可在网页内按页阅读，最多保留9页画布，防止长论文一次耗尽浏览器内存。无原文下载控件、无新版权文件镜像。
- 源图40页与24篇专题资料、六章论文、ERA5/地震/风载资料继承保留。首页增加文献全集的81/163/395/40真实统计以及同页入口。
- 这只是**原始文件索引级**的79份“有URL”。对单份的物理PDF字节、浏览器/CORS/源服务器可用性不能仅凭目录数宣称全部已实际打开，须通过GitHub Actions Playwright对代表性授权PDF真页 `L040` 的`PDF.js`光栅化判定。
- 此次新增 `scripts/qa-jiayu-browser.cjs` 断言 81个书架原件、79个原文按钮、163条书目、395张来源页、无新外部链接/下载、L040真实PDF第一页生成canvas且每页存在连续占位；不改变旧3份PDF阅读器和541图。

## 仍然缺少、不允许谎称完整的材料

- 163条文献中未找到对应真实PDF的90条仅完整保留作者/题目/DOI与可用性；如版权或开放许可不允许，不得上传全文截图。
- 2条restricted档案缺少真正可直接读取PDF；已标注`元数据`或`Git LFS指针`。
- 对非开放许可的第三方论文**没有额外复制PDF、制作新增整篇截图或绕过付费墙**；只在原已有归档文件位置提供阅读界面。
- 仍然是历史网页证据装配，没有新增模型物理验证成果：新接触全塔、地震正式场址波和材料疲劳仍按T091的原状态HOLD。

## 源级追溯

- 81/79/2、163/73及395数值来自 `public/thesis-studio/data/reference-index.json`。
- 541源图来自 `public/thesis-studio/data/figure-index.json`；24专题条目来自 `public/thesis-studio/data/inline-atlas.json`；40合法完整页图来自 `public/thesis-studio/data/development-paper-pages.json`。
- 最终Pages部署与Playwright UI验收需以最新GitHub Actions回执复核，源码已提交不自动等于全部浏览器可见性通过。
