# 🍔 外卖数据看板系统

一个完整的外卖平台数据自动化处理与可视化系统，支持**美团、饿了么、京东**三个平台的数据清洗、计算、入库和可视化展示。

---

## ✨ 核心功能

- 📊 **多平台数据整合**：统一处理美团、饿了么、京东三个平台的数据
- 🔄 **自动化ETL流程**：一键完成数据提取、清洗、转换、入库
- 📈 **可视化看板**：基于 Streamlit 的实时数据仪表盘
- 🏪 **门店映射管理**：自动识别和映射各平台门店名称
- 🔒 **数据去重机制**：基于唯一约束防止重复导入

---

## 📁 项目结构

```
ZZDemo/
├── app.py                          # Streamlit 主看板
├── pages/                          # 多页面应用
│   ├── 1_周报数据.py               # 周报数据页
│   └── store_mapping_simple.py    # 门店映射页
│
├── etl/                            # ETL 模块
│   ├── config/                     # 配置文件
│   │   ├── config.py              # 统一配置
│   │   └── daily_orders_schema.sql # 数据库表结构
│   ├── core/                       # 核心模块
│   │   ├── etl_main.py            # ETL 主程序
│   │   ├── field_mapping.py       # 字段映射
│   │   ├── data_processor.py      # 数据处理
│   │   └── store_mapper.py        # 门店映射
│   ├── data/                       # 数据目录
│   │   └── sources/               # 源数据文件
│   └── scripts/                    # 工具脚本
│
├── docs/                           # 项目文档
│   ├── quickstart.md              # 快速启动指南
│   ├── project-specification.md   # 项目规格说明书
│   └── store-mapping-guide.md     # 门店映射指南
│
├── run_etl.py                      # ETL 入口脚本
├── run_dashboard.sh               # 看板启动脚本
└── requirements.txt               # Python 依赖
```

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 初始化数据库

```bash
mysql -u root -p -e "CREATE DATABASE waimai_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u root -p waimai_db < etl/config/daily_orders_schema.sql
```

### 3. 配置数据库连接

编辑 `etl/config/config.py` 或设置环境变量：

```bash
export DB_PASSWORD=your_password
```

### 4. 运行ETL导入数据

```bash
python run_etl.py
```

### 5. 启动数据看板

```bash
streamlit run app.py
# 或
./run_dashboard.sh
```

访问 http://localhost:8501 查看看板。

---

## 📊 数据看板功能

### 主页

- 📅 日期范围筛选
- 🏪 平台/门店多选
- 📈 周累计指标卡片（曝光、进店率、下单率、到手率）
- 📊 周环比对比（订单、实收、到手率）
- 📉 分平台趋势图
- 🥧 平台占比分析

### 周报页

- 📋 每日汇总表
- 🏆 门店核心指标
- 📱 线上过程指标

### 门店映射页

- 🗺️ 品牌门店与平台门店映射关系
- 📤 映射数据导出

---

## 🔧 技术栈

| 类别 | 技术 |
|------|------|
| 语言 | Python 3.8+ |
| 数据处理 | pandas, numpy |
| 数据库 | MySQL 5.7+, SQLAlchemy, PyMySQL |
| 前端 | Streamlit, Plotly |
| Excel处理 | openpyxl |

---

## 📖 文档

| 文档 | 说明 |
|------|------|
| [快速启动指南](docs/quickstart.md) | 快速上手项目 |
| [项目规格说明书](docs/project-specification.md) | 完整技术文档 |
| [门店映射指南](docs/store-mapping-guide.md) | 门店映射使用说明 |

---

## 📝 数据处理流程

```
源数据 (Excel/CSV)
    ↓
字段映射 (中文名 → 英文字段)
    ↓
数据清洗 (日期、数值、百分比)
    ↓
门店映射 (平台门店 → 品牌门店)
    ↓
去重检查 (唯一约束)
    ↓
入库 (MySQL daily_orders 表)
    ↓
可视化 (Streamlit 看板)
```

---

## ⚠️ 开发约定

- **平台名称**：数据库存储中文名（美团/饿了么/京东）
- **字段映射**：`英文目标字段 → 中文源列名`，使用时需反转
- **入库模式**：始终使用 `append`，禁止使用 `replace`
- **去重策略**：`(date, platform, brand_store_name)` 唯一约束

---

## 📄 许可证

本项目仅供学习交流使用。

---

**创建日期**: 2025-02-10  
**最后更新**: 2026-02-18  
**版本**: v1.1