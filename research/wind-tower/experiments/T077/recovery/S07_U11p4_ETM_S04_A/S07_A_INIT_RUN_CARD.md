# S07 U11p4_ETM_S04 A批｜SHA锁定装配与最小初始化RUN卡（未授权执行）

**状态：PREPARED / NOT_EXECUTED。** 仅用于验证历史T072输入是否能够由原生OpenFAST初始化；不属于DLC1.2正式风载、31站完整时程、Abaqus外载或任何物理PASS。禁止在本卡下启动700s生产计算。来源为已归档三ZIP、A批ElastoDyn、控制器DLL、437MB真实BTS与61MB真实EXE；输入图见`S07_A_RUNTIME_DEPENDENCY_RECEIPT.json`。脚本`../s07_a_runtime_dependency_gate.py`只装配，不执行求解器。

## SOURCE / REF / STANDARD / OFFICIAL / RUN / FIG / TAB

- **SOURCE（直接原件与历史实证分开）：** ZIP SHA256：part-001 `ddfa02734274ad5bd36e84d975d18544bb5360554e25d71d8689f32313a95267`；part-002 `5100b6b255e1706874feac95d6d967c7625b53536efac26d77719d56db63d71a`；supplement `c8d8201f97025729634b3f6a97076524c4329179693a97778456e6e7201477b0`。A批ED `701a3e30bc058d97c673e28947307066a245c276cb10042a1eb3ca133c571833`。BTS `9f138ad2065efb791352a6e5a242b03e06e731fb68176bf9f6cbca98c9888c78`（436,968,166字节，前次真实LFS核验）；exe `0cc8147fdda188365b8eacda8a831e74fafef59440d71185d66c3272af9e176a`（61,086,208字节，前次真实核验）。**本卡未重新下载二者。**
- **REF：** T071/T072历史Windows OpenFAST输入；版本v3.5.3目前仅历史标签，尚待原生版本输出。
- **STANDARD：** 本轮没有新增授权IEC/GB/NB原文阅读，绝不称条款通过。
- **OFFICIAL：** 原始归档、T072工作流及PE x64身份，不等于OpenFAST官方发行包身份或DLL ABI验证。
- **RUN：** 本卡实际OpenFAST/Abaqus运行数均为**0**；只在未来得到独立批准、资源和原生环境时执行下面的初始化命令。
- **FIG/TAB：** 无响应图；预计可达17个原始模块、诊断FST一件、BTS一件、exe一件，装配成功后由`S07_A_ASSEMBLY_RECEIPT.json`逐件给出实际字节与SHA。不能用预计数冒充已装配数。
- **误差预算：** 装配输入身份采用精确SHA256；路径为T072 Windows语义；物理数值误差未定义，必须在原生初始化及后续V&V后建立。
- **HOLD：** 原生启动/控制器ABI、31站OUTB、同刻RP/TP/DCM、签名自由体、材料疲劳与抗震验算均未验收。

## 1. 只装配（无RUN）

在独立Windows工作目录，提供下列已实际存在的**原件字节**路径；缺任一项必须停止，不允许将Git LFS指针冒充BTS/exe。运行脚本时用`--assemble-dir`指定**尚不存在**的输出目录，拒绝覆盖。示意命令（将路径替换为实际路径）：

```powershell
$root = "D:\\S07-A-DIAGNOSTIC"
$py = "s07_a_runtime_dependency_gate.py"
python $py --selftest
python $py --base-zip "part-001.zip" --target-zip "part-002.zip" --supp-zip "supplement-part-001.zip" `
  --child-ed "DTU_10MW_RWT_ElastoDyn.dat" --dll "libdiscon.dll" `
  --exe "openfast_x64_v353.exe" --prior-manifest "S07_A_REAL_BUNDLE_IDENTITY.json" `
  --bts "U11p4_ETM_S04.bts" --assemble-dir "$root"
```

脚本应在`$root/CASES/U11p4_ETM_S04`保留原FST，另生成**仅TMax=0.1s**的`DTU_10MW_RWT_INIT_DIAG.fst`；全部可达模块及BTS、exe以SHA锁定装配，原文件不被修改。装配后回读`S07_A_ASSEMBLY_RECEIPT.json`，核对`RUN.executed=false`、每件文件SHA与源文件一致；Windows-only AeroDyn翼型大小写差异仍须登记，Linux不直接执行。

## 2. 最小初始化（本轮禁止执行，仅待独立授权）

**预设资源上限：** 1个工况×A批、2逻辑CPU、内存4GiB、墙钟180s、诊断输出合计不超过1GiB；无并发、无完整700s时程、不得提交原始大OUTB到普通Git。Windows PowerShell中从`$root/CASES/U11p4_ETM_S04`运行已SHA验证的exe，参数为`DTU_10MW_RWT_INIT_DIAG.fst`；启动前另行核对OpenFAST版本横幅、DLL加载、初始时间步、FST与ED源SHA和风场路径。**不得在此研究自动化中执行这条命令。**

原生执行须在独立目录记录实际命令、起止时刻、进程退出码、标准输出/错误、OpenFAST横幅、`.sum`、`.outb`或失败日志、各文件SHA；超时/资源越界/非零退出立即终止并保存失败，不扩大到B/C/D批。若0.1s诊断不能覆盖需要验证的初始化/控制器状态，应先说明局限，不能擅自延长至生产时长。

## 3. 后续真正验收

仅当原生初始化通过且模型/控制器/风场身份与历史T071/T072一致，才考虑一次**单工况A批**受控补采；补采必须长期保存真实OUTB并与已有31段六分量逐点对齐。随后继续S07的RP/TP/DCM、载荷所有权与自由体闭合；不能直接将OpenFAST截面内力当作Abaqus外载。当前S07整阶段HOLD，S10分材料疲劳与S11优化主线不变。
