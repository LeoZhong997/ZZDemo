# PROJECT BRIEF — 外卖数据看板 ETL 系统

> 本文档面向 AI 助手，描述项目的完整背景、架构、数据模型、当前状态和待办事项。
> 阅读本文档后你应该能直接上手开发，无需额外询问基础信息。

---

## 1. 项目定位

这是一个**外卖平台多源数据 ETL + 可视化看板**系统。

- **业务场景**：餐饮品牌同时在美团、饿了么、京东三个外卖平台运营多家门店，需要每周汇总各平台数据进行对比分析。
- **核心价值**：将三个平台各自不同格式的 Excel/CSV 导出文件，清洗、映射、统一后存入 MySQL，再通过 Streamlit 仪表盘展示关键经营指标。
- **用户角色**：运营人员（查看看板）、数据分析师（导出分析）、开发者（维护 ETL 流程）。

---

## 2. 技术栈

| 层级 | 技术 | 版本要求 |
|------|------|----------|
| 语言 | Python | >= 3.8 |
| 数据处理 | pandas, numpy | >= 2.0, >= 1.24 |
| ORM / 连接池 | SQLAlchemy + PyMySQL | >= 2.0, >= 1.1 |
| Excel 解析 | openpyxl | >= 3.1 |
| 前端 | Streamlit + Plotly | >= 1.28 |
| 数据库 | MySQL (InnoDB, utf8mb4) | >= 5.7 |
| 部署 | 本地运行，Shell 脚本启动 | — |

依赖清单见 `requirements.txt`。

---

## 3. 目录结构

```
20260210demo/
│
├── config.py                    # [统一配置] DB连接、常量、日志，支持环境变量覆盖
├── field_mapping.py             # [字段映射] 三平台 中文列名 ↔ 英文字段名 映射字典
├── data_processor.py            # [工具模块] 可复用的清洗、去重、导入、验证函数
├── etl_main.py                  # [ETL主程序] 读取Excel → 映射 → 清洗 → 去重 → 入库
├── import_platform_source.py    # [平台导入器] 处理三平台原始下载文件（更细粒度映射）
├── validate_and_import.py       # [校验导入器] 带数据质量校验的导入流程
├── import_data.py               # [旧版导入] 早期版本，功能已被上面三个文件覆盖
│
├── app.py                       # [主看板] Streamlit 仪表盘首页
├── pages/
│   └── 1_周报数据.py             # [周报页] 每日汇总 + 门店核心指标 + 线上过程指标
├── history_section.py           # [组件] 历史到手率 HTML 片段
├── app_fix.py                   # [补丁] 平台名称修复代码片段
│
├── init_database.sql            # [建库] CREATE DATABASE + CREATE TABLE 完整脚本
├── daily_orders_schema.sql      # [建表] daily_orders 表结构（可单独执行）
├── setup_db.sh                  # [脚本] 数据库初始化自动化
├── run.sh                       # [脚本] ETL 一键运行（含环境检查）
├── run_dashboard.sh             # [脚本] Dashboard 一键启动
│
├── 目标源数据/                    # 已整理的目标格式 Excel（美团历史数据）
├── 下载源文件/                    # 三平台原始下载的 Excel/CSV
├── 目标源文件/                    # 处理后的目标文件（可能为空）
├── logs/                         # ETL 运行日志输出目录
│
├── README.md                    # 项目说明
├── QUICKSTART.md                # 快速上手
├── FIX_REPORT.md                # 平台名称 bug 修复记录
└── IMPORT_SUCCESS.md            # 数据导入成功报告
```

---

## 4. 数据库设计

### 4.1 数据库 & 表

- **数据库名**：`waimai_db`（所有模块统一使用，见 `config.py`）
- **主表**：`daily_orders`（64 列，含自增主键和导入时间）
- **唯一约束**：`UNIQUE KEY (date, platform, brand_store_name)` — 防止重复导入

### 4.2 字段清单（按业务分组）

#### 系统字段
| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | BIGINT AUTO_INCREMENT | 主键 |
| `import_time` | DATETIME | 导入时间戳 |

#### 基础信息（4 字段）
| 字段 | 类型 | 说明 |
|------|------|------|
| `date` | DATE NOT NULL | 订单日期 |
| `brand_store_name` | VARCHAR(100) | 品牌门店名称（如"XX店-朝阳路"）|
| `platform` | VARCHAR(20) NOT NULL | 平台名（中文：美团 / 饿了么 / 京东）|
| `platform_store_name` | VARCHAR(100) | 平台侧门店名称 |

#### 财务指标（15 字段，DECIMAL(10,2)）
| 字段 | 中文 | 计算方式 |
|------|------|----------|
| `actual_income` | 商家实收 | 源数据直取 |
| `expense` | 支出 | 源数据直取 |
| `turnover` | 营业额 | 源数据直取 |
| `net_margin_rate` | 到手率% | = actual_income / turnover × 100 |
| `original_price` | 商品原价 | 仅美团有 |
| `packaging_fee` | 包装费 | 美团/饿了么有 |
| `customer_delivery_fee` | 顾客配送费 | 美团/饿了么有 |
| `customer_paid` | 顾客实付 | 三平台均有 |
| `avg_paid_price` | 实付单均价 | 三平台均有 |
| `activity_subsidy` | 活动补贴 | 三平台均有 |
| `platform_service_fee` | 平台服务费 | 三平台均有 |
| `real_actual_income` | 真实实收 | = actual_income - promotion_cost |
| `promotion_cost` | 推广花费 | 需手动录入或计算 |
| `gift_sausage_cost` | 赠红肠成本 | 需手动录入 |
| `real_net_margin_rate` | 真实到手率% | = real_actual_income / turnover × 100 |

#### 订单数量（3 字段，INT）
| 字段 | 中文 | 来源 |
|------|------|------|
| `valid_orders` | 有效订单 | 三平台均有 |
| `invalid_orders` | 无效订单 | 仅饿了么 |
| `merchant_cancelled_orders` | 商责取消订单 | 美团/饿了么 |

#### 转化率（8 字段，DECIMAL(5,2)，单位%）
| 字段 | 中文 | 来源 |
|------|------|------|
| `store_entry_rate` | 入店转化率 | 三平台均有（饿了么叫"进店转化率"）|
| `order_conversion_rate` | 下单转化率 | 三平台均有 |
| `merchant_cancellation_rate` | 商责取消率 | 美团/饿了么 |
| `new_customer_entry_rate` | 新客入店转化率 | 美团/饿了么 |
| `new_customer_order_rate` | 新客下单转化率 | 美团/饿了么 |
| `old_customer_entry_rate` | 老客入店转化率 | 美团/饿了么 |
| `old_customer_order_rate` | 老客下单转化率 | 美团/饿了么 |
| `repurchase_rate` | 复购率 | 仅美团 |

#### 流量数据（12 字段，INT）
| 字段 | 中文 | 来源 |
|------|------|------|
| `exposure_count` | 曝光人数 | 三平台均有 |
| `entry_count` | 入店人数 | 三平台均有 |
| `exposure_new_customer` | 曝光新客 | 美团/饿了么 |
| `entry_new_customer` | 入店新客 | 美团/饿了么 |
| `exposure_old_customer` | 曝光老客 | 美团/饿了么 |
| `entry_old_customer` | 入店老客 | 美团/饿了么 |
| `exposure_times` | 曝光次数 | 三平台均有 |
| `entry_times` | 入店次数 | 三平台均有 |
| `order_people` | 下单人数 | 美团/饿了么 |
| `order_new_customer` | 下单新客 | 美团/饿了么 |
| `order_old_customer` | 下单老客 | 美团/饿了么 |
| `uv` | UV | 无直接来源 |

#### 评分字段（17 字段，DECIMAL(5,2)）
| 字段 | 中文 | 来源 |
|------|------|------|
| `store_score` | 店铺分 | 仅美团 |
| `new_merchant_score` | 新商家评分 | 美团→综合体验分 / 饿了么→店铺评分 |
| `overall_experience_score` | 综合体验分 | 仅京东 |
| `product_satisfaction` | 商品满意度 | 仅京东 |
| `peak_duration_score` | 高峰营业时长得分 | 美团/饿了么 |
| `quality_product_rate_score` | 优质商品率得分 | 美团/饿了么 |
| `activity_richness_score` | 有效活动丰富度得分 | 美团/饿了么 |
| `reject_order_rate_score` | 商家不接单率得分 | 美团/饿了么 |
| `bad_review_reply_rate_score` | 差评回复率得分 | 美团/饿了么 |
| `online_reply_rate_score` | 在线联系回复率得分 | 美团/饿了么 |
| `menu_richness_score` | 菜单丰富度得分 | 美团/饿了么 |
| `decoration_richness_score` | 装修丰富度得分 | 美团/饿了么 |
| `service_function_score` | 服务功能丰富度得分 | 美团/饿了么 |
| `product_quality_score` | 商品质量分 | 无直接来源 |
| `service_experience_score` | 服务体验分 | 无直接来源 |
| `packaging_satisfaction` | 包装满意度 | 无直接来源 |
| `old_merchant_score` | 旧商家评分 | 无直接来源 |

#### 绩效指标得分（4 字段，DECIMAL(5,2)）
| 字段 | 中文 |
|------|------|
| `repurchase_rate_score` | 复购率指标得分 |
| `message_reply_rate_score` | 消息回复率指标得分 |
| `service_negative_feedback_score` | 服务负反馈率指标得分 |
| `food_safety_negative_feedback_score` | 食品安全负反馈率指标得分 |

#### 回复率 & 其他（7 字段）
| 字段 | 中文 | 类型 |
|------|------|------|
| `five_min_reply_rate` | 5分钟在线联系回复率 | DECIMAL(5,2) |
| `one_min_reply_rate` | 1分钟在线联系回复率 | DECIMAL(5,2) |
| `message_reply_rate` | 消息回复率 | DECIMAL(5,2) |
| `service_negative_feedback_rate` | 服务负反馈率 | DECIMAL(5,2) |
| `food_safety_negative_feedback_rate` | 食品安全负反馈率 | DECIMAL(5,2) |
| `basic_duration` | 基础营业时长(小时) | DECIMAL(6,1) |
| `meal_completion_report_rate` | 出餐完成上报率 | DECIMAL(5,2) |

### 4.3 索引
```sql
INDEX idx_date (date)
INDEX idx_platform (platform)
INDEX idx_brand_store (brand_store_name)
INDEX idx_date_platform (date, platform)   -- 常用组合查询
INDEX idx_import_time (import_time)
UNIQUE KEY uk_date_platform_store (date, platform, brand_store_name)  -- 去重约束
```

---

## 5. 字段映射体系

`field_mapping.py` 中 `FIELD_MAPPING` 是一个**嵌套字典**：

```python
FIELD_MAPPING = {
    "meituan": { "target_field": "中文源列名", ... },
    "eleme":   { "target_field": "中文源列名", ... },
    "jd":      { "target_field": "中文源列名", ... },
}
```

**映射方向**：`target_field`（英文 DB 列名）→ `source_column`（中文 Excel 列名）

**使用方式**：需要构建反向映射来做 `df.rename(columns=...)`:
```python
platform_mapping = FIELD_MAPPING["meituan"]
reverse = {v: k for k, v in platform_mapping.items() if v is not None}
df = df.rename(columns=reverse)  # 中文列名 → 英文字段名
```

### 关键跨平台差异

| 目标字段 | 美团源列名 | 饿了么源列名 | 京东源列名 |
|----------|-----------|-------------|-----------|
| `actual_income` | 营业收入 | 收入 | 收入 |
| `turnover` | 营业收入 | 营业额 | 营业额 |
| `expense` | 补贴及支出 | 支出 | 支出 |
| `store_entry_rate` | 入店转化率 | 进店转化率 | 入店转化率 |
| `entry_count` | 入店人数 | 进店人数 | 入店人数 |
| `customer_paid` | 顾客实付 | 顾客实付总额 | 顾客实付 |
| `packaging_fee` | 包装费 | 打包费 | _(无)_ |
| `platform_service_fee` | 平台服务费(含佣金和配送服务费) | 平台技术服务费 | 平台服务费 |
| `merchant_cancelled_orders` | 商责取消订单 | 商责退单数 | _(无)_ |

> 值为 `None` 的字段表示该平台不提供此指标，导入时自动填 NULL。

---

## 6. ETL 数据流

```
┌─────────────────────────────────────────────────────────┐
│  源数据                                                  │
│  ├── 美团: 目标源数据/外卖源数据.xlsx (4.9MB)              │
│  ├── 饿了么: 下载源文件/【260116】外卖源数据指标.xlsx       │
│  └── 京东: 下载源文件/门店下载_20260112至...xlsx           │
└────────────────────┬────────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Step 1: 读取文件                                        │
│  - Excel → pd.read_excel()                              │
│  - CSV → pd.read_csv(encoding='gbk')                    │
│  - 自动检测表头行                                         │
└────────────────────┬────────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Step 2: 字段映射                                        │
│  - FIELD_MAPPING[platform_key] 获取平台映射               │
│  - 反向映射：中文列名 → 英文字段名                         │
│  - 跳过 None（平台无此指标）                               │
└────────────────────┬────────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Step 3: 数据清洗                                        │
│  - 日期标准化 → datetime.date                            │
│  - 去除 %、¥、逗号等符号                                  │
│  - 字符串数值 → float/int                                │
│  - NaN → 0                                              │
│  - 添加 platform 列（中文名：美团/饿了么/京东）             │
└────────────────────┬────────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Step 4: 验证                                            │
│  - 必需列检查：date, platform, brand_store_name           │
│  - 数值范围检查（百分比 0-100）                            │
│  - 异常值检测（IQR 法）                                   │
└────────────────────┬────────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Step 5: 合并 & 去重                                     │
│  - pd.concat() 合并三平台数据                             │
│  - 按 (date, platform, brand_store_name) 查询已有记录     │
│  - 仅保留数据库中不存在的新记录                             │
└────────────────────┬────────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Step 6: 入库                                            │
│  - 过滤列（只保留 DB 表中存在的列）                        │
│  - to_sql(if_exists='append', chunksize=1000)            │
│  - 添加 import_time 时间戳                                │
└────────────────────┬────────────────────────────────────┘
                     ▼
              MySQL: waimai_db.daily_orders
```

---

## 7. Dashboard 看板功能

### 7.1 主页 (`app.py`)

**侧边栏筛选器**：
- 日期范围选择器（默认最近 7 天）
- 平台多选（美团 / 饿了么 / 京东）
- 门店多选（动态加载）

**主页内容**：
1. **周累计指标卡片**：曝光人数、进店率、下单率、到手率
2. **周环比对比**：有效订单、商家实收、到手率（带涨跌标识和百分比变化）
3. **历史到手率**：上周 / 上上周对比
4. **每日趋势图**：分平台营收趋势（折线图）、分平台单量趋势（折线图）
5. **平台占比分析**：真实实收占比（环形图）、平均客单价对比（柱状图）
6. **Tab 切换**：每日趋势详情 / 原始数据表预览

### 7.2 周报页 (`pages/1_周报数据.py`)

三个数据表格区域：

| 区域 | 展示字段 |
|------|---------|
| 每日汇总 | 日期、星期、营业额、商家实收、到手率、有效订单、实付单均价、无效订单 |
| 门店核心指标 | 日期、店铺分、新商家评分、5分钟回复率、1分钟回复率、出餐完成率、商责取消订单、营业时长、差评回复率得分 |
| 线上过程指标 | 日期、曝光人数、入店人数、入店转化率、下单人数、下单转化率、推广花费、产出、ROI、UV |

---

## 8. 配置管理 (`config.py`)

```python
# 数据库（支持环境变量覆盖）
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', '1203'),
    'database': os.getenv('DB_NAME', 'waimai_db'),
}

# 平台常量
PLATFORM_MEITUAN = '美团'
PLATFORM_ELEME = '饿了么'
PLATFORM_JD = '京东'
ALL_PLATFORMS = [PLATFORM_MEITUAN, PLATFORM_ELEME, PLATFORM_JD]

# ETL 参数
TABLE_NAME = 'daily_orders'
BATCH_SIZE = 1000
DUPLICATE_CHECK_DAYS = 90
```

所有文件（`etl_main.py`、`app.py`、`pages/1_周报数据.py`、`validate_and_import.py`、`import_platform_source.py`）均从 `config.py` 导入配置，不再各自硬编码。

---

## 9. 当前数据状态

| 指标 | 数值 |
|------|------|
| 总记录数 | 13,465 |
| 门店数量 | 13 家 |
| 时间跨度 | 2024-09-05 ~ 2026-01-11（489 天）|
| 美团记录 | 5,359 条（39.8%）|
| 饿了么记录 | 5,211 条（38.7%）|
| 京东记录 | 2,895 条（21.5%）|

---

## 10. 已完成的功能

- [x] 三平台 Excel/CSV 数据提取
- [x] 平台专属字段映射（91/84/70 字段）
- [x] 数据清洗（日期、数值、百分比、空值处理）
- [x] 基于 (date, platform, store) 的去重机制
- [x] 批量入库（append 模式，1000 条/批）
- [x] 统一配置管理（config.py）
- [x] 可复用工具模块（data_processor.py）
- [x] Streamlit 主看板 + 周报页
- [x] KPI 卡片 + 周环比 + 趋势图 + 占比分析
- [x] 侧边栏筛选（日期/平台/门店）
- [x] 10 分钟数据缓存
- [x] 日志框架（文件 + 控制台输出）
- [x] 数据库唯一约束防重复

---

## 11. 已知问题 & 待优化

### 架构层面
- [ ] `import_data.py`、`import_platform_source.py`、`validate_and_import.py` 功能重叠，需要合并或明确分工
- [ ] 没有自动化测试（无 pytest、无 CI/CD）
- [ ] 没有定时调度（每次手动运行 ETL）

### 数据层面
- [ ] `real_actual_income`、`promotion_cost`、`gift_sausage_cost` 等计算字段尚未在 ETL 中自动计算
- [ ] 京东平台的字段覆盖率较低（很多字段映射为 None）
- [ ] `import_platform_source.py` 有更细粒度的映射（如京东的佣金、配送服务费单独拆分），但这些额外字段未在 `daily_orders` 表中体现

### Dashboard 层面
- [ ] 周报页的"线上过程指标"中 ROI 和产出的计算逻辑未实现
- [ ] 缺少门店维度的排名和对比分析
- [ ] 缺少数据导出功能
- [ ] 移动端适配不足
- [ ] 趋势图缺少移动平均线等高级分析

### 代码质量
- [ ] 部分 print 语句未统一迁移到 logging
- [ ] 异常处理粒度较粗（部分 `except Exception`）
- [ ] `app.py` 中主页和 tab1 的图表代码有重复

---

## 12. 开发约定

### 平台名称
数据库中存储的是**中文名**（美团 / 饿了么 / 京东），**不是**英文代码。所有 SQL 查询和 Dashboard 筛选都使用中文名。

### 字段映射方向
`field_mapping.py` 中的映射是 `英文目标字段 → 中文源列名`。使用时需要反转为 `中文源列名 → 英文目标字段` 再做 `df.rename(columns=...)`。

### 数据入库模式
始终使用 `if_exists='append'`，**严禁使用** `if_exists='replace'`（会清空整张表）。

### 去重策略
以 `(date, platform, brand_store_name)` 三元组作为唯一标识。入库前先查询已有数据，跳过重复记录。

### 文件编码
- 美团 CSV 文件使用 GBK 编码
- 其他 Excel 文件使用 openpyxl 读取（自动处理编码）
- 饿了么 Excel 的 sheet 名为 `data`
- 京东 Excel 的 sheet 名为 `数据`

---

## 13. 快速启动命令

```bash
# 初始化数据库
mysql -u root -p < init_database.sql

# 安装依赖
pip install -r requirements.txt

# 运行 ETL
python etl_main.py

# 启动看板
streamlit run app.py
```

---

## 14. 关键文件依赖关系

```
config.py ←── 被所有模块导入
    │
field_mapping.py ←── 被 ETL 模块导入
    │
data_processor.py ←── 导入 config + field_mapping
    │
etl_main.py ←── 导入 config + field_mapping（主 ETL 入口）
import_platform_source.py ←── 导入 config（平台原始文件导入）
validate_and_import.py ←── 导入 config（校验+导入）
    │
app.py ←── 导入 config（Dashboard 主页）
pages/1_周报数据.py ←── 导入 config（周报页，需 sys.path 处理）
```
