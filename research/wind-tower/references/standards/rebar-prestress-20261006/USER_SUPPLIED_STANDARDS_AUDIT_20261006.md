# User-supplied standards intake audit — 2026-10-06

This note records the five files supplied in chat for the wind-tower reinforcement/prestress standards library.

| File supplied | Size | SHA256 | Audit status | Decision |
|---|---:|---|---|---|
| 风电机组混凝土—钢混合塔筒设计规范（附条文说明）.pdf | 11,980,695 B | fcf98aee390850e27c22cdf2f3baf40a933a6b21645f787eb16dd2fea6dac18e | VALID, 68 pages, NB/T 10907-2021, includes 条文说明 | Canonical user-supplied copy |
| 风电机组混凝土-钢混合塔筒设计规范.pdf | 13,973,934 B | 1188783ec78412251651b94bd185eea4c882c2f91cd868ff8691f9dda44766a4 | VALID, 59 pages, NB/T 10907-2021, duplicate/alternate scan | Keep as alternate only if binary is archived |
| 风能发电系统 风力发电机组塔架和基础设计要求 (1).pdf | 12,241,402 B | 36c15c3a10f182b8cc3490e6a4753077185cea0a8c01ffcdf6dd9aa16c879484 | VALID, 99 pages, GB/T 42600-2023 / IEC 61400-6:2020 | Canonical user-supplied copy |
| 风能发电系统 风力发电机组塔架和基础设计要求.pdf | 2,536,012 B | 67d966b050887bcce834000644be16f6aa52107162d26a002224b9e19974ae9d | PARTIAL, 32 pages; starts with front matter then jumps to selected later appendices | Do not use as canonical full text |
| 预应力混凝土用钢绞线.pdf | 163 B | f155dc572ad04ac9ec2fc8eece7a77e79bf112f4fb60acbb16e0fdfe0f9553f7 | INVALID — not a PDF; body is a 404 JSON response pointing to /api/download/pc/standard/GB/T%205224-2014 | User must redownload GB/T 5224-2023 |

## Evidence confirmed from the supplied NB/T 10907-2021

- Cover identifies **NB/T 10907-2021 风电机组混凝土—钢混合塔筒设计规范**, issued 2021-12-22 and implemented 2022-03-22.
- Chapter 4 is **Materials** and 4.2 is **Steel Reinforcement**.
- Table 4.2.1-1 lists ordinary reinforcement grades including HPB300, HRB400/HRBF400/RRB400 and HRB500/HRBF500.
- Table 4.2.1-2 lists prestressing reinforcement characteristic strengths.
- Chapter 8 gives detailing requirements; Table 8.0.11 gives minimum reinforcement ratios for longitudinal and circumferential reinforcement.
- This standard therefore becomes the primary dedicated standard for the tower reinforcement audit.

## Evidence confirmed from the supplied GB/T 42600-2023

- Cover identifies **GB/T 42600-2023 / IEC 61400-6:2020**, 风能发电系统 风力发电机组塔架和基础设计要求.
- The 99-page copy is the complete user-supplied copy and includes the concrete tower/foundation clauses and annexes.
- The 32-page copy is not complete and must not be cited as a full-text source.

## Open item

**GB/T 5224-2023《预应力混凝土用钢绞线》 full PDF is still missing.** The supplied file is an HTTP 404 body, not a PDF.
