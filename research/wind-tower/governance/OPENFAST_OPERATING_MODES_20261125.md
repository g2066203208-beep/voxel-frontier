# OpenFAST DTU158运行模态研究 V1.0

## 目标
以真实归档的158 m R2整机输入为基础，独立计算停机无风及运行状态线性化模型；完成原生 .lin 文件、MBC3状态矩阵及未跟踪的频率/总阻尼提取。不是最新REV22、不是ROSCO闭环线性化、不是已分离的气动阻尼。

## 源与方法
- 原始17文件逐一SHA-256核验：public/thesis-studio/wind-figures/blade-aero。
- 官方OpenFAST v3.5.3求解器及既有二进制哈希门禁。
- 运行点来源：仓库 research/wind-tower/references/baselines-and-site-20261004/openfast-v330-adaptation/0Linearization/LinearizationPoints_Servo.csv；历史DTU参考转速、桨距及转矩仅作为初始参考，不当作158 m机组已验证运行结果。
- 0 m/s：静止、无气动/入流/伺服、发电机自由度锁定；不等于有风停机或顺桨状态。
- 7、10、14 m/s：均匀风，保留R2 RNA柔性和塔架自由度；采用参考简单变速转矩控制，非ROSCO闭环；BEM冻结尾流，定常翼型气动。
- CalcSteady=True，TrimTol=0.001；参考低于额定转矩修整、较高风速桨距修整；36个旋转方位点。零转速1点。
- MBC3官方工具 https://github.com/OpenFAST/python-toolbox 固定09596209e4160c44d43ec1b702994ca1820ebae1。
- 输出原生.lin、输入、日志、MBC状态矩阵、未跟踪模态CSV；运行点转速误差门限1%。保留失败证据。
- 依据：https://openfast.readthedocs.io/en/v3.5.3/source/working.html 。

## 门禁与后续
1. 四组原生线性化及MBC3数值门禁，未执行不得称完成。
2. 校核实际周期稳态、方位覆盖、状态描述、模态振型和MAC/参与度跟踪，再扩展4、9.343881、11.4、19.202140、20m/s等合理运行点（不得把历史最大小时风速称作认证极端风）。
3. 对一致状态和模态做气动反馈开关或有依据的扰动识别、分离结构/气动/控制阻尼；本轮总阻尼不等于气动阻尼。
4. 另做真实ROSCO时域均匀风性能曲线，控制线性化采用可追溯的线性化策略；不可将简单控制替代模型称为ROSCO。
5. 匹配REV22质量、刚度、模态、RNA质量惯量及实际荷载接口；本轮不改Abaqus。
6. 禁止未经验证发布Campbell曲线；失败保留并按日志修复。
当前版本：工作流已提交，尚未通过求解验证。