# T049 — 原始 RHOOP 环向钢筋闭合审计

状态：**EXTRACTOR READY / NATIVE ABAQUS RE-RUN REQUIRED**

目标：不把“原 CAE 有 RHOOP”等同于“RHOOP 正确”。对原始 CAE 逐段提取并验证：

- 31 个 RHOOP Part；
- 每个 Part 的节点/单元数量与 T3D2 类型；
- `SEC_REBAR_HOOP` 的 section class、面积、等效直径、材料；
- 每个闭合环的平均标高和平均半径；
- 相邻环竖向间距；
- assembly instance 抑制状态；
- 若存在，RHOOP 对应 EmbeddedRegion 与 host；
- 源 CAE 运行前后 SHA256 不变。

已由 T038 原生审计冻结的事实：
- 每模型 31 个 RHOOP Part；
- 合计 32712 个 T3D2；
- 截面名 `SEC_REBAR_HOOP`，材料 S345；
- 对应 31 个装配实例全部 suppressed，因此当前装配有效 RHOOP 单元为 0。

这说明**环筋资产真实存在，但当前活动装配没有使用它们**。T049 的目的就是继续回答“它们的截面积、直径、间距、位置与 Embedded 是否正确”。

## 运行

在安装 Abaqus 的机器上创建配置：

```json
{
  "source_cae": "D:/MC/DTU158_Hoop_Repair_20260909/DTU158_Hoop_Repair.cae",
  "output": "D:/Codex-research-native/t049-rhoop/rhoop-details.json"
}
```

然后：

```text
abaqus cae noGUI=extract_rhoop_details.py -- config.json
```

脚本不调用 save、writeInput 或 submit。

## 通过标准

原 RHOOP 只有在以下全部通过后才能进入正式模型：

1. section 面积/等效直径可解释且与材料身份一致；
2. 环筋全部位于混凝土壁厚内；
3. 保护层、最大间距、最小配筋率满足采用的规范；
4. 内外层拓扑与纵筋钢筋网关系正确；
5. Embedded host 正确、无重复约束；
6. 恢复实例后 Abaqus data check、Gravity、PT 平衡与 Modal 通过；
7. 总质量/反力/低阶频率相对复现基线变化可解释。

未通过前不得写“原 CAE 环筋正确”。
