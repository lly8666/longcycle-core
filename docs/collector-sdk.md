# Longcycle Collector SDK

本文面向采集源和抽取适配器的开发者，说明如何在不修改核心流水线的情况下扩展 `longcycle-core`。示例代码展示扩展方式，不代表示例插件已经包含在项目中。

## 1. 安装与开发环境

核心包要求 Python 3.11 以上：

```bash
pip install -e .
pip install -e ".[dev]"
```

使用 PostgreSQL 或 S3/R2 时分别安装：

```bash
pip install -e ".[postgres]"
pip install -e ".[s3]"
```

## 2. SourcePlugin 最小协议

所有来源插件都实现 `longcycle.ports.source.SourcePlugin`：

```python
from collections.abc import AsyncIterator

from longcycle.domain.models import DiscoveryItem, RawPayload
from longcycle.ports.source import DiscoveryContext, FetchContext


class SourcePlugin(Protocol):
    plugin_name: str

    async def discover(
        self,
        context: DiscoveryContext,
    ) -> AsyncIterator[DiscoveryItem]: ...

    async def fetch(
        self,
        item: DiscoveryItem,
        context: FetchContext,
    ) -> RawPayload: ...
```

插件工厂的实际约定是：构造函数接收一个 `SourceDefinition`，返回插件实例。类本身可以直接作为工厂注册。

### `SourceDefinition`

来源定义包含：

- `id`：稳定 UUID；
- `name`；
- `kind`：监管、交易所、公司、协会、政府、数据商、新闻、研究或人工来源；
- `plugin`：注册表中的插件名；
- `quality_grade`：A/B/C/D；
- `publisher_domain`；
- `rate_limit_per_minute`；
- `enabled`；
- `config`：插件专属配置；
- `syndication_cluster`：转载/独立来源簇。

`rate_limit_per_minute` 当前只是配置字段，核心代码尚未提供统一限流器。需要联网的插件必须自行遵守来源限制，或由部署层包装限流。

### `DiscoveryContext`

发现上下文可以带行业、起始时间、来源游标和任意参数：

```python
DiscoveryContext(
    source=definition,
    industry_id=industry_id,
    since=last_success_at,
    cursor={"page": 4},
    parameters={"report_type": "monthly"},
)
```

插件可以忽略不适用的字段，但不得修改上下文。

### `DiscoveryItem`

发现项至少需要：

- `source_id`；
- `url`。

强烈建议提供来源侧稳定的 `external_id`。当前 `DiscoveryItem.idempotency_key` 为：

```text
sha256(source_id | external_id-or-url)
```

可选字段包括标题提示、发布时间提示、关联行业和来源元数据。发现只应返回候选，不应下载大正文、写数据库或调用 AI。

### `FetchContext` 与 `RawPayload`

`FetchContext` 提供：

- `source`；
- 超时，默认 30 秒；
- 最大正文大小，默认 50 MiB；
- 条件请求头。

`fetch()` 返回的 `RawPayload` 保存字节、MIME、最终规范 URL、HTTP 状态、响应头和 UTC 获取时间。其 `sha256` 属性由正文字节计算。

插件应确保：

1. `canonical_url` 对同一逻辑资源保持稳定。
2. 在内存无限增长前执行 `maximum_bytes`。
3. 使用 `timeout_seconds`。
4. 不把身份凭证写入 URL、metadata 或日志。
5. 对所有跳转目标重新执行 allowlist 和 SSRF 检查。
6. 不在插件内部做无界重试；重试由 Job Worker 管理。

## 3. 一个文件清单插件示例

下面的示例读取配置根目录中的 `manifest.json`，再获取清单列出的本地文件。它演示协议和路径安全，尚未包含在项目中：

```python
from __future__ import annotations

import json
import mimetypes
from collections.abc import AsyncIterator
from pathlib import Path

from longcycle.domain.models import (
    DiscoveryItem,
    RawPayload,
    SourceDefinition,
)
from longcycle.ports.source import DiscoveryContext, FetchContext


class ManifestFolderSource:
    plugin_name = "manifest_folder"

    def __init__(self, definition: SourceDefinition) -> None:
        self.definition = definition
        self.root = Path(str(definition.config["root"])).expanduser().resolve()
        self.manifest = (self.root / "manifest.json").resolve()
        if not self.manifest.is_relative_to(self.root):
            raise ValueError("manifest escapes configured root")

    async def discover(
        self,
        context: DiscoveryContext,
    ) -> AsyncIterator[DiscoveryItem]:
        rows = json.loads(self.manifest.read_text(encoding="utf-8"))
        for row in rows:
            relative_path = str(row["path"])
            path = (self.root / relative_path).resolve()
            if not path.is_relative_to(self.root) or not path.is_file():
                continue
            yield DiscoveryItem(
                source_id=context.source.id,
                external_id=relative_path.replace("\\", "/"),
                url=path.as_uri(),
                title_hint=row.get("title") or path.name,
                industry_ids=(context.industry_id,) if context.industry_id else (),
                metadata={"file_path": str(path)},
            )

    async def fetch(
        self,
        item: DiscoveryItem,
        context: FetchContext,
    ) -> RawPayload:
        raw_path = item.metadata.get("file_path")
        if not isinstance(raw_path, str):
            raise ValueError("discovery item has no file_path")
        path = Path(raw_path).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError("path escapes configured root")
        if path.stat().st_size > context.maximum_bytes:
            raise ValueError("file exceeds maximum_bytes")
        content = path.read_bytes()
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        return RawPayload(
            content=content,
            content_type=content_type,
            canonical_url=item.url,
        )
```

真实联网插件可参考内置 `HttpDocumentSource` 的安全行为：HTTP(S) 限定、URL 规范化、域名 allowlist、公共 IP 校验、每次跳转复查、响应体上限和禁用自动跳转。不要直接复制一个不带这些检查的普通 `httpx.get()`。

## 4. 注册插件

### 4.1 包内或测试注册

```python
from longcycle.adapters.sources.registry import SourceRegistry

registry = SourceRegistry()
registry.register("manifest_folder", ManifestFolderSource)
plugin = registry.create(source_definition)
```

重复注册同名插件会抛出 `ValueError`。

### 4.2 第三方 Python 包 entry point

在插件包的 `pyproject.toml` 中声明：

```toml
[project.entry-points."longcycle.sources"]
manifest_folder = "my_collector.sources:ManifestFolderSource"
```

然后加载：

```python
registry = SourceRegistry()
registry.load_entry_points()
plugin = registry.create(source_definition)
```

entry point 名称必须与 `SourceDefinition.plugin` 一致。当前核心包已经用该机制声明 `local_folder` 和 `http_document`。

可用插件可以通过以下命令查看：

```bash
longcycle source plugins
```

## 5. 直接执行发现与单文档管道

最小调用顺序如下：

```python
plugin = registry.create(source_definition)
context = DiscoveryContext(
    source=source_definition,
    industry_id=industry_id,
)

async for item in plugin.discover(context):
    report = await pipeline.ingest(
        plugin=plugin,
        item=item,
        target=ExtractionTarget(
            industry_ids=(industry_id,),
            predicate_allowlist=(
                "price.market_index",
                "capacity.nameplate",
            ),
            schema_version="fact-v1",
            prompt_version="extract-v1",
            risk_tier="low",
        ),
        fetch_context=FetchContext(source=source_definition),
    )
```

`pipeline.ingest()` 不负责插件发现，也不检查 SourceDefinition 的 `enabled`。生产调用方在投递任务前必须自行过滤禁用来源。

`PipelineReport` 返回文档 ID、内容哈希、是否为新文档、抽取和各分流数量，以及本次抽取声明的微单位成本。

## 6. 编写 DocumentParser

PDF、OCR、HTML 表格和 Excel 解析器实现 `DocumentParser`，只返回一个或多个 `ParsedOutput`，不自行写数据库：

```python
class DocumentParser(Protocol):
    parser_name: str
    parser_version: str
    supported_media_types: frozenset[str]

    async def parse(self, document, content) -> tuple[ParsedOutput, ...]: ...
```

`ArtifactPipeline` 统一核验输入哈希、MIME、输出数量和总字节数，然后将输出写入内容寻址对象库并登记为不可变 `DocumentArtifact`。同一 parser/version/input/artifact type 重放是幂等的；若输出字节改变则拒绝写入。项目内的 `CanonicalJsonParser` 是最小参考实现。

## 7. 编写 ModelGateway

生产抽取器实现：

```python
class ModelGateway(Protocol):
    extractor_name: str
    extractor_version: str
    model_name: str | None

    async def extract(
        self,
        *,
        document: SourceDocument,
        content: bytes,
        target: ExtractionTarget,
    ) -> ExtractionEnvelope: ...
```

Gateway 的职责是把文档变成“证据片段 + 原子断言”，而不是直接生成行业结论。每个候选断言必须：

- 指向当前 `document.id`；
- 引用当前 envelope 中的一个 `EvidenceFragment.id`；
- 使用 envelope 的 `run_id`；
- 使用命名空间字段，例如 `price.market_index`，不能只写 `price`；
- 声明 extractor 名称和版本；
- 提供 `QualityComponents`；
- 有数值时保留原始 `value`，并另填 `normalized_number` 与 `normalized_unit`；
- 明确 `valid_time`、`observed_at` 与 `known_at` 的不同含义。

模型给出的 source quality、corroboration、freshness、entity match 和 completeness 不会被信任；管道会使用持久化来源定义、目标约束和归一结果重新计算。生产 Gateway 应把自身不确定性表达在 `confidence`，不要试图替代来源质量或独立信源判断。

稳定的抽取运行 ID 至少应包含：

```text
document.content_sha256
extractor_name + extractor_version
target.schema_version
target.prompt_version
实际模型/路由版本
```

只有这些版本完全相同时才应复用抽取。改变 prompt、schema、模型路线或解析逻辑时必须改变对应版本。

### 证据片段

使用 `EvidenceFragment.create()` 创建稳定证据：

```python
fragment = EvidenceFragment.create(
    document_id=document.id,
    locator="pdf:page=12,bbox=70,110,510,180",
    excerpt="该项目设计产能为……",
    structured_payload={"table": 3, "row": 8, "column": "设计产能"},
)
```

`locator` 的具体语法尚未由核心枚举约束，但同一 parser 必须保持稳定。建议使用带前缀的格式：

```text
html:css=<selector>#chars=<start>-<end>
pdf:page=<n>,bbox=<x1>,<y1>,<x2>,<y2>
xlsx:sheet=<name>,range=<A1:C4>
json:path=<json-pointer-or-jsonpath>
```

对于 JSON、纯文本、CSV 和 XML，核心管道会检查 excerpt 是否真实出现在原文字符串中，并校验证据 ID/哈希与内容一致。PDF、扫描件和 HTML 的严格 grounding 应由版本化 parser artifact 完成；模型不能用“看起来合理”的摘录替代可回放 locator。

## 8. 归一与断言身份

`AssertionNormalizer` 会从 raw `value` 重算 typed value、解析显式单位，并在换算后生成稳定断言 ID。默认启动规则覆盖吨、千吨、千克、克和百分比等有限单位；生产 Worker 应使用数据库语义快照，而不是为每个行业改代码。

数据库装配示例：

```python
from longcycle.adapters.storage.semantic_catalog import PostgresSemanticCatalog

runtime = await PostgresSemanticCatalog(database_url).load_runtime()
pipeline = CollectionPipeline(
    repository=repository,
    archive=archive,
    model=model,
    normalizer=runtime.normalizer,
    reconciler=runtime.reconciler,
)
```

新增单位必须先进入 `core.units`，换算版本进入 `core.unit_conversion_versions`，predicate 同时声明维度 schema、允许值类型、规范单位和调和 policy。未知单位不会由 AI 自动注册：系统保留原单位、令 `normalized_unit=None`、标记维度不完整并送复核。

当前归一器会验证已给出的强类型价格维度、显式单位规则和 numeric/text/boolean/date/entity/json 值，但不自动做汇率换算、地区映射、公司别名消歧、产品规格匹配或模糊日期推断。这些能力应作为独立、版本化的 normalizer 扩展；不要让模型静默合并实体。

断言的稳定 ID 包含：

- 文档 ID；
- 证据片段 ID；
- 主体 + predicate + `FactDimensions.comparability_hash` 形成的事实键；
- 有效时间；
- 规范化 value fingerprint；
- extractor 名称与版本。
- normalizer 名称与版本。

价格等严格 predicate 还必须填写产品规格、地区、现货/长协、税、运费、币种、频率和价格分量。缺失必需维度时断言会被保存并进入复核，不会把空值当作能匹配所有口径的 wildcard。

同一事实来自两个真正独立来源时，应形成两个断言，再由调和器处理，不能提前去重成一个断言。

## 9. 阶段化执行 SDK

长任务可以使用 `PipelineDispatcher`，而不是把全部工作放在一个 Worker handler 中。

```python
from longcycle.application.workflow import NextStage, StageResult
from longcycle.domain.enums import JobStage


async def fetch_handler(job: CollectionJob) -> StageResult:
    # 先执行并幂等持久化本阶段结果。
    document_id = await fetch_and_save(job)
    return StageResult(
        schema_version="fetch-output-v1",
        output_reference={"document_id": str(document_id)},
        next_stages=(
            NextStage(
                stage=JobStage.ARCHIVE,
                pool="io",
                payload={"document_id": str(document_id)},
            ),
        ),
    )


dispatcher = PipelineDispatcher(
    queue=queue,
    checkpoint_store=checkpoint_store,
    handlers={
        JobStage.FETCH: ("fetch-handler-v1", fetch_handler),
    },
)
```

注意：

- handler 的 producer version 属于幂等键的一部分，行为变化时必须升级。
- `output_reference` 应保存对象或数据库行的引用，不应塞入大正文。
- 下游 job ID 根据父 job、序号、阶段、payload 和输出 schema 稳定生成。
- 改变 `next_stages` 顺序会改变下游任务身份。
- 配置 `EventSink` 后，`emitted_events` 会用确定性幂等键写入相应 sink；`PostgresOutboxEventSink` 只负责落库，不等于已经投递到外部消息系统。
- 默认阶段 handler 集合尚未由核心包提供，部署项目负责装配。

## 10. Job Worker 与错误分类

Worker 接收 `dict[JobStage, JobHandler]`。handler 抛出：

```python
raise RetryableJobError("upstream returned 503")
raise PermanentJobError("document violates configured size limit")
```

当前 Worker 会把未知异常视为可重试。因此插件和 handler 应主动把确定性的配置错误、非法 URL、schema 不兼容、超出安全上限等包装为 `PermanentJobError`，避免浪费尝试次数。

当前队列默认最多尝试五次，使用最大一小时的指数退避；尚未实现 full jitter 和 `Retry-After`。不要在 SourcePlugin、ModelGateway 与 Worker 三层同时重试。

只有当前 `lease_owner + lease_token` 可以 acknowledge、fail 或 heartbeat。长任务由 Worker 每隔约三分之一租期自动心跳。

## 11. 其他适配器扩展点

### `ArchiveStore`

必须提供：

```python
put_if_absent(content, content_type, metadata) -> ArchivedObject
get(key) -> bytes
exists(key) -> bool
```

当前文件系统和 S3/R2 实现都使用 SHA-256 内容寻址。新的对象存储适配器必须保持同内容同 key，并验证返回的 `sha256` 和 `size`。

### `ResearchRepository`

Repository 负责来源、文档、证据、抽取、断言、调和和复核。实现必须保持 append/idempotent 语义。业务层只能调用 `reconcile_assertion(candidate, evaluator)`；实现必须在一个事实键锁内读取最新可信基线、执行 evaluator 并持久化 evaluation。不要重新暴露“先查 comparison、后 save”的非原子接口。也不要在 `save_document()` 中覆盖历史正文，或在 `append_assertions()` 中根据字段名覆盖已有来源断言。

### `JobQueue`

队列是至少一次语义，必须实现幂等 enqueue、租约抢占、带 token 的确认/失败和心跳。不能假设 handler 只会执行一次。

### `CheckpointStore`

检查点的完整身份为：

```text
job_id + stage + input_hash + producer_version
```

存储的结果应能恢复成 `StageResult`。PostgreSQL 和内存适配器已经实现该语义。

### `Telemetry`

应用层只依赖 span、counter 与 histogram 风格的窄接口。新增 OpenTelemetry/Prometheus 适配器时，至少保留：

- `job_id`、`trace_id`、stage；
- `source_id`、industry_id；
- 文档哈希，不记录完整正文；
- 模型、prompt/schema 版本；
- token、成本和耗时。

当前默认是 `NullTelemetry`，不会实际输出指标。

## 12. 插件契约测试

每个插件应使用冻结 fixture 测试，不应让普通 CI 依赖实时网站。

最低测试集：

1. 重复 discover 产生相同 `DiscoveryItem.idempotency_key`。
2. 同一资源重复 fetch 产生相同正文哈希。
3. URL 或文件路径不能逃逸允许范围。
4. 超过 `maximum_bytes` 时失败。
5. timeout 与条件请求头被传递。
6. 重定向后仍检查域名和 IP。
7. 缺失必需配置时构造失败。
8. 不在 metadata 中暴露密钥。

一个最小离线测试：

```python
import pytest


@pytest.mark.asyncio
async def test_manifest_plugin_is_stable(source_definition):
    plugin = ManifestFolderSource(source_definition)
    context = DiscoveryContext(source=source_definition)

    first = [item async for item in plugin.discover(context)]
    second = [item async for item in plugin.discover(context)]

    assert [item.idempotency_key for item in first] == [
        item.idempotency_key for item in second
    ]

    fetch_context = FetchContext(
        source=source_definition,
        maximum_bytes=1024 * 1024,
    )
    left = await plugin.fetch(first[0], fetch_context)
    right = await plugin.fetch(first[0], fetch_context)
    assert left.sha256 == right.sha256
```

模型适配器还应有 Golden 测试，固定文档并比较：

- schema 校验；
- 断言数量和字段；
- 数值与单位；
- evidence locator；
- 重复运行 ID；
- token/成本上限。

## 13. 上线前检查表

新增插件或 Gateway 合并前确认：

- [ ] 没有绕过 ports 直接访问应用层内部对象。
- [ ] `plugin_name`、entry point 与 SourceDefinition 配置一致。
- [ ] external ID 或 canonical URL 稳定。
- [ ] 联网插件具备 SSRF、跳转、体积、超时和凭证防护。
- [ ] 原文先归档，抽取结果引用同一文档。
- [ ] 每个断言都有当前 envelope 内的 evidence。
- [ ] extractor、schema、prompt 和 producer version 已固定。
- [ ] 同一输入重复执行不会重复插入断言或下游任务。
- [ ] 已区分可重试和永久错误。
- [ ] 测试使用冻结 fixture，并覆盖安全边界。
- [ ] 未把示例、测试 Gateway 或尚未实现的 Outbox 外部 relay 当成生产能力。
