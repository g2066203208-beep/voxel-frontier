# T026 实际材料与预应力实施核验研究卡

所有算例登记后再提交。原始模型只读；这些单元/筋算例是 numerical verification，不是10MW机组物理标定。源输入 SHA256：2098a8cb08bfb9e12c9b2ec0dd8861317c7bcd3b3dc0603f39ab35f91e896e23。

依据：Abaqus 2025 CDP、Initial Conditions、truss 官方理论。具体改变变量、解析参考和预登记诊断判据见 run-manifest.json；所有数值判据只管本算例实施精度，不能推广为论文物理误差容许值。

固定项：源 C65/C70 内嵌表（未改为Li再生曲线）；SI 单位；均匀单轴自由侧向试件；真实PT E/A/L/初始应力；所有失败保留并新建RUN补救。材料加载伪时间1s、单调段0–0.8s、最大增量0.002s，0.8–1s卸载重载。初应力为generic STRESS，不使用REBAR/HOLD。

输出：输入/版本/hash、solver日志、ODB、RF/S/U/E/damage/energy CSV和图；反力平衡、目标包络和卸载关系、中心差分h/h2。超预算：先查约束/变量/伪时间/增量，再独立补算；不调材料来拟合正文频率。
