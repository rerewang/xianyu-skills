# 闲鱼三阶段交接契约 v1

## 文件、类型和唯一标识

所有文件UTF-8标准JSON。日期必须含时区，商品/卖家ID用字符串，金额统一整数人民币分（price_fen、amount_fen），未知为null而非0。正文存实际字符串，序列化用JSON标准换行转义；读取后保留空格、加号和空行，禁止URL解码。
路径统一为相对于商品库根目录的路径，不相对于进程cwd；文件必须存在，禁止引用库外路径。SKU ID在同一商品内唯一。JSON Schema见相邻两个schema文件，禁止额外顶层字段；attributes可容纳平台类目属性。
所有阶段验证输入contract和schema_version，不认识的版本明确报错，不猜测兼容。

## 第一 → 第二：discovery.json

输出位置 discovery-batches/<batch_id>/discovery.json，格式见 discovery.schema.json。
每个candidate表示一个已找到的具体商品或卖家：kind=product/seller，platform_id分别为商品ID/卖家ID。candidate_id在批次内唯一。必须提供URL、观察时间、推荐依据和至少一份实际证据路径；没有真实候选时允许空数组，不凑数。
metrics的value只存精确数；缩略值如“1万”存display，value=null，precision=abbreviated。未公开单品销量value=null、precision=unknown；卖家累计销量不能填入product_sales。
第二个skill直接消费此文件，不重新选品；按用户指定candidate_id执行，未指定时处理全部候选。卖家候选展开为多个商品档案，每个商品保留相同lineage.candidate_id。不自动将发现清单加入上架队列。

## 第二 → 第三：listing.json

输出位置 listing-packages/<product_id>/revisions/<revision>.json；同目录listing.json是当前版本副本，历史版本不覆盖。格式见listing-package.schema.json。lineage回溯discovery的batch_id/candidate_id；用户直接提供链接时input_kind=direct，两个上游ID为null。
source保留竞品原始事实与卖家声称；listing为实际执行值，用户覆盖写入overrides。不能修改source来匹配我们自己的价格。每个SKU必须明确options和对应price_fen；禁止按区间猜测。无SKU必须有主价格；有SKU主价格应为null。
completeness与队列状态是两套独立状态。可上架必须满足：正文非空、至少一张本地图片且watermark_check=passed、分类明确、价格模式有效、运费明确、missing_fields/conflicts为空。free/none运费amount_fen=0，fixed金额明确；distance必须有可在平台实际选择的规则说明(scope)。按地区观察的运费不能推广为全国统一价。属性如缺必填信息须待补齐。可上架不代表平台已审核或履约已核实。
图片数组顺序即上传顺序，第一张是主图；rejected/unknown图片禁止上传。每项必须对应当前商品且本地文件可读。

## 第二阶段批次清单与第三阶段取件

每次建档另存 archive-batches/<batch_id>/manifest.json：
{"contract":"xianyu.archive-manifest","schema_version":1,"batch_id":"批次ID","items":[{"product_id":"123","candidate_id":"候选ID或null","revision":1,"package_path":"listing-packages/123/revisions/1.json","completeness":"待补齐"}]}
manifest每项必须指向存在且ID/版本/完整度一致的资料单。第三个skill默认仍由用户队列授权选择商品，从队列未上架状态按加入时间取前N件；通过product_id找到listing.json并固定其revision和历史文件路径。批次清单本身不授权把全部商品上架。用户明确指定资料单/批次时可直接输入，但需在本地队列登记后执行，保持可追溯。

## 第三阶段回执与失败

批次目录保存run.json：contract=xianyu.listing-run、schema_version=1、batch_id、items。每项记录product_id、package_revision、package_path、step、result(pending/filled/failed)、tab_id、publish_url、checks、screenshot_paths、error、updated_at。
checks记录description、layout、images、skus、shipping、services，各项为passed/failed/not_checked，未检查不能当通过。只有全部passed且表单保留成功才标filled并回写队列待上架。失败保留未上架，记录步骤和原因，不从批次外补位。平台验证触发时停止平台操作。
回写使用现有POST /api/listing-queue，preparation保存package_revision/package_path/run_path及页面标识。已上架由用户手动标记。平台URL与本地文件都不等于已保存平台草稿。

## 校验范围

JSON Schema负责字段、类型和枚举；执行前另外检查唯一性、证据/图片文件存在、上游关联、金额与SKU组合、完整度条件及manifest一致性。校验失败列出字段路径与错误，不能宣称资料可上架。本契约不自动迁移历史catalog或改造工作台UI；旧数据必须显式整理成资料单后才能进入新版执行流程。
