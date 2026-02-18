# 项目规格说明书 - 外卖数据看板 ETL 系统

> **本文档目的**：提供完整的项目规格说明，使 AI 助手能够根据本文档从头开始构建一个功能完全相同的外卖数据看板系统。
> 
> **适用场景**：项目重建、代码重构、团队协作、技术文档。

---

## 1. 项目概述

### 1.1 项目定位

这是一个**外卖平台多源数据 ETL + 可视化看板**系统，用于餐饮品牌在美团、饿了么、京东三个外卖平台运营多门店时的数据汇总和分析。

### 1.2 业务场景

- **数据来源**：三个外卖平台各自导出的 Excel/CSV 格式数据文件
- **数据特点**：不同平台的列名、数据格式、字段定义各不相同
- **数据需求**：每周汇总各平台数据，进行横向对比分析，监控经营指标

### 1.3 核心价值

1. **数据统一**：将三平台不同格式的数据清洗、映射、统一为标准化格式
2. **自动化处理**：一键完成数据提取、清洗、计算、入库全流程
3. **可视化展示**：通过 Streamlit 仪表盘直观展示关键经营指标
4. **去重机制**：基于唯一约束防止重复导入，保证数据准确性

### 1.4 用户角色

- **运营人员**：查看看板，了解各平台经营状况
- **数据分析师**：导出数据，进行深入分析
- **开发者**：维护 ETL 流程，扩展功能

---

## 2. 技术栈

### 2.1 后端技术

| 技术 | 版本要求 | 用途 |
|------|----------|------|
| Python | >= 3.8 | 主要编程语言 |
| pandas | >= 2.0 | 数据处理和分析 |
| numpy | >= 1.24 | 数值计算 |
| SQLAlchemy | >= 2.0 | 数据库 ORM |
| PyMySQL | >= 1.1.0 | MySQL 驱动 |
| openpyxl | >= 3.1.0 | Excel 文件读写 |

### 2.2 前端技术

| 技术 | 版本要求 | 用途 |
|------|----------|------|
| Streamlit | >= 1.28.0 | 数据可视化框架 |
| Plotly | (随 Streamlit 安装) | 交互式图表 |

### 2.3 数据库

| 技术 | 版本要求 | 配置 |
|------|----------|------|
| MySQL | >= 5.7 | 数据存储引擎 |
| 字符集 | utf8mb4 | 支持中文和特殊字符 |
| 排序规则 | utf8mb4_unicode_ci | 大小写不敏感排序 |

### 2.4 完整依赖清单

创建 `requirements.txt` 文件：

```txt
streamlit>=1.28.0
pandas>=2.0.0
sqlalchemy>=2.0.0
pymysql>=1.1.0
openpyxl>=3.1.0
numpy>=1.24.0
```

---

## 3. 项目目录结构

```
20260210demo/
│
├── app.py                              # [主看板] Streamlit 仪表盘主页
│
├── pages/                              # [多页应用] Streamlit 多页面
│   ├── 1_周报数据.py                    # 周报数据页
│   └── store_management.py             # 门店管理页
│
├── etl/                                # [ETL 模块] 数据处理核心
│   ├── __init__.py
│   │
│   ├── config/                         # [配置目录]
│   │   ├── __init__.py
│   │   ├── config.py                   # 统一配置文件（数据库、常量、路径）
│   │   ├── daily_orders_schema.sql     # 建表 SQL 脚本
│   │   ├── init_database.sql           # 初始化数据库脚本
│   │   └── store_schema.sql            # 门店映射表结构
│   │
│   ├── core/                           # [核心模块]
│   │   ├── __init__.py
│   │   ├── etl_main.py                 # ETL 主程序
│   │   ├── field_mapping.py            # 字段映射字典
│   │   ├── data_processor.py           # 数据处理工具函数
│   │   ├── import_data.py              # 数据导入模块
│   │   ├── import_platform_source.py   # 平台源文件导入
│   │   ├── validate_and_import.py     # 验证和导入
│   │   ├── validate_etl_data.py        # 数据验证
│   │   └── store_mapper.py             # 门店映射处理
│   │
│   ├── data/                           # [数据目录]
│   │   ├── sources/                    # 源数据目录
│   │   │   ├── 目标源数据/              # 已整理的目标格式数据
│   │   │   ├── 下载源文件/              # 三平台原始下载文件
│   │   │   └── 目标源文件/              # 处理后的目标文件
│   │   └── backup/                     # 备份目录
│   │
│   ├── logs/                           # [日志目录]
│   │   ├── etl_validation_report.html
│   │   └── etl_validation_results.json
│   │
│   └── reports/                        # [报告目录]
│       ├── ETL_FIX_REPORT.md
│       ├── ETL_IMPORT_REPORT.md
│       └── ETL_VALIDATION_ANALYSIS.md
│
├── logs/                               # [应用日志目录]
│
├── run_etl.py                          # [启动脚本] ETL 程序入口
├── run_dashboard.sh                    # [启动脚本] Dashboard 启动脚本
│
├── requirements.txt                    # [依赖清单] Python 包依赖
│
├── README.md                           # 项目说明文档
├── PROJECT_BRIEF.md                    # 项目简要说明
├── QUICKSTART.md                       # 快速上手指南
├── PROJECT_SPECIFICATION.md            # 本文档：完整规格说明
│
├── .gitignore                          # Git 忽略文件配置
│
└── [其他文档和脚本文件...]              # 各种修复报告、分析文档等
```

---

## 4. 数据库设计

### 4.1 数据库基本信息

- **数据库名**：`waimai_db`
- **字符集**：`utf8mb4`
- **排序规则**：`utf8mb4_unicode_ci`
- **引擎**：`InnoDB`

### 4.2 主表：daily_orders

**表用途**：存储每日订单汇总数据，包含三个平台的所有指标。

**字段总数**：64 个字段

### 4.3 字段详细说明

#### 4.3.1 系统字段（2个）

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | BIGINT | AUTO_INCREMENT PRIMARY KEY | 自增主键 |
| `import_time` | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP | 数据导入时间 |

#### 4.3.2 基础信息字段（4个）

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `date` | DATE | NOT NULL | 订单日期 |
| `brand_store_name` | VARCHAR(100) | - | 品牌门店名称（如"XX店-朝阳路"） |
| `platform` | VARCHAR(20) | NOT NULL | 平台名称（中文：美团/饿了么/京东） |
| `platform_store_name` | VARCHAR(100) | - | 平台侧门店名称 |

#### 4.3.3 财务指标字段（15个）

所有金额字段使用 `DECIMAL(10,2)`，精度到分。

| 字段名 | 类型 | 说明 | 计算方式 |
|--------|------|------|----------|
| `actual_income` | DECIMAL(10,2) | 商家实收 | 源数据直取 |
| `expense` | DECIMAL(10,2) | 支出 | 源数据直取 |
| `turnover` | DECIMAL(10,2) | 营业额 | 源数据直取 |
| `net_margin_rate` | DECIMAL(5,2) | 到手率（%） | = actual_income / turnover × 100 |
| `original_price` | DECIMAL(10,2) | 商品原价 | 仅美团有 |
| `packaging_fee` | DECIMAL(10,2) | 包装费 | 美团/饿了么有 |
| `customer_delivery_fee` | DECIMAL(10,2) | 顾客配送费 | 美团/饿了么有 |
| `customer_paid` | DECIMAL(10,2) | 顾客实付 | 三平台均有 |
| `avg_paid_price` | DECIMAL(10,2) | 实付单均价 | 三平台均有 |
| `activity_subsidy` | DECIMAL(10,2) | 活动补贴 | 三平台均有 |
| `platform_service_fee` | DECIMAL(10,2) | 平台服务费 | 三平台均有 |
| `real_actual_income` | DECIMAL(10,2) | 真实实收 | = actual_income - promotion_cost |
| `promotion_cost` | DECIMAL(10,2) | 推广花费 | 需手动录入 |
| `gift_sausage_cost` | DECIMAL(10,2) | 赠红肠成本 | 需手动录入 |
| `real_net_margin_rate` | DECIMAL(5,2) | 真实到手率（%） | = real_actual_income / turnover × 100 |

#### 4.3.4 订单数量字段（3个）

| 字段名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `valid_orders` | INT | 0 | 有效订单 |
| `invalid_orders` | INT | 0 | 无效订单 |
| `merchant_cancelled_orders` | INT | 0 | 商责取消订单 |

#### 4.3.5 转化率字段（8个）

所有百分比字段使用 `DECIMAL(5,2)`，保留2位小数。

| 字段名 | 类型 | 说明 | 备注 |
|--------|------|------|------|
| `merchant_cancellation_rate` | DECIMAL(5,2) | 商责取消率（%） | 美团/饿了么 |
| `store_entry_rate` | DECIMAL(5,2) | 入店转化率（%） | 饿了么叫"进店转化率" |
| `order_conversion_rate` | DECIMAL(5,2) | 下单转化率（%） | 三平台均有 |
| `new_customer_entry_rate` | DECIMAL(5,2) | 新客入店转化率（%） | 美团/饿了么 |
| `new_customer_order_rate` | DECIMAL(5,2) | 新客下单转化率（%） | 美团/饿了么 |
| `old_customer_entry_rate` | DECIMAL(5,2) | 老客入店转化率（%） | 美团/饿了么 |
| `old_customer_order_rate` | DECIMAL(5,2) | 老客下单转化率（%） | 美团/饿了么 |
| `repurchase_rate` | DECIMAL(5,2) | 复购率（%） | 仅美团 |

#### 4.3.6 流量数据字段（12个）

| 字段名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `exposure_count` | INT | 0 | 曝光人数 |
| `entry_count` | INT | 0 | 入店人数 |
| `exposure_new_customer` | INT | 0 | 曝光新客 |
| `entry_new_customer` | INT | 0 | 入店新客 |
| `exposure_old_customer` | INT | 0 | 曝光老客 |
| `entry_old_customer` | INT | 0 | 入店老客 |
| `exposure_times` | INT | 0 | 曝光次数 |
| `entry_times` | INT | 0 | 入店次数 |
| `order_people` | INT | 0 | 下单人数 |
| `order_new_customer` | INT | 0 | 下单新客 |
| `order_old_customer` | INT | 0 | 下单老客 |
| `uv` | INT | 0 | UV |

#### 4.3.7 评分字段（17个）

所有评分字段使用 `DECIMAL(5,2)`，通常为0-10或0-100。

| 字段名 | 类型 | 说明 | 备注 |
|--------|------|------|------|
| `store_score` | DECIMAL(5,2) | 店铺分 | 仅美团 |
| `peak_duration_score` | DECIMAL(5,2) | 高峰营业时长得分 | 美团/饿了么 |
| `quality_product_rate_score` | DECIMAL(5,2) | 优质商品率得分 | 美团/饿了么 |
| `activity_richness_score` | DECIMAL(5,2) | 有效活动丰富度得分 | 美团/饿了么 |
| `reject_order_rate_score` | DECIMAL(5,2) | 商家不接单率得分 | 美团/饿了么 |
| `bad_review_reply_rate_score` | DECIMAL(5,2) | 差评回复率得分 | 美团/饿了么 |
| `online_reply_rate_score` | DECIMAL(5,2) | 在线联系回复率得分 | 美团/饿了么 |
| `new_merchant_score` | DECIMAL(5,2) | 新商家评分 | 美团→综合体验分 / 饿了么→店铺评分 |
| `menu_richness_score` | DECIMAL(5,2) | 菜单丰富度得分 | 美团/饿了么 |
| `decoration_richness_score` | DECIMAL(5,2) | 装修丰富度得分 | 美团/饿了么 |
| `service_function_score` | DECIMAL(5,2) | 服务功能丰富度得分 | 美团/饿了么 |
| `overall_experience_score` | DECIMAL(5,2) | 综合体验分 | 仅京东 |
| `product_quality_score` | DECIMAL(5,2) | 商品质量分 | 无直接来源 |
| `service_experience_score` | DECIMAL(5,2) | 服务体验分 | 无直接来源 |
| `product_satisfaction` | DECIMAL(5,2) | 商品满意度 | 仅京东 |
| `packaging_satisfaction` | DECIMAL(5,2) | 包装满意度 | 无直接来源 |
| `old_merchant_score` | DECIMAL(5,2) | 旧商家评分 | 无直接来源 |

#### 4.3.8 指标得分字段（4个）

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `repurchase_rate_score` | DECIMAL(5,2) | 复购率指标得分 |
| `message_reply_rate_score` | DECIMAL(5,2) | 消息回复率指标得分 |
| `service_negative_feedback_score` | DECIMAL(5,2) | 服务负反馈率指标得分 |
| `food_safety_negative_feedback_score` | DECIMAL(5,2) | 食品安全负反馈率指标得分 |

#### 4.3.9 回复率字段（4个）

使用 `DECIMAL(5,4)`，保留4位小数。

| 字段名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `five_min_reply_rate` | DECIMAL(5,4) | 0 | 5分钟回复率 |
| `one_min_reply_rate` | DECIMAL(5,4) | 0 | 1分钟回复率 |
| `message_reply_rate` | DECIMAL(5,4) | 0 | 消息回复率 |
| `food_safety_negative_feedback_rate` | DECIMAL(5,4) | 0 | 食品安全负反馈率 |

#### 4.3.10 时间和完成率字段（2个）

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `basic_duration` | DECIMAL(6,1) | 基础营业时长（小时） |
| `meal_completion_report_rate` | DECIMAL(5,2) | 出餐完成上报率（%） |

### 4.4 完整建表 SQL 脚本

保存为 `etl/config/daily_orders_schema.sql`：

```sql
-- 外卖数据看板 - 每日订单汇总表
CREATE TABLE daily_orders (
    -- 主键和系统字段
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    import_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '数据导入时间',

    -- 基础信息字段
    `date` DATE NOT NULL COMMENT '订单日期',
    brand_store_name VARCHAR(100) COMMENT '品牌门店名称',
    platform VARCHAR(20) NOT NULL COMMENT '平台（美团/饿了么/京东）',
    platform_store_name VARCHAR(100) COMMENT '平台门店名称',

    -- 财务指标字段（金额统一使用 DECIMAL(10,2)，精度为元，支持到分）
    actual_income DECIMAL(10,2) COMMENT '商家实收',
    expense DECIMAL(10,2) COMMENT '支出',
    turnover DECIMAL(10,2) COMMENT '营业额',
    net_margin_rate DECIMAL(5,2) COMMENT '到手率（百分比）',
    original_price DECIMAL(10,2) COMMENT '商品原价',
    packaging_fee DECIMAL(10,2) COMMENT '包装费',
    customer_delivery_fee DECIMAL(10,2) COMMENT '顾客配送费（跑腿/自配送）',
    customer_paid DECIMAL(10,2) COMMENT '顾客实付',
    avg_paid_price DECIMAL(10,2) COMMENT '实付单均价',
    activity_subsidy DECIMAL(10,2) COMMENT '活动补贴',
    platform_service_fee DECIMAL(10,2) COMMENT '平台服务费(含佣金和配送服务费)',
    real_actual_income DECIMAL(10,2) COMMENT '真实实收',
    promotion_cost DECIMAL(10,2) COMMENT '推广花费',
    gift_sausage_cost DECIMAL(10,2) COMMENT '赠红肠成本',
    real_net_margin_rate DECIMAL(5,2) COMMENT '真实到手率（百分比）',

    -- 订单数量字段（整数）
    valid_orders INT DEFAULT 0 COMMENT '有效订单',
    invalid_orders INT DEFAULT 0 COMMENT '无效订单',
    merchant_cancelled_orders INT DEFAULT 0 COMMENT '商责取消订单',

    -- 转化率字段（百分比，保留2位小数）
    merchant_cancellation_rate DECIMAL(5,2) COMMENT '商责取消率（百分比）',
    store_entry_rate DECIMAL(5,2) COMMENT '入店转化率（百分比）',
    order_conversion_rate DECIMAL(5,2) COMMENT '下单转化率（百分比）',
    new_customer_entry_rate DECIMAL(5,2) COMMENT '新客入店转化率（百分比）',
    new_customer_order_rate DECIMAL(5,2) COMMENT '新客下单转化率（百分比）',
    old_customer_entry_rate DECIMAL(5,2) COMMENT '老客入店转化率（百分比）',
    old_customer_order_rate DECIMAL(5,2) COMMENT '老客下单转化率（百分比）',
    repurchase_rate DECIMAL(5,2) COMMENT '复购率（百分比）',

    -- 流量数据字段（整数）
    exposure_count INT DEFAULT 0 COMMENT '曝光人数',
    entry_count INT DEFAULT 0 COMMENT '入店人数',
    exposure_new_customer INT DEFAULT 0 COMMENT '曝光新客',
    entry_new_customer INT DEFAULT 0 COMMENT '入店新客',
    exposure_old_customer INT DEFAULT 0 COMMENT '曝光老客',
    entry_old_customer INT DEFAULT 0 COMMENT '入店老客',
    exposure_times INT DEFAULT 0 COMMENT '曝光次数',
    entry_times INT DEFAULT 0 COMMENT '入店次数',
    order_people INT DEFAULT 0 COMMENT '下单人数',
    order_new_customer INT DEFAULT 0 COMMENT '下单新客',
    order_old_customer INT DEFAULT 0 COMMENT '下单老客',
    uv INT DEFAULT 0 COMMENT 'UV',

    -- 评分字段（分数，通常为0-10或0-100，保留2位小数）
    store_score DECIMAL(5,2) COMMENT '店铺分',
    peak_duration_score DECIMAL(5,2) COMMENT '高峰营业时长得分',
    quality_product_rate_score DECIMAL(5,2) COMMENT '优质商品率得分',
    activity_richness_score DECIMAL(5,2) COMMENT '有效活动丰富度得分',
    reject_order_rate_score DECIMAL(5,2) COMMENT '商家不接单率得分',
    bad_review_reply_rate_score DECIMAL(5,2) COMMENT '差评回复率得分',
    online_reply_rate_score DECIMAL(5,2) COMMENT '在线联系回复率得分',
    new_merchant_score DECIMAL(5,2) COMMENT '新商家评分',
    menu_richness_score DECIMAL(5,2) COMMENT '菜单丰富度得分',
    decoration_richness_score DECIMAL(5,2) COMMENT '装修丰富度得分',
    service_function_score DECIMAL(5,2) COMMENT '服务功能丰富度得分',
    overall_experience_score DECIMAL(5,2) COMMENT '综合体验分',
    product_quality_score DECIMAL(5,2) COMMENT '商品质量分',
    service_experience_score DECIMAL(5,2) COMMENT '服务体验分',
    product_satisfaction DECIMAL(5,2) COMMENT '商品满意度',
    packaging_satisfaction DECIMAL(5,2) COMMENT '包装满意度',
    old_merchant_score DECIMAL(5,2) COMMENT '旧商家评分',

    -- 指标得分字段（保留2位小数）
    repurchase_rate_score DECIMAL(5,2) COMMENT '复购率指标得分',
    message_reply_rate_score DECIMAL(5,2) COMMENT '消息回复率指标得分',
    service_negative_feedback_score DECIMAL(5,2) COMMENT '服务负反馈率指标得分',
    food_safety_negative_feedback_score DECIMAL(5,2) COMMENT '食品安全负反馈率指标得分',

    -- 回复率字段（百分比，保留4位小数）
    five_min_reply_rate DECIMAL(5,4) DEFAULT 0 COMMENT '5分钟回复率',
    one_min_reply_rate DECIMAL(5,4) DEFAULT 0 COMMENT '1分钟回复率',
    message_reply_rate DECIMAL(5,4) DEFAULT 0 COMMENT '消息回复率',
    food_safety_negative_feedback_rate DECIMAL(5,4) DEFAULT 0 COMMENT '食品安全负反馈率',

    -- 时间字段（小时数，保留1位小数）
    basic_duration DECIMAL(6,1) COMMENT '基础营业时长（小时）',

    -- 完成率字段（百分比，保留2位小数）
    meal_completion_report_rate DECIMAL(5,2) COMMENT '出餐完成上报率（百分比）',

    -- 索引优化
    INDEX idx_date (`date`),
    INDEX idx_platform (`platform`),
    INDEX idx_brand_store (`brand_store_name`),
    INDEX idx_date_platform (`date`, `platform`),
    INDEX idx_import_time (`import_time`),

    -- 唯一约束：防止重复导入
    UNIQUE KEY uk_date_platform_store (`date`, `platform`, `brand_store_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='外卖数据看板 - 每日订单汇总表';
```

### 4.5 索引和约束说明

- **普通索引**：
  - `idx_date`：加速日期查询
  - `idx_platform`：加速平台筛选
  - `idx_brand_store`：加速门店查询
  - `idx_date_platform`：加速日期+平台组合查询
  - `idx_import_time`：加速导入时间查询

- **唯一约束**：
  - `uk_date_platform_store(date, platform, brand_store_name)`：防止重复导入同一天同一平台同一门店的数据

---

## 5. 字段映射体系

### 5.1 映射字典结构

字段映射定义在 `etl/core/field_mapping.py` 文件中，结构如下：

```python
FIELD_MAPPING = {
    "meituan": {
        "目标字段名": "中文源列名",
        ...
    },
    "eleme": {
        "目标字段名": "中文源列名",
        ...
    },
    "jd": {
        "目标字段名": "中文源列名",
        ...
    }
}
```

### 5.2 映射规则

- **映射方向**：`目标字段名`（英文 DB 列名）→ `中文源列名`（Excel 列名）
- **使用方式**：需要构建反向映射来做 `df.rename(columns=...)`
- **None 值**：表示该平台不提供此指标，导入时自动填 NULL

### 5.3 完整字段映射

#### 5.3.1 美团平台映射

```python
"meituan": {
    # 基础信息字段
    "date": "日期",
    "brand_store_name": None,  # 通过映射表获取
    "platform_store_name": "门店名称",
    "store_id": "门店id",
    "city": "门店所在城市",

    # 财务指标字段
    "actual_income": "营业收入",
    "expense": "补贴及支出",
    "turnover": "优惠前总额",
    "net_margin_rate": None,  # 到手率需要计算
    "original_price": "商品原价",
    "packaging_fee": "包装费",
    "customer_delivery_fee": "顾客配送费（跑腿/自配送）",
    "customer_paid": "顾客实付",
    "avg_paid_price": "实付单均价",
    "activity_subsidy": "活动补贴",
    "platform_service_fee": "平台服务费(含佣金和配送服务费)",
    "real_actual_income": None,
    "promotion_cost": None,
    "gift_sausage_cost": None,
    "real_net_margin_rate": None,

    # 订单数量字段
    "valid_orders": "有效订单",
    "invalid_orders": "取消订单",
    "merchant_cancelled_orders": "商责取消订单",

    # 转化率字段
    "merchant_cancellation_rate": "商责取消率",
    "store_entry_rate": "入店转化率",
    "order_conversion_rate": "下单转化率",
    "new_customer_entry_rate": "新客入店转化率",
    "new_customer_order_rate": "新客下单转化率",
    "old_customer_entry_rate": "老客入店转化率",
    "old_customer_order_rate": "老客下单转化率",
    "repurchase_rate": "复购率",

    # 流量数据字段
    "exposure_count": "曝光人数",
    "entry_count": "入店人数",
    "exposure_new_customer": "曝光新客",
    "entry_new_customer": "入店新客",
    "exposure_old_customer": "曝光老客",
    "entry_old_customer": "入店老客",
    "exposure_times": "曝光次数",
    "entry_times": "入店次数",
    "order_people": "下单人数",
    "order_new_customer": "下单新客",
    "order_old_customer": "下单老客",
    "uv": None,

    # 评分字段
    "store_score": "店铺分",
    "peak_duration_score": "高峰营业时长得分",
    "quality_product_rate_score": "优质商品率得分",
    "activity_richness_score": "有效活动丰富度得分",
    "reject_order_rate_score": "商家不接单率得分",
    "bad_review_reply_rate_score": "差评回复率得分",
    "online_reply_rate_score": "在线联系回复率得分",
    "new_merchant_score": "overall_experience_score",
    "menu_richness_score": "菜单丰富度得分",
    "decoration_richness_score": "装修丰富度得分",
    "service_function_score": "服务功能丰富度得分",
    "product_quality_score": "商品质量分",
    "service_experience_score": "服务体验分",
    "product_satisfaction": "商品满意度",
    "packaging_satisfaction": "包装满意度",

    # 指标得分字段
    "repurchase_rate_score": "复购率指标得分",
    "message_reply_rate_score": "消息回复率指标得分",
    "service_negative_feedback_score": "服务负反馈率指标得分",
    "food_safety_negative_feedback_score": "食品安全负反馈率指标得分",

    # 回复率字段
    "five_min_reply_rate": None,
    "one_min_reply_rate": None,
    "message_reply_rate": "消息回复率",
    "food_safety_negative_feedback_rate": "食品安全负反馈率",

    # 时间字段
    "basic_duration": "基础营业时长",

    # 完成率字段
    "meal_completion_report_rate": "出餐完成上报率",
}
```

#### 5.3.2 饿了么平台映射

```python
"eleme": {
    # 基础信息字段
    "date": "日期",
    "brand_store_name": None,
    "platform_store_name": "门店名称",
    "store_id": "门店编号",
    "city": "城市名称",

    # 财务指标字段
    "actual_income": "收入",
    "expense": "支出",
    "turnover": "营业额",
    "net_margin_rate": None,
    "original_price": None,
    "packaging_fee": "打包费",
    "customer_delivery_fee": "商家应收配送费",
    "customer_paid": "顾客实付总额",
    "avg_paid_price": "单均实付",
    "activity_subsidy": "活动补贴",
    "platform_service_fee": "平台技术服务费",
    "real_actual_income": None,
    "promotion_cost": None,
    "gift_sausage_cost": None,
    "real_net_margin_rate": None,

    # 订单数量字段
    "valid_orders": "有效订单",
    "invalid_orders": "无效订单",
    "merchant_cancelled_orders": "商责退单数",

    # 转化率字段
    "merchant_cancellation_rate": "商责取消率",
    "store_entry_rate": "进店转化率",
    "order_conversion_rate": "下单转化率",
    "new_customer_entry_rate": "新客进店转化率",
    "new_customer_order_rate": "新客下单转化率",
    "old_customer_entry_rate": "老客进店转化率",
    "old_customer_order_rate": "老客下单转化率",
    "repurchase_rate": "近30日复购率",

    # 流量数据字段
    "exposure_count": "曝光人数",
    "entry_count": "进店人数",
    "exposure_new_customer": "新客曝光人数",
    "entry_new_customer": "新客进店人数",
    "exposure_old_customer": "老客曝光人数",
    "entry_old_customer": "老客进店人数",
    "exposure_times": "曝光次数",
    "entry_times": "进店次数",
    "order_people": "下单人数",
    "order_new_customer": "新客下单人数",
    "order_old_customer": "老客下单人数",
    "uv": None,

    # 评分字段
    "new_merchant_score": "店铺评分",
    "peak_duration_score": "高峰营业时长得分",
    "quality_product_rate_score": "优质商品率得分",
    "activity_richness_score": "有效活动丰富度得分",
    "reject_order_rate_score": "商家不接单率得分",
    "bad_review_reply_rate_score": "差评回复率得分",
    "online_reply_rate_score": "在线联系回复率得分",
    "menu_richness_score": "菜单丰富度得分",
    "decoration_richness_score": "装修丰富度得分",
    "service_function_score": "昨日服务功能丰富度指标得分",
    "product_quality_score": None,
    "service_experience_score": None,
    "product_satisfaction": None,
    "packaging_satisfaction": None,

    # 指标得分字段
    "repurchase_rate_score": None,
    "message_reply_rate_score": None,
    "service_negative_feedback_score": None,
    "food_safety_negative_feedback_score": None,

    # 回复率字段
    "five_min_reply_rate": None,
    "one_min_reply_rate": None,
    "message_reply_rate": None,
    "food_safety_negative_feedback_rate": None,

    # 时间字段
    "basic_duration": "营业时长",

    # 完成率字段
    "meal_completion_report_rate": "近7日出餐完成上报率当前值",
}
```

#### 5.3.3 京东平台映射

```python
"jd": {
    # 基础信息字段
    "date": "日期",
    "brand_store_name": None,
    "platform_store_name": "门店名称",
    "store_id": "门店id",
    "city": "门店所在城市",
    
    # 财务指标字段
    "actual_income": "营业收入",
    "expense": "补贴及支出",
    "turnover": "优惠前总额",
    "original_price": "商品原价",
    "packaging_fee": "包装费",
    "customer_delivery_fee": "顾客配送费（跑腿/自配送）",
    "customer_paid": "顾客实付",
    "avg_paid_price": "实付单均价",
    "activity_subsidy": "活动补贴",
    "platform_service_fee": "平台服务费(含佣金和配送服务费)",
    "net_margin_rate": None,
    "real_actual_income": None,
    "promotion_cost": None,
    "gift_sausage_cost": None,
    "real_net_margin_rate": None,
    
    # 订单数量字段
    "valid_orders": "有效订单",
    "invalid_orders": "取消订单",
    "merchant_cancelled_orders": "商责取消订单",
    
    # 转化率字段
    "store_entry_rate": "入店转化率",
    "order_conversion_rate": "下单转化率",
    "merchant_cancellation_rate": "商责取消率",
    "new_customer_entry_rate": "新客入店转化率",
    "new_customer_order_rate": "新客下单转化率",
    "old_customer_entry_rate": "老客入店转化率",
    "old_customer_order_rate": "老客下单转化率",
    "repurchase_rate": "复购率",
    
    # 流量数据字段
    "exposure_count": "曝光人数",
    "entry_count": "入店人数",
    "exposure_times": "曝光次数",
    "entry_times": "入店次数",
    "exposure_new_customer": "曝光新客",
    "entry_new_customer": "入店新客",
    "exposure_old_customer": "曝光老客",
    "entry_old_customer": "入店老客",
    "order_people": "下单人数",
    "order_new_customer": "下单新客",
    "order_old_customer": "下单老客",
    "uv": None,
    
    # 评分字段
    "store_score": "店铺分",
    "peak_duration_score": "高峰营业时长得分",
    "quality_product_rate_score": "优质商品率得分",
    "activity_richness_score": "有效活动丰富度得分",
    "reject_order_rate_score": "商家不接单率得分",
    "bad_review_reply_rate_score": "差评回复率得分",
    "online_reply_rate_score": "在线联系回复率得分",
    "new_merchant_score": "综合体验分",
    "menu_richness_score": "菜单丰富度得分",
    "decoration_richness_score": "装修丰富度得分",
    "service_function_score": None,
    "product_quality_score": None,
    "service_experience_score": None,
    "product_satisfaction": None,
    "packaging_satisfaction": None,
    
    # 指标得分字段
    "repurchase_rate_score": None,
    "message_reply_rate_score": None,
    "service_negative_feedback_score": None,
    "food_safety_negative_feedback_score": None,
    
    # 回复率字段
    "message_reply_rate": None,
    "food_safety_negative_feedback_rate": None,
    
    # 时间字段
    "basic_duration": "日均营业时长",
    
    # 完成率字段
    "meal_completion_report_rate": None,
    
    # 未提供字段（设置为 None）
    "overall_experience_score": None,
    "old_merchant_score": None,
}
```

### 5.4 字段数据类型映射

定义在 `FIELD_TYPES` 字典中，用于数据类型转换：

```python
FIELD_TYPES = {
    # 日期类型
    "date": "date",

    # 字符串类型
    "brand_store_name": "str",
    "platform_store_name": "str",
    "platform": "str",

    # 金额类型（使用Decimal）
    "actual_income": "decimal",
    "expense": "decimal",
    "turnover": "decimal",
    "net_margin_rate": "decimal",
    "original_price": "decimal",
    "packaging_fee": "decimal",
    "customer_delivery_fee": "decimal",
    "customer_paid": "decimal",
    "avg_paid_price": "decimal",
    "activity_subsidy": "decimal",
    "platform_service_fee": "decimal",
    "real_actual_income": "decimal",
    "promotion_cost": "decimal",
    "gift_sausage_cost": "decimal",
    "real_net_margin_rate": "decimal",

    # 整数类型
    "valid_orders": "int",
    "invalid_orders": "int",
    "merchant_cancelled_orders": "int",
    "exposure_count": "int",
    "entry_count": "int",
    "exposure_new_customer": "int",
    "entry_new_customer": "int",
    "exposure_old_customer": "int",
    "entry_old_customer": "int",
    "exposure_times": "int",
    "entry_times": "int",
    "order_people": "int",
    "order_new_customer": "int",
    "order_old_customer": "int",
    "uv": "int",

    # 百分比类型（Decimal）
    "merchant_cancellation_rate": "decimal",
    "store_entry_rate": "decimal",
    "order_conversion_rate": "decimal",
    "new_customer_entry_rate": "decimal",
    "new_customer_order_rate": "decimal",
    "old_customer_entry_rate": "decimal",
    "old_customer_order_rate": "decimal",
    "repurchase_rate": "decimal",
    "five_min_reply_rate": "decimal",
    "one_min_reply_rate": "decimal",
    "message_reply_rate": "decimal",
    "food_safety_negative_feedback_rate": "decimal",
    "meal_completion_report_rate": "decimal",

    # 评分类型（Decimal）
    "store_score": "decimal",
    "peak_duration_score": "decimal",
    "quality_product_rate_score": "decimal",
    "activity_richness_score": "decimal",
    "reject_order_rate_score": "decimal",
    "bad_review_reply_rate_score": "decimal",
    "online_reply_rate_score": "decimal",
    "new_merchant_score": "decimal",
    "menu_richness_score": "decimal",
    "decoration_richness_score": "decimal",
    "service_function_score": "decimal",
    "overall_experience_score": "decimal",
    "product_quality_score": "decimal",
    "service_experience_score": "decimal",
    "product_satisfaction": "decimal",
    "packaging_satisfaction": "decimal",
    "old_merchant_score": "decimal",
    "repurchase_rate_score": "decimal",
    "message_reply_rate_score": "decimal",
    "service_negative_feedback_score": "decimal",
    "food_safety_negative_feedback_score": "decimal",

    # 时长类型（Decimal）
    "basic_duration": "decimal",

    # 系统字段
    "import_time": "datetime",
}
```

### 5.5 关键跨平台差异对比

| 目标字段 | 美团源列名 | 饿了么源列名 | 京东源列名 | 备注 |
|----------|-----------|-------------|-----------|------|
| `actual_income` | 营业收入 | 收入 | 营业收入 | - |
| `turnover` | 优惠前总额 | 营业额 | 优惠前总额 | - |
| `expense` | 补贴及支出 | 支出 | 补贴及支出 | - |
| `store_entry_rate` | 入店转化率 | 进店转化率 | 入店转化率 | 饿了么叫"进店" |
| `entry_count` | 入店人数 | 进店人数 | 入店人数 | 饿了么叫"进店" |
| `customer_paid` | 顾客实付 | 顾客实付总额 | 顾客实付 | 饿了么多了"总额" |
| `packaging_fee` | 包装费 | 打包费 | 包装费 | - |
| `platform_service_fee` | 平台服务费(含佣金和配送服务费) | 平台技术服务费 | 平台服务费(含佣金和配送服务费) | - |
| `merchant_cancelled_orders` | 商责取消订单 | 商责退单数 | 商责取消订单 | 饿了么叫"退单数" |
| `repurchase_rate` | 复购率 | 近30日复购率 | 复购率 | 饿了么多了"近30日" |
| `new_merchant_score` | overall_experience_score | 店铺评分 | 综合体验分 | 映射到不同字段 |
| `basic_duration` | 基础营业时长 | 营业时长 | 日均营业时长 | - |
| `meal_completion_report_rate` | 出餐完成上报率 | 近7日出餐完成上报率当前值 | None | 饿了么多了"近7日"和"当前值" |

---

## 6. ETL 数据处理流程

### 6.1 完整流程图

```
┌─────────────────────────────────────────────────────────┐
│  源数据                                                  │
│  ├── 美团: CSV文件，GBK编码                            │
│  ├── 饿了么: Excel文件，sheet名为'data'                 │
│  └── 京东: Excel文件，sheet名为'数据'                  │
└────────────────────┬────────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Step 1: 读取文件                                        │
│  - CSV → pd.read_csv(encoding='gbk')                   │
│  - Excel → pd.read_excel()                             │
│  - 自动检测表头行（通常为第0行）                         │
└────────────────────┬────────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Step 2: 字段映射                                        │
│  - 根据FIELD_MAPPING[platform]获取映射                  │
│  - 反向映射：中文列名 → 英文字段名                       │
│  - df.rename(columns=reverse_mapping)                  │
│  - 跳过None值（平台无此指标）                            │
└────────────────────┬────────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Step 3: 门店映射                                        │
│  - 读取platform_store_name列                            │
│  - 通过store_mapper获取brand_store_name                 │
│  - 过滤掉未映射的门店记录                                │
└────────────────────┬────────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Step 4: 数据清洗                                        │
│  - 日期标准化：整数格式 → DATE，字符串格式 → DATE       │
│  - 去除符号：%、¥、逗号等                                │
│  - 数值转换：字符串 → float/int                         │
│  - NaN → 0                                              │
│  - 百分比智能检测：小数格式 ×100 → 百分比格式           │
│  - 添加platform列（中文名：美团/饿了么/京东）            │
└────────────────────┬────────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Step 5: 数据验证                                        │
│  - 必需列检查：date, platform, brand_store_name         │
│  - 数值范围检查：百分比 0-100                            │
│  - 异常值检测：IQR 法（可选）                            │
└────────────────────┬────────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Step 6: 合并数据                                        │
│  - pd.concat() 合并三平台数据                            │
│  - 统计各平台数据量和占比                                │
└────────────────────┬────────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Step 7: 数据入库                                        │
│  - 过滤列（只保留DB表中存在的列）                       │
│  - 添加import_time时间戳                                │
│  - 使用INSERT IGNORE跳过重复数据                        │
│  - 批量写入（1000条/批）                                 │
└────────────────────┬────────────────────────────────────┘
                     ▼
              MySQL: waimai_db.daily_orders
```

### 6.2 关键步骤详解

#### Step 1: 读取文件

```python
def read_excel_file(platform, filepath, header=0):
    """
    读取Excel文件或CSV文件
    
    Args:
        platform: 平台名称
        filepath: 文件路径
        header: 表头所在行索引，默认0
    
    Returns:
        DataFrame 或 None (读取失败时)
    """
    try:
        if filepath.endswith('.csv'):
            # 美团CSV使用GBK编码
            df = pd.read_csv(filepath, header=header, encoding='gbk')
        else:
            # Excel文件
            df = pd.read_excel(filepath, header=header)
        return df
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return None
```

#### Step 2: 字段映射

```python
# 获取平台专属的字段映射
platform_mapping = FIELD_MAPPING.get(mapping_key, {})

# 构建反向映射：中文列名 -> 英文字段名（跳过 None 值）
reverse_mapping = {v: k for k, v in platform_mapping.items() if v is not None}

# 重命名列
df_processed = df.rename(columns=reverse_mapping)
```

#### Step 3: 门店映射

```python
if 'platform_store_name' in df_processed.columns:
    store_mapper = get_store_mapper()
    
    brand_store_names = []
    for idx, row in df_processed.iterrows():
        platform_store = row['platform_store_name']
        brand_store = store_mapper.get_brand_store_name(platform_name, platform_store)
        brand_store_names.append(brand_store)
    
    df_processed['brand_store_name'] = brand_store_names
    
    # 过滤掉未映射的门店记录
    df_processed = df_processed[df_processed['brand_store_name'].notna()]
```

#### Step 4: 数据清洗

**日期标准化**：

```python
if 'date' in df_processed.columns:
    dtype = df_processed['date'].dtype
    
    if dtype in ['int64', 'int32']:
        # 美团：整数格式（如 20260112）
        df_processed['date'] = pd.to_datetime(
            df_processed['date'].astype(str), 
            format='%Y%m%d', 
            errors='coerce'
        ).dt.date
    else:
        # 饿了么/京东：字符串格式（如 '2026-01-12'）
        df_processed['date'] = pd.to_datetime(
            df_processed['date'], 
            errors='coerce'
        ).dt.date
```

**百分比智能检测和转换**：

```python
# 清洗百分比列（包含中文"率"或"转化"的列名）
percentage_cols = [col for col in df_processed.columns if ('率' in str(col) or '转化' in str(col))]

for col in percentage_cols:
    if df_processed[col].dtype == 'object':
        # 清理字符串
        df_processed[col] = (
            df_processed[col].astype(str)
            .str.replace('%', '', regex=False)
            .str.replace(',', '', regex=False)
            .str.replace('nan', '0', regex=False)
            .str.strip()
        )
        df_processed[col] = pd.to_numeric(df_processed[col], errors='coerce').fillna(0)
    
    # 智能检测并统一转换率为百分比格式（0-100）
    non_zero_values = df_processed[col][df_processed[col] > 0]
    
    if len(non_zero_values) > 0:
        # 检查大部分值是否小于1（小数格式）
        values_less_than_1 = (non_zero_values < 1).sum()
        ratio = values_less_than_1 / len(non_zero_values)
        
        # 如果超过80%的值小于1，则认为是小数格式，需要转换
        if ratio > 0.8:
            df_processed[col] = df_processed[col] * 100
```

**数值清洗**：

```python
# 清洗数值列
numeric_columns = df_processed.select_dtypes(include=['float64', 'int64']).columns
for col in numeric_columns:
    df_processed[col] = pd.to_numeric(df_processed[col], errors='coerce').fillna(0)
```

**添加平台标识**：

```python
df_processed['platform'] = platform_name  # 使用中文名：美团/饿了么/京东
```

#### Step 5: 数据验证

```python
# 简化验证：只检查必需列
required_columns = ['date', 'platform', 'brand_store_name']
missing_cols = [col for col in required_columns if col not in df_processed.columns]

if missing_cols:
    print(f"⚠️  数据缺少必需列: {missing_cols}")
    return None

# 验证百分比列的值是否在合理范围内（0-100）
for col in percentage_cols:
    if col in df_processed.columns:
        out_of_range = df_processed[(df_processed[col] < 0) | (df_processed[col] > 100)]
        if len(out_of_range) > 0:
            df_processed[col] = df_processed[col].clip(0, 100)
```

#### Step 6: 合并数据

```python
# 合并所有平台数据
merged_df = pd.concat(processed_dataframes, ignore_index=True)

# 按平台分组统计
for platform in merged_df['platform'].unique():
    count = len(merged_df[merged_df['platform'] == platform])
    percentage = count / len(merged_df) * 100
    print(f"   {platform:10s}: {count:5d} 行 ({percentage:5.2f}%)")
```

#### Step 7: 数据入库

```python
# 只保留数据库存在的列
db_columns = set(['date', 'platform', 'brand_store_name', ...])  # 从DESCRIBE获取
df_columns = set(df.columns)
final_columns = list(df_columns & db_columns)
df_to_import = df[final_columns]

# 添加导入时间
df_to_import['import_time'] = datetime.now()

# 将NaN替换为None（MySQL不接受NaN）
df_to_import = df_to_import.replace({float('nan'): None})

# 使用 INSERT IGNORE 自动跳过重复数据
from sqlalchemy.dialects.mysql import insert

for chunk_start in range(0, len(df_to_import), BATCH_SIZE):
    chunk = df_to_import.iloc[chunk_start:chunk_start+BATCH_SIZE]
    
    with engine.connect() as conn:
        insert_stmt = text(f"""
            INSERT IGNORE INTO {table_name}
            ({', '.join([f'`{col}`' for col in chunk.columns])})
            VALUES ({', '.join([':' + col for col in chunk.columns])})
        """)
        
        result = conn.execute(insert_stmt, chunk.to_dict('records'))
        conn.commit()
```

### 6.3 文件配置

在 `etl/core/etl_main.py` 中定义要处理的文件列表：

```python
FILES_TO_PROCESS = [
    (PLATFORM_MEITUAN, 'meituan', 'path/to/meituan.csv', 0),
    (PLATFORM_ELEME, 'eleme', 'path/to/eleme.xlsx', 0),
    (PLATFORM_JD, 'jd', 'path/to/jd.xlsx', 0),
]
```

格式：`(平台中文名, 平台映射key, 文件路径, 表头行索引)`

---

## 7. 核心模块说明

### 7.1 配置模块：etl/config/config.py

**文件路径**：`etl/config/config.py`

**功能**：统一管理所有配置，支持环境变量覆盖。

**完整代码**：

```python
"""
外卖数据看板 - 统一配置文件
所有数据库连接、文件路径、常量均在此处集中管理
"""
import os

# ========== 数据库配置 ==========
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', '1203'),  # 请修改为实际密码
    'database': os.getenv('DB_NAME', 'waimai_db'),
}

# SQLAlchemy 连接字符串
def get_connection_string():
    return (
        f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        f"?charset=utf8mb4"
    )

# ========== 数据库表名 ==========
TABLE_NAME = 'daily_orders'

# ========== 平台名称（中文，与数据库一致）==========
PLATFORM_MEITUAN = '美团'
PLATFORM_ELEME = '饿了么'
PLATFORM_JD = '京东'
ALL_PLATFORMS = [PLATFORM_MEITUAN, PLATFORM_ELEME, PLATFORM_JD]

# ========== ETL 批处理配置 ==========
BATCH_SIZE = 1000
DUPLICATE_CHECK_DAYS = 90  # 去重检查回溯天数

# ========== 项目根目录 ==========
CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
ETL_DIR = os.path.dirname(CONFIG_DIR)
PROJECT_ROOT = os.path.dirname(ETL_DIR)

# ========== 目录配置 ==========
LOG_DIR = os.path.join(PROJECT_ROOT, 'logs')
DATA_DIR = os.path.join(PROJECT_ROOT, 'etl', 'data')
SOURCES_DIR = os.path.join(DATA_DIR, 'sources')
BACKUP_DIR = os.path.join(DATA_DIR, 'backup')
REPORTS_DIR = os.path.join(PROJECT_ROOT, 'etl', 'reports')

# 确保目录存在
for directory in [LOG_DIR, DATA_DIR, SOURCES_DIR, BACKUP_DIR, REPORTS_DIR]:
    os.makedirs(directory, exist_ok=True)

# ========== 日志配置 ==========
LOG_FORMAT = '%(asctime)s [%(levelname)s] %(name)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
```

**使用方式**：

```python
from etl.config import (
    DB_CONFIG, 
    get_connection_string, 
    TABLE_NAME, 
    PLATFORM_MEITUAN,
    LOG_DIR
)

# 创建数据库连接
engine = create_engine(get_connection_string())

# 使用配置
print(f"表名: {TABLE_NAME}")
print(f"平台: {PLATFORM_MEITUAN}")
```

### 7.2 字段映射模块：etl/core/field_mapping.py

**文件路径**：`etl/core/field_mapping.py`

**功能**：定义三个平台的字段映射关系和数据类型映射。

**关键内容**：

1. `FIELD_MAPPING`：三平台字段映射字典（详见第5章）
2. `FIELD_TYPES`：字段数据类型映射（详见第5.4节）

**使用方式**：

```python
from etl.core.field_mapping import FIELD_MAPPING, FIELD_TYPES

# 获取平台映射
meituan_mapping = FIELD_MAPPING['meituan']

# 构建反向映射用于重命名列
reverse_mapping = {v: k for k, v in meituan_mapping.items() if v is not None}
df = df.rename(columns=reverse_mapping)

# 检查字段类型
field_type = FIELD_TYPES['actual_income']  # 返回 'decimal'
```

### 7.3 ETL主程序：etl/core/etl_main.py

**文件路径**：`etl/core/etl_main.py`

**功能**：完整的ETL流程实现。

**主要函数**：

#### 7.3.1 create_database_engine()

创建数据库连接引擎。

```python
def create_database_engine():
    """
    创建数据库连接引擎
    """
    engine = create_engine(
        get_connection_string(),
        echo=False,
        pool_size=5,
        max_overflow=10,
        pool_recycle=3600
    )
    return engine
```

#### 7.3.2 test_database_connection(engine)

测试数据库连接。

```python
def test_database_connection(engine):
    """
    测试数据库连接是否正常
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ 数据库连接成功")
            return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False
```

#### 7.3.3 read_excel_file(platform, filepath, header=0)

读取Excel或CSV文件。

```python
def read_excel_file(platform, filepath, header=0):
    """
    读取Excel文件或CSV文件
    """
    try:
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath, header=header, encoding='gbk')
        else:
            df = pd.read_excel(filepath, header=header)
        return df
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return None
```

#### 7.3.4 process_single_file(platform_name, mapping_key, filepath, header=0)

处理单个文件：读取 → 清洗 → 验证 → 门店映射。

```python
def process_single_file(platform_name, mapping_key, filepath, header=0):
    """
    处理单个文件：读取 -> 清洗 -> 验证 -> 门店映射
    """
    # 读取文件
    df = read_excel_file(platform_name, filepath, header)
    if df is None:
        return None

    # 数据清洗和计算
    try:
        # 获取平台专属的字段映射
        platform_mapping = FIELD_MAPPING.get(mapping_key, {})
        
        # 构建反向映射
        reverse_mapping = {v: k for k, v in platform_mapping.items() if v is not None}
        df_processed = df.rename(columns=reverse_mapping)
        
        # 门店映射处理
        if 'platform_store_name' in df_processed.columns:
            store_mapper = get_store_mapper()
            brand_store_names = []
            
            for idx, row in df_processed.iterrows():
                platform_store = row['platform_store_name']
                brand_store = store_mapper.get_brand_store_name(platform_name, platform_store)
                brand_store_names.append(brand_store)
            
            df_processed['brand_store_name'] = brand_store_names
            df_processed = df_processed[df_processed['brand_store_name'].notna()]
        
        # 日期标准化
        if 'date' in df_processed.columns:
            dtype = df_processed['date'].dtype
            
            if dtype in ['int64', 'int32']:
                df_processed['date'] = pd.to_datetime(
                    df_processed['date'].astype(str), 
                    format='%Y%m%d', 
                    errors='coerce'
                ).dt.date
            else:
                df_processed['date'] = pd.to_datetime(df_processed['date'], errors='coerce').dt.date
        
        # 添加平台标识
        df_processed['platform'] = platform_name
        
        # 清洗数值列
        numeric_columns = df_processed.select_dtypes(include=['float64', 'int64']).columns
        for col in numeric_columns:
            df_processed[col] = pd.to_numeric(df_processed[col], errors='coerce').fillna(0)
        
        # 清洗百分比列
        percentage_cols = [col for col in df_processed.columns if ('率' in str(col) or '转化' in str(col))]
        for col in percentage_cols:
            if df_processed[col].dtype == 'object':
                df_processed[col] = (
                    df_processed[col].astype(str)
                    .str.replace('%', '', regex=False)
                    .str.replace(',', '', regex=False)
                    .str.strip()
                )
                df_processed[col] = pd.to_numeric(df_processed[col], errors='coerce').fillna(0)
            
            # 智能检测并转换百分比格式
            non_zero_values = df_processed[col][df_processed[col] > 0]
            if len(non_zero_values) > 0:
                values_less_than_1 = (non_zero_values < 1).sum()
                ratio = values_less_than_1 / len(non_zero_values)
                
                if ratio > 0.8:
                    df_processed[col] = df_processed[col] * 100
        
        # 验证必需列
        required_columns = ['date', 'platform', 'brand_store_name']
        missing_cols = [col for col in required_columns if col not in df_processed.columns]
        
        if missing_cols:
            print(f"⚠️  数据缺少必需列: {missing_cols}")
            return None
        
        return df_processed

    except Exception as e:
        print(f"❌ 数据清洗失败: {e}")
        return None
```

#### 7.3.5 save_to_database(df, engine, table_name)

将DataFrame保存到数据库。

```python
def save_to_database(df, engine, table_name):
    """
    将DataFrame保存到数据库（使用 INSERT IGNORE 自动跳过重复数据）
    """
    try:
        # 获取数据库列名
        with engine.connect() as conn:
            result = conn.execute(text(f"DESCRIBE {table_name}"))
            db_columns = set(row[0] for row in result)
        
        # 只保留数据库存在的列
        df_columns = set(df.columns)
        final_columns = list(df_columns & db_columns)
        df_to_import = df[final_columns]
        
        # 添加导入时间
        if 'import_time' in df_to_import.columns:
            df_to_import = df_to_import.drop(columns=['import_time'])
        df_to_import['import_time'] = datetime.now()
        
        # 将NaN替换为None
        df_to_import = df_to_import.replace({float('nan'): None})
        
        # 分批写入
        rows_inserted = 0
        rows_skipped = 0
        
        for chunk_start in range(0, len(df_to_import), BATCH_SIZE):
            chunk_end = min(chunk_start + BATCH_SIZE, len(df_to_import))
            chunk = df_to_import.iloc[chunk_start:chunk_end]
            
            with engine.connect() as conn:
                insert_stmt = text(f"""
                    INSERT IGNORE INTO {table_name}
                    ({', '.join([f'`{col}`' for col in chunk.columns])})
                    VALUES ({', '.join([':' + col for col in chunk.columns])})
                """)
                
                result = conn.execute(insert_stmt, chunk.to_dict('records'))
                rows_inserted += result.rowcount
                conn.commit()
        
        rows_skipped = len(df_to_import) - rows_inserted
        print(f"   ✅ 导入完成:")
        print(f"      - 成功插入: {rows_inserted} 条")
        print(f"      - 跳过重复: {rows_skipped} 条")
        
        return True

    except Exception as e:
        print(f"❌ 写入数据库失败: {e}")
        return False
```

#### 7.3.6 main()

主函数：完整的ETL流程。

```python
def main():
    """
    主函数：完整的ETL流程
    """
    print("\n" + "="*60)
    print("🍔 外卖数据看板 ETL 主程序")
    print(f"{'='*60}")
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 步骤1: 创建数据库连接
    print(f"\n📡 步骤 1/4: 创建数据库连接...")
    engine = create_database_engine()

    if not test_database_connection(engine):
        print("\n❌ 无法连接数据库，程序退出")
        sys.exit(1)

    # 步骤2: 读取和处理所有文件
    print(f"\n📂 步骤 2/4: 读取和处理Excel文件...")

    processed_dataframes = []
    success_count = 0
    failed_platforms = []

    for platform_name, mapping_key, filepath, header in FILES_TO_PROCESS:
        try:
            processed_df = process_single_file(platform_name, mapping_key, filepath, header)
            if processed_df is not None:
                processed_dataframes.append(processed_df)
                success_count += 1
            else:
                failed_platforms.append(platform_name)
        except Exception as e:
            print(f"❌ 处理 {platform_name} 时发生异常: {e}")
            failed_platforms.append(platform_name)
            continue

    if len(processed_dataframes) == 0:
        print("\n❌ 所有文件处理失败，程序退出")
        sys.exit(1)

    # 步骤3: 合并数据
    print(f"\n🔗 步骤 3/4: 合并所有平台数据...")

    merged_df = pd.concat(processed_dataframes, ignore_index=True)
    print(f"✅ 数据合并完成，共 {len(merged_df)} 行 {len(merged_df.columns)} 列")

    # 按平台分组统计
    print(f"\n📈 各平台数据量统计:")
    for platform in merged_df['platform'].unique():
        count = len(merged_df[merged_df['platform'] == platform])
        percentage = count / len(merged_df) * 100
        print(f"   {platform:10s}: {count:5d} 行 ({percentage:5.2f}%)")

    # 步骤4: 写入数据库
    print(f"\n💾 步骤 4/4: 写入数据库...")

    if not save_to_database(merged_df, engine, TABLE_NAME):
        print("\n❌ 数据入库失败，程序退出")
        sys.exit(1)

    # 完成
    print(f"\n{'='*60}")
    print(f"🎉 ETL 流程完成！")
    print(f"{'='*60}")
    print(f"⏰ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 总计处理: {len(merged_df)} 条记录")
    print(f"📋 写入表名: {TABLE_NAME}")
```

### 7.4 门店映射模块：etl/core/store_mapper.py

**文件路径**：`etl/core/store_mapper.py`

**功能**：处理平台门店名称到品牌门店名称的映射。

**主要功能**：

1. 读取门店映射配置
2. 根据平台和平台门店名称查找品牌门店名称
3. 记录未映射的门店
4. 生成未映射门店报告

**使用方式**：

```python
from etl.core.store_mapper import get_store_mapper

# 获取门店映射器实例
store_mapper = get_store_mapper()

# 获取品牌门店名称
brand_store = store_mapper.get_brand_store_name('美团', '平台门店名称')

# 记录未映射门店
store_mapper.log_unmapped_stores()
```

---

## 8. Dashboard 看板功能

### 8.1 主页：app.py

**文件路径**：`app.py`

**功能**：Streamlit 仪表盘主页，展示核心经营指标。

#### 8.1.1 侧边栏筛选器

```python
import streamlit as st

# 侧边栏标题
st.sidebar.header("📊 数据筛选")

# 日期范围选择器
date_range = st.sidebar.date_input(
    "选择日期范围",
    value=[start_date, end_date],
    max_value=today
)

# 平台多选
platforms = st.sidebar.multiselect(
    "选择平台",
    options=ALL_PLATFORMS,  # ['美团', '饿了么', '京东']
    default=ALL_PLATFORMS
)

# 门店多选
stores = st.sidebar.multiselect(
    "选择门店",
    options=store_list,
    default=store_list
)
```

#### 8.1.2 周累计指标卡片

```python
# 周累计指标
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="周曝光人数",
        value=f"{total_exposure:,}",
        delta=f"{exposure_change:+.1%}"
    )

with col2:
    st.metric(
        label="周进店率",
        value=f"{total_entry_rate:.2f}%",
        delta=f"{entry_rate_change:+.2f}个百分点"
    )

with col3:
    st.metric(
        label="周下单率",
        value=f"{total_order_rate:.2f}%",
        delta=f"{order_rate_change:+.2f}个百分点"
    )

with col4:
    st.metric(
        label="周到手率",
        value=f"{total_margin_rate:.2f}%",
        delta=f"{margin_rate_change:+.2f}个百分点"
    )
```

#### 8.1.3 周环比对比

```python
# 周环比对比
st.subheader("📈 周环比对比")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="有效订单",
        value=f"{current_week_orders:,}",
        delta=f"{orders_change:+.1%}",
        delta_color="normal"
    )

with col2:
    st.metric(
        label="商家实收（元）",
        value=f"¥{current_week_income:,.2f}",
        delta=f"{income_change:+.1%}",
        delta_color="normal"
    )

with col3:
    st.metric(
        label="到手率",
        value=f"{current_week_rate:.2f}%",
        delta=f"{rate_change:+.2f}个百分点",
        delta_color="normal"
    )
```

#### 8.1.4 趋势图表

```python
import plotly.express as px

# 分平台营收趋势
fig_revenue = px.line(
    df_weekly,
    x='date',
    y='actual_income',
    color='platform',
    title='分平台营收趋势',
    labels={'actual_income': '实收金额（元）', 'date': '日期'}
)

st.plotly_chart(fig_revenue, use_container_width=True)

# 分平台单量趋势
fig_orders = px.line(
    df_weekly,
    x='date',
    y='valid_orders',
    color='platform',
    title='分平台单量趋势',
    labels={'valid_orders': '有效订单数', 'date': '日期'}
)

st.plotly_chart(fig_orders, use_container_width=True)
```

#### 8.1.5 平台占比分析

```python
# 真实实收占比（环形图）
fig_pie = px.pie(
    df_platform,
    values='real_actual_income',
    names='platform',
    title='平台真实实收占比',
    hole=0.4
)

st.plotly_chart(fig_pie, use_container_width=True)

# 平均客单价对比（柱状图）
fig_bar = px.bar(
    df_platform,
    x='platform',
    y='avg_paid_price',
    title='平台平均客单价对比',
    labels={'avg_paid_price': '客单价（元）', 'platform': '平台'}
)

st.plotly_chart(fig_bar, use_container_width=True)
```

#### 8.1.6 数据缓存

```python
@st.cache_data(ttl=600)  # 缓存10分钟
def load_data():
    """加载数据，带缓存"""
    engine = create_engine(get_connection_string())
    
    query = f"""
    SELECT * FROM {TABLE_NAME}
    WHERE `date` >= '{start_date}' AND `date` <= '{end_date}'
    """
    
    df = pd.read_sql(query, engine)
    return df
```

### 8.2 周报页：pages/1_周报数据.py

**文件路径**：`pages/1_周报数据.py`

**功能**：展示详细的周报数据表格。

#### 8.2.1 每日汇总表

```python
st.subheader("📅 每日汇总")

columns_daily = [
    'date', 'turnover', 'actual_income', 'net_margin_rate',
    'valid_orders', 'avg_paid_price', 'invalid_orders'
]

df_daily = df_filtered[columns_daily].copy()
df_daily['date'] = pd.to_datetime(df_daily['date']).dt.strftime('%Y-%m-%d')
df_daily['net_margin_rate'] = df_daily['net_margin_rate'].round(2)

st.dataframe(
    df_daily,
    use_container_width=True,
    hide_index=True
)
```

#### 8.2.2 门店核心指标表

```python
st.subheader("🏪 门店核心指标")

columns_core = [
    'date', 'store_score', 'new_merchant_score', 'five_min_reply_rate',
    'one_min_reply_rate', 'meal_completion_report_rate',
    'merchant_cancelled_orders', 'basic_duration',
    'bad_review_reply_rate_score'
]

df_core = df_filtered[columns_core].copy()

st.dataframe(
    df_core,
    use_container_width=True,
    hide_index=True
)
```

#### 8.2.3 线上过程指标表

```python
st.subheader("📱 线上过程指标")

columns_process = [
    'date', 'exposure_count', 'entry_count', 'store_entry_rate',
    'order_people', 'order_conversion_rate', 'promotion_cost',
    'output', 'roi', 'uv'
]

df_process = df_filtered[columns_process].copy()

st.dataframe(
    df_process,
    use_container_width=True,
    hide_index=True
)
```

---

## 9. 配置管理

### 9.1 环境变量支持

所有配置都支持通过环境变量覆盖：

```bash
export DB_HOST=localhost
export DB_PORT=3306
export DB_USER=root
export DB_PASSWORD=your_password
export DB_NAME=waimai_db
```

### 9.2 配置优先级

1. 环境变量（最高优先级）
2. config.py 中的默认值
3. 代码中的硬编码值（最低优先级，应避免）

### 9.3 敏感信息处理

数据库密码等敏感信息应通过环境变量传递，不应硬编码在代码中。

---

## 10. 开发约定

### 10.1 平台名称规范

- **数据库中存储**：中文名（美团/饿了么/京东）
- **代码中使用**：从 `config.py` 导入常量
- **禁止使用**：英文名称（meituan/eleme/jd）直接在代码中出现

**正确示例**：

```python
from etl.config import PLATFORM_MEITUAN, PLATFORM_ELEME, PLATFORM_JD

df['platform'] = PLATFORM_MEITUAN  # ✅ 正确
df['platform'] = '美团'            # ✅ 正确
df['platform'] = 'meituan'        # ❌ 错误
```

### 10.2 字段映射方向

- `FIELD_MAPPING` 中定义：`目标字段名`（英文）→ `中文源列名`
- 使用时需要反转：`中文源列名` → `目标字段名`（英文）

**反转示例**：

```python
platform_mapping = FIELD_MAPPING['meituan']
reverse_mapping = {v: k for k, v in platform_mapping.items() if v is not None}
df = df.rename(columns=reverse_mapping)
```

### 10.3 数据入库模式

- **使用**：`if_exists='append'` 或 `INSERT IGNORE`
- **禁止使用**：`if_exists='replace'`（会清空整张表）

### 10.4 去重策略

- **唯一标识**：`(date, platform, brand_store_name)` 三元组
- **实现方式**：数据库唯一约束 `UNIQUE KEY`
- **入库时**：使用 `INSERT IGNORE` 自动跳过重复数据

### 10.5 文件编码处理

- **美团 CSV**：GBK 编码
- **其他文件**：Excel 文件，由 openpyxl 自动处理编码
- **饿了么 Excel**：sheet 名为 `data`
- **京东 Excel**：sheet 名为 `数据`

**代码示例**：

```python
if filepath.endswith('.csv'):
    df = pd.read_csv(filepath, header=header, encoding='gbk')
else:
    df = pd.read_excel(filepath, header=header)
```

### 10.6 日期格式处理

- **美团**：整数格式（如 20260112），使用 `%Y%m%d` 解析
- **饿了么/京东**：字符串格式（如 '2026-01-12'），使用自动解析

**代码示例**：

```python
dtype = df['date'].dtype

if dtype in ['int64', 'int32']:
    # 美团：整数格式
    df['date'] = pd.to_datetime(
        df['date'].astype(str), 
        format='%Y%m%d', 
        errors='coerce'
    ).dt.date
else:
    # 饿了么/京东：字符串格式
    df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date
```

### 10.7 百分比处理

- **智能检测**：自动识别小数格式（0-1）和百分比格式（0-100）
- **统一转换**：所有百分比统一为 0-100 格式
- **阈值**：如果超过80%的值小于1，则认为是小数格式，乘以100转换

**代码示例**：

```python
# 检测并转换百分比格式
non_zero_values = df[col][df[col] > 0]

if len(non_zero_values) > 0:
    values_less_than_1 = (non_zero_values < 1).sum()
    ratio = values_less_than_1 / len(non_zero_values)
    
    # 如果超过80%的值小于1，则认为是小数格式，需要转换
    if ratio > 0.8:
        df[col] = df[col] * 100
```

---

## 11. 快速启动指南

### 11.1 环境准备

**系统要求**：
- Python 3.8 或更高版本
- MySQL 5.7 或更高版本
- 至少 2GB 可用内存
- 至少 1GB 可用磁盘空间

### 11.2 数据库初始化

**步骤1：创建数据库**

```bash
mysql -u root -p
```

在MySQL命令行中执行：

```sql
CREATE DATABASE waimai_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```

**步骤2：创建表结构**

```bash
mysql -u root -p waimai_db < etl/config/daily_orders_schema.sql
```

**步骤3：验证表结构**

```bash
mysql -u root -p waimai_db -e "DESCRIBE daily_orders;"
```

### 11.3 安装依赖

**步骤1：创建虚拟环境（推荐）**

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

**步骤2：安装依赖包**

```bash
pip install -r requirements.txt
```

**步骤3：验证安装**

```bash
python -c "import pandas, sqlalchemy, streamlit; print('所有依赖安装成功！')"
```

### 11.4 配置数据库连接

**方式1：修改配置文件（不推荐，仅用于开发）**

编辑 `etl/config/config.py`：

```python
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'your_password',  # 修改为实际密码
    'database': 'waimai_db',
}
```

**方式2：使用环境变量（推荐）**

创建 `.env` 文件：

```bash
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=waimai_db
```

然后在 `.bashrc` 或 `.zshrc` 中添加：

```bash
export $(cat .env | xargs)
```

### 11.5 准备源数据文件

将三个平台的导出文件放入 `etl/data/sources/下载源文件/` 目录：

```
etl/data/sources/下载源文件/
├── 美团数据.csv
├── 饿了么数据.xlsx
└── 京东数据.xlsx
```

### 11.6 运行ETL程序

**方式1：使用主程序**

```bash
python -m etl.core.etl_main
```

**方式2：使用启动脚本**

创建 `run_etl.sh`：

```bash
#!/bin/bash

echo "🍔 开始运行 ETL 程序..."

# 激活虚拟环境
source venv/bin/activate

# 运行ETL
python -m etl.core.etl_main

echo "✅ ETL 程序运行完成"
```

赋予权限并运行：

```bash
chmod +x run_etl.sh
./run_etl.sh
```

### 11.7 启动Dashboard

**方式1：使用streamlit命令**

```bash
streamlit run app.py
```

**方式2：使用启动脚本**

创建 `run_dashboard.sh`：

```bash
#!/bin/bash

echo "🎨 启动数据看板..."

# 激活虚拟环境
source venv/bin/activate

# 启动Streamlit
streamlit run app.py

echo "✅ 数据看板已启动"
```

赋予权限并运行：

```bash
chmod +x run_dashboard.sh
./run_dashboard.sh
```

### 11.8 访问Dashboard

打开浏览器，访问：

```
http://localhost:8501
```

### 11.9 常见问题排查

**问题1：数据库连接失败**

```bash
# 检查MySQL服务是否运行
sudo systemctl status mysql  # Linux
# 或
brew services list  # Mac

# 检查端口是否被占用
netstat -an | grep 3306

# 测试连接
mysql -u root -p -h localhost -P 3306 waimai_db
```

**问题2：模块导入错误**

```bash
# 确保在项目根目录
cd /path/to/20260210demo

# 检查Python路径
python -c "import sys; print('\n'.join(sys.path))"

# 重新安装依赖
pip install --upgrade -r requirements.txt
```

**问题3：文件读取失败**

```bash
# 检查文件是否存在
ls -lh etl/data/sources/下载源文件/

# 检查文件权限
chmod 644 etl/data/sources/下载源文件/*

# 检查文件编码
file -i etl/data/sources/下载源文件/美团数据.csv
```

**问题4：Streamlit无法启动**

```bash
# 检查端口是否被占用
lsof -i :8501

# 清除缓存
rm -rf .streamlit

# 重新启动
streamlit run app.py --server.port 8502
```

---

## 12. 关键文件依赖关系

```
config.py ←── 被所有模块导入
    │
field_mapping.py ←── 被 ETL 模块导入
    │
data_processor.py ←── 导入 config + field_mapping
    │
etl_main.py ←── 导入 config + field_mapping + data_processor（主 ETL 入口）
import_platform_source.py ←── 导入 config（平台原始文件导入）
validate_and_import.py ←── 导入 config（校验+导入）
store_mapper.py ←── 导入 config（门店映射）
    │
app.py ←── 导入 config（Dashboard 主页）
pages/1_周报数据.py ←── 导入 config（周报页）
```

**导入示例**：

```python
# etl/core/etl_main.py
from ..config import (
    DB_CONFIG, 
    get_connection_string, 
    TABLE_NAME, 
    PLATFORM_MEITUAN,
    PLATFORM_ELEME,
    PLATFORM_JD
)
from .field_mapping import FIELD_MAPPING, FIELD_TYPES
from .store_mapper import get_store_mapper

# app.py
from etl.config import (
    DB_CONFIG,
    get_connection_string,
    TABLE_NAME,
    ALL_PLATFORMS
)
```

---

## 13. 已完成功能清单

### 13.1 ETL 功能

- [x] 三平台 Excel/CSV 数据提取
- [x] 平台专属字段映射（美团 84 个字段、饿了么 70 个字段、京东 70 个字段）
- [x] 数据清洗（日期、数值、百分比、空值处理）
- [x] 百分比智能检测和转换（小数格式 ↔ 百分比格式）
- [x] 基于 (date, platform, brand_store_name) 的去重机制
- [x] 批量入库（append 模式，1000 条/批）
- [x] 统一配置管理（config.py）
- [x] 可复用工具模块（data_processor.py）
- [x] 门店映射处理（store_mapper.py）
- [x] 日志框架（文件 + 控制台输出）
- [x] 数据库唯一约束防重复
- [x] INSERT IGNORE 自动跳过重复数据

### 13.2 Dashboard 功能

- [x] Streamlit 主看板
- [x] 周报数据页
- [x] 侧边栏筛选器（日期范围、平台、门店）
- [x] KPI 卡片展示（曝光人数、进店率、下单率、到手率）
- [x] 周环比对比（有效订单、商家实收、到手率）
- [x] 历史到手率对比
- [x] 每日趋势图（分平台营收趋势、分平台单量趋势）
- [x] 平台占比分析（真实实收占比、平均客单价对比）
- [x] Tab 切换（每日趋势详情 / 原始数据表预览）
- [x] 10 分钟数据缓存
- [x] 数据表格展示（每日汇总、门店核心指标、线上过程指标）
- [x] 响应式布局（宽屏布局）

---

## 14. 已知问题和待优化

### 14.1 架构层面

**问题**：
- `import_data.py`、`import_platform_source.py`、`validate_and_import.py` 功能重叠，需要合并或明确分工
- 没有自动化测试（无 pytest、无 CI/CD）
- 没有定时调度（每次手动运行 ETL）

**待优化**：
- [ ] 重构导入模块，明确各文件职责
- [ ] 添加单元测试和集成测试
- [ ] 实现定时任务调度（使用 APScheduler 或 cron）
- [ ] 添加 Docker 支持

### 14.2 数据层面

**问题**：
- `real_actual_income`、`promotion_cost`、`gift_sausage_cost` 等计算字段尚未在 ETL 中自动计算
- 京东平台的字段覆盖率较低（很多字段映射为 None）
- `import_platform_source.py` 有更细粒度的映射，但这些额外字段未在 `daily_orders` 表中体现

**待优化**：
- [ ] 在 ETL 中实现计算字段的自动计算
- [ ] 扩充京东平台的字段映射
- [ ] 评估是否需要新增字段来存储细粒度数据
- [ ] 添加数据质量检查报告

### 14.3 Dashboard 层面

**问题**：
- 周报页的"线上过程指标"中 ROI 和产出的计算逻辑未实现
- 缺少门店维度的排名和对比分析
- 缺少数据导出功能
- 移动端适配不足
- 趋势图缺少移动平均线等高级分析

**待优化**：
- [ ] 实现 ROI 和产出的计算逻辑
- [ ] 添加门店排名功能
- [ ] 实现数据导出功能（Excel/CSV）
- [ ] 优化移动端布局
- [ ] 添加更多图表类型和高级分析功能
- [ ] 添加数据预警功能

### 14.4 代码质量

**问题**：
- 部分 print 语句未统一迁移到 logging
- 异常处理粒度较粗（部分 `except Exception`）
- `app.py` 中主页和 tab1 的图表代码有重复

**待优化**：
- [ ] 统一使用 logging 模块输出日志
- [ ] 细化异常处理，捕获特定异常
- [ ] 提取公共代码，减少重复
- [ ] 添加类型注解（type hints）
- [ ] 完善代码文档（docstring）

---

## 15. 附录

### 15.1 术语表

| 术语 | 说明 |
|------|------|
| ETL | Extract-Transform-Load，数据抽取、转换、加载 |
| Streamlit | Python 数据可视化框架，快速构建 Web 应用 |
| SQLAlchemy | Python SQL 工具包和 ORM 框架 |
| PyMySQL | MySQL 的 Python 驱动 |
| pandas | Python 数据分析库 |
| openpyxl | Python Excel 读写库 |
| 到手率 | 商家实收 / 营业额 × 100% |
| 商责取消率 | 商家原因导致的订单取消比例 |
| 入店转化率 | 进店人数 / 曝光人数 × 100% |
| 下单转化率 | 下单人数 / 进店人数 × 100% |

### 15.2 参考资源

**官方文档**：
- [Streamlit 文档](https://docs.streamlit.io/)
- [pandas 文档](https://pandas.pydata.org/docs/)
- [SQLAlchemy 文档](https://docs.sqlalchemy.org/)
- [MySQL 文档](https://dev.mysql.com/doc/)

**相关工具**：
- [Plotly 图表库](https://plotly.com/python/)
- [APScheduler 任务调度](https://apscheduler.readthedocs.io/)
- [pytest 测试框架](https://docs.pytest.org/)

### 15.3 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2025-02-10 | 初始版本，完成基础 ETL 和 Dashboard 功能 |

### 15.4 联系方式

如有问题或建议，请通过以下方式联系：

- 项目仓库：[待补充]
- 问题反馈：[待补充]
- 邮箱：[待补充]

---

**文档版本**：v1.0  
**最后更新**：2025-02-10  
**维护者**：[待补充]  
**许可证**：仅供学习交流使用