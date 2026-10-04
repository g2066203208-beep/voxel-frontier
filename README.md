# 论文工作室 · Paper Studio

一个在浏览器中使用的科研工作台，把论文写作、论文审查、研究复盘、实验记录、执行步骤、模型文件、数据与参考文献放在同一个项目里。

**在线工作台：** [打开论文工作室](https://g2066203208-beep.github.io/voxel-frontier/)

## 功能

- **论文**：组织标题、摘要与正文，记录写作进度。
- **审查**：记录问题、意见与处理状态，跟踪修订。
- **复盘**：保存研究结论、不足与下一步计划。
- **实验**：记录实验目的、方法、参数、结果与观察。
- **步骤**：拆解研究任务，维护执行顺序与完成状态。
- **模型**：保存模型说明和相关附件。
- **数据**：导入 CSV，查看和整理表格数据。
- **参考文献**：管理文献信息并导入、导出 BibTeX。
- **项目备份**：以 JSON 导出项目及附件，也可导入备份恢复工作。

## 数据保存与使用边界

这是一个静态前端应用。记录保存在当前浏览器的 `localStorage`，附件保存在 `IndexedDB`。数据跟随浏览器配置文件和网站地址，不会自动上传到 GitHub，也不会在不同设备之间自动同步。清除网站数据或使用其他浏览器会影响本地记录；请定期导出项目备份。

正式研究流程与工程输入由GitHub管理：[MASTER科研总流程](research/wind-tower/workflow/MASTER_RESEARCH_PROTOCOL.md)。首页进入正式研究区；原有项目模块是浏览器草稿，不能误认为已同步GitHub。

工程模型区显示由GitHub Actions实际读取STEP生成的三维装配，支持部件选择/隔离、线框、PNG出图及CAE审计元数据查看。当前STEP单位存在冲突，页面明确警告。没有执行有限元求解、完整CAE二进制解码或CAE修改，不会自动验证科学结论。

## 本地运行

需要 Node.js 22 和 npm。

```sh
npm ci
git lfs pull --include="research/wind-tower/geometry/*.step"
node scripts/read-model.cjs
npm run dev
```

开发服务器会输出本地访问地址。生产构建与检查：

```sh
npm test
npm run build
npm run preview
```

`npm run build` 会先检查 TypeScript，再输出静态站点到 `dist/`。

## 部署

GitHub Actions 对提交和 Pull Request 运行测试与构建。推送到 `main` 后，Pages 工作流会再次验证项目并发布 `dist/`。也可在 Actions 中手动执行 Pages 工作流。

当前站点部署在仓库子路径 `/voxel-frontier/`，因此 Vite 的 `base` 与该路径一致。更改仓库名称或改用独立域名时，需要同时修改 `base`、站点链接和 Pages 设置。

## 项目结构

```text
src/                    工作台界面、数据存储与测试
public/                 公开静态资源
.github/workflows/      CI 检查与 GitHub Pages 部署
index.html              站点入口
PROJECT.md              产品范围与后续方向
```

仓库当前源码已改为论文工作室。仓库路径沿用现有地址，便于继续使用已连接的 GitHub Pages。
