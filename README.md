# Longcycle Core

行业周期研究平台的数据库与采集内核。当前版本只做后端：保存可追溯原文、事实断言、历史版本、产能项目、行业事件、公司敞口和采集运行状态；网页端不在本仓库范围内。

## 已实现的边界

- PostgreSQL 16+ 的四层数据模型：`core`、`evidence`、`research`、`ops`。
- S3/R2/MinIO 或本地文件系统的 SHA-256 内容寻址原文库。
- 可插拔 `SourcePlugin`、`ModelGateway`、Repository、Queue、Checkpoint 和 EventSink。
- 本地文件与受限 HTTP 采集源；HTTP 源具备域名白名单、重定向复查、响应体上限和基础 SSRF 防护。
- 原文归档 → 证据片段 → 抽取运行 → 原子断言 → 质量评分 → 冲突/复核 → 可信事实版本的完整链路。
- 解析产物具有独立的 producer/version/input hash/content hash 血缘；结构化证据必须引用已持久化解析产物。
- 数据库驱动的 predicate、维度 schema、单位换算与分 predicate 调和策略快照；规则指纹进入处理版本。
- 同一事实键下“读取可信基线 → 调和 → 保存 evaluation”原子串行，避免并发冲突值双双发布。
- 带租约、心跳、重试、死信、断点和确定性 fan-out 的 PostgreSQL 任务执行骨架。
- 动态频率：行业热度与数据风险共同决定每日、每三日或每周采集，并带降频迟滞与事件覆盖。
- 价格、产能、产量、项目、事件、上市公司收入/利润/成本/产能敞口、上下游关系和周期快照的数据库结构。

当前还没有生产 AI 连接器、通用 PDF/OCR/Excel 解析器、语义目录热更新/部署装配、默认全阶段 handler 装配、对外 API 或网页。`JsonFixtureGateway` 是离线黄金测试适配器，不是生产模型。

## 结构

```text
migrations/                   PostgreSQL 迁移；数据库是真实结构化数据源
src/longcycle/domain/         不可变领域对象与枚举
src/longcycle/ports/          可替换端口契约
src/longcycle/application/    采集、归一、调和、调度、Worker、工作流
src/longcycle/adapters/       HTTP/本地源、PostgreSQL、S3/文件、测试模型
docs/                         架构、Schema 契约、采集 SDK、运维说明
tests/                        无网络确定性测试
```

```text
来源发现
  → 获取并归档原始字节
  → 解析/抽取候选
  → 绑定证据与版本
  → 归一产品规格、地区、价格口径、单位和时间
  → 质量评分与独立信源调和
  → 可信事实/冲突/人工复核
  → 指标序列、产能管线、事件影响、公司敞口、周期快照
```

## 本地快速验证

要求 Python 3.11+：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
longcycle doctor
longcycle source plugins
longcycle demo
python -m unittest discover -s tests -v
```

`longcycle demo` 完全离线，运行一条本地 JSON → 原文归档 → 事实抽取 → 归一 → 调和链路。

## PostgreSQL 与对象存储

开发环境可复制 `.env.example`，然后启动基础设施：

```powershell
Copy-Item .env.example .env
docker compose up -d postgres minio minio-init
docker compose run --rm migrate
```

或直接连接已有 PostgreSQL 16+：

```powershell
$env:LONGCYCLE_DATABASE_URL='postgresql://longcycle:longcycle@localhost:5432/longcycle'
pip install -e ".[postgres,s3]"
longcycle db upgrade
longcycle doctor --check-database
longcycle scheduler-tick
```

迁移使用会话级 advisory lock、逐文件事务和 SHA-256 校验；已应用迁移被修改时会拒绝继续。迁移角色需要创建 `pgcrypto`、`btree_gist`、`pg_trgm` 扩展的权限。

`compose.yaml` 只用于本地开发，并未在本工作区运行验证，因为当前环境没有 Docker。生产环境应固定镜像 digest，使用托管 PostgreSQL 的 PITR、对象锁/版本控制和独立凭证管理。

## 关键设计原则

1. AI 只能写候选断言，不能直接写可信事实。
2. 每条可信事实都能回溯到归档原文、精确 locator、抽取器、prompt/schema/model 版本。
3. 同一主体、predicate 和可比维度形成事实键；有效时间决定比较范围，不被混入维度哈希。
4. 现货、长协、含税/未税、到厂/出厂、地区、规格和币种不完整时，不自动互证或判冲突。
5. 原始产能、名义产能、有效产能、产量和利用率是不同指标。
6. 来源断言和系统采用结论分别保存；修订追加版本，不覆盖历史。
7. Queue 是至少一次语义，所有 handler 和外部副作用必须幂等。

## 文档入口

- [总体架构](docs/architecture.md)
- [Schema 与时间契约](docs/schema-contracts.md)
- [采集插件 SDK](docs/collector-sdk.md)
- [运行、成本与安全](docs/operations.md)

## 当前验收

无需网络或数据库即可运行的单元测试覆盖：内容寻址归档、来源安全、断言归一与可比性、冲突分流、同文档不同目标抽取、队列租约与死信、Worker 并发、断点重放和 Outbox 幂等。

真实 PostgreSQL/S3 集成测试需要在具备相应服务的环境中执行；不能用当前纯内存测试替代上线前的并发、故障注入、备份恢复和对象一致性演练。
