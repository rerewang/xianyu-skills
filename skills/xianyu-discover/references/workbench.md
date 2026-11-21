# 工作台与接口

当前项目：`/Users/wanghongjie/Documents/Codex/2026-10-28/wo/outputs/xianyu-research`
本地界面：`http://127.0.0.1:8765/`；数据库：`data/research.sqlite3`。
路径失效时查找已有项目或询问，不静默创建空数据库。当前启动脚本 `python3 app.py --port 8765`。服务运行中修改Python后需重启同一服务。

## 读写

```bash
python3 /Users/wanghongjie/.codex/skills/xianyu-discover/scripts/workbench.py --root /Users/wanghongjie/Documents/Codex/2026-10-28/wo/outputs/xianyu-research status
```

`data` 返回全量数据，`check` 返回方向覆盖与下一步。写操作把实际 JSON 写入临时 UTF-8 文件，使用同一命令的 `project|keyword|create|review|update --file /绝对路径.json`。读返回ID后再进行依赖写入，保留真实换行，不用shell插值拼任意文案。

- project: `{name,parent_term,location,priority,notes}`。同名更新，避免覆盖未请求的已有资料。
- keyword: `{project_id,keyword,parent_term,dimension,reason,priority}`。结构化扩词，优先级在 keyword_context，采样进度在 keywords.status。当前一个词只能归一个方向；跨方向复用要先检查已有归属，不能静默改归属。
- create: `{project_id,name,reason,next_action}`。生成待评估机会，返回id。同方向同名唯一，先查再建。
- review: `{observation_id,project_id,disposition,reason,opportunity_ids:[]}`。disposition 为机会证据/排除/待核验；机会证据必须关联本方向机会。覆盖旧初筛及关联，重评前读取旧值。观察ID取 data.products.id（最近观察），完整历史可读GET `/api/history?id=商品ID`；历史批次初筛必须用对应历史观察ID。
- update: `{id,status,reason,next_action,demand,competition,economics,fulfillment,eligibility,test_plan,readiness:{},test_result:{}}`。部分更新；六个英文评估字段分别对应需求/竞争/利润/履约/销售条件/测试方案；readiness同名布尔字段。进入待测试前六项均 true 且文字有依据。readiness和test_result传入时整对象替换，先读现值合并。

测试结果对象字段：period（周期文本）、exposure、inquiries、orders、refunds、labor_minutes（非负数）、conclusion。缺失值null；不能用0代替未观察。

## 流转

- 待评估 → 追加研究 / 暂缓 / 淘汰
- 追加研究 → 需求候选 / 待测试 / 暂缓 / 淘汰
- 需求候选 → 待测试 / 追加研究 / 暂缓 / 淘汰
- 待测试 → 测试中 / 追加研究 / 暂缓 / 淘汰
- 测试中 → 保留 / 追加研究 / 暂缓 / 淘汰
- 保留 → 追加研究 / 测试中 / 暂缓 / 淘汰
- 暂缓 → 追加研究 / 淘汰
- 淘汰 → 追加研究（新证据重新打开）

同阶段允许补充评估；每次更新写 workflow_events，包含完整前后快照和时间。六项门槛由人/agent核实，服务端只校验字段完备，不能自动验证真伪。

## 采样与兼容

`ingest_capture.py` 的 parse_card/convert 可复用，但 convert 的默认 external_key/notes 写第一轮；新轮次转换后必须替换为独立前缀及真实轮次描述，再使用 app.import_batch 或POST `/api/import`。归档原始capture至 data/captures，SHA256按 `json.dumps(capture,ensure_ascii=False,sort_keys=True)`计算。不要覆盖第一轮最终报告与备份。

旧 candidates 是竞品锚点，保留作历史；v2 decisions 使用 opportunities + opportunity_evidence。不能继续向旧表写入冒充新流程判断。未归入流程的历史批次不是已完成初筛；方向覆盖只计算已关联关键词。

上海山姆：用户指定重点，非仅虚拟产品。已有80条/79商品，线上代下单、到店带入、650g芥末夏威夷果、零食组合为追加研究；会员账号权益类暂缓。用户会员、门店距离、车辆等未确认。后续以实时工作台为准，不将此快照当成永久结论。

## 需求优先规则（用户2026-10-29修正）

需求候选只要求真实需求文字、readiness.demand=true与有效关联证据；其余五项可未知。进入待测试仍须六项核验。GET /api/data 的 workflow.demand_ranking 提供按方向、交易类型去重的需求指标；detail_metrics 单独保存商品销量和账号累计，不能混用。ingest_detail.py.ingest 归档实际浏览器详情，正文必须排除推荐区。免费和异常价不直接排除需求；异常价标注待核验。用户已确认有会员、门店近且可采购交付，会员类型仍未知；旧快照仅供历史参考。
