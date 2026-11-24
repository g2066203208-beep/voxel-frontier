# REV13 双水平地震试算
母本REV11；实际目标SHA256 7a56d8f7bfc059434f57dc4ddb99961e2ea1f41176b6aff27e587ad4fcd1f8d2，34232781 bytes，9处差异，补丁Git blob与本地逐字节一致。旧版本保留，latest仍REV11。

- ESM v3 IT-2012-0008/NVL/MP，Actions artifact 12884814391：实际归档原ZIP ad370abe14e308856754456e5bf172bb327ca59cb002344e2937726c14fec2b7，旧摘要另一次ZIP哈希不同，实际归档自身收据一致，三个规范化数值SHA256与既有来源一致；处理CSV a353c1216b80cf2739b9cedfbd09b68bab3d3ffe49f1d6f3b537366c3559db34；两水平64080值逐点完全匹配，未缩放，X=HNE，Z=-HNN，Y上，场址及方位未验。
- 0.005s采样、160.195s、峰值0.47522846/0.51205727m/s²；最大积分步0.005s；塔底及PT下锚同步加速度，Y固定，初速0；原先4步不变，新增EQ步；CDP默认拉/压恢复0/1显式化；无Rayleigh，接触数值稳定仅原PT步。
- 103部件，318647定义节点，421713定义单元，节点连接和材料引用检查通过；30 contact、62 embedded、5 tie；混凝土硬化损伤表换算塑性应变非负递增；几何不变，增加2个输出探针；反向补丁重建一致。未执行原生求解，未验收材料参数、断裂能、网格、预应力数量、法兰/接缝、阻尼、场址设计地震或风外载。18条风响应幅值保留但不激活。
- Abaqus 2025官方：*BOUNDARY、*DYNAMIC、*INITIAL CONDITIONS、*CONTACT CONTROLS、*CONCRETE COMPRESSION DAMAGE、*CONCRETE TENSION DAMAGE、*OUTPUT。详细记录在研究白皮书。云备份接口本轮失败；工作室可按已归档REV11和精确补丁恢复完整文件并校验SHA256。
