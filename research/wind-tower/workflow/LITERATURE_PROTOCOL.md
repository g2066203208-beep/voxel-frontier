# LITERATURE PROTOCOL — 文献检索、下载、阅读与证据提取

本文件规定“找文献”不是搜标题，而是一个可复核过程。

## 1. 检索计划必须预先登记
每个主题登记：
- question_id
- concept groups
- 英文关键词
- 中文关键词
- 时间范围
- 数据库
- 纳入/排除标准
- 最新检索日期

## 2. 核心检索式模板

### Hybrid tower / joint
("wind turbine" AND ("hybrid tower" OR "concrete-steel tower" OR "prestressed concrete tower") AND (joint OR segment* OR prestress* OR transition))

### dynamics / RNA
("wind turbine tower" AND ("rotor nacelle assembly" OR RNA OR "top mass" OR inertia OR eccentric*) AND (modal OR dynamic*))

### OpenFAST validation
(OpenFAST AND validation AND (onshore OR turbine) AND (load* OR modal OR fatigue))

### load transfer / FE
("wind turbine" AND (load mapping OR "load transfer" OR interface) AND (finite element OR Abaqus))

### fatigue
("wind turbine tower" AND (fatigue OR rainflow OR "damage equivalent load" OR S-N) AND (concrete OR prestress* OR hybrid))

### optimization
("hybrid wind turbine tower" AND (optimization OR sensitivity OR surrogate OR NSGA OR Morris OR Kriging))

## 3. 下载规则
优先：
1. publisher OA PDF；
2. institutional repository/AAM；
3. author repository；
4. school database合法下载。

每份PDF记录：
- ref_id
- title
- DOI
- version
- source_url
- license
- sha256
- pages
- acquired_date

不成功：进入NEED_USER_DOWNLOAD。

## 4. 阅读层级
- Screening：标题/摘要判断相关性；
- Core read：全文方法、对象、结果、局限；
- Formula read：逐式；
- Reproduction read：输入、边界、步骤和验证可复现。

## 5. 文献提取模板
每篇核心文献输出：
1. Bibliography
2. Research question
3. Object
4. Model/experiment
5. Geometry/material
6. Boundary
7. Loads/wind
8. Software/version
9. Parameters
10. Verification
11. Validation
12. QoI
13. Results
14. Limitations
15. Applicable-to-us
16. Not-applicable-to-us
17. Exact page/section/figure/table/equation
18. Claims supported

## 6. 研究缺口规则
禁止从单篇论文的limitations直接写“本文创新”。
必须对同主题核心文献群建立：
- 已解决；
- 未解决；
- 对象差异；
- 方法差异；
- 数据/验证差异；
- 本文真正能回答的新增问题。

## 7. 第一章写作规则
每个综述段：
问题 → 代表方法 → 证据 → 局限 → 本文承接。
禁止“某某研究了…某某又研究了…”流水账。
