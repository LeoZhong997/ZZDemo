# ETL系统 - 外卖数据提取、转换、加载

## 📚 相关文档

- [快速启动指南](../docs/quickstart.md) - 快速上手项目
- [项目规格说明书](../docs/project-specification.md) - 完整技术文档
- [门店映射指南](../docs/store-mapping-guide.md) - 门店映射使用说明

---

## 📁 目录结构

```
etl/
├── __init__.py                 # ETL包初始化文件
├── README.md                   # 本文档
├── config/                     # 配置模块
│   ├── __init__.py
│   ├── config.py              # 数据库、路径、常量配置
│   ├── daily_orders_schema.sql # 主表结构
│   ├── init_database.sql      # 数据库初始化
│   └── store_schema.sql       # 门店映射表结构
├── core/                       # 核心ETL模块
│   ├── __init__.py
│   ├── data_processor.py      # 数据处理器
│   ├── etl_main.py            # ETL主程序
│   ├── field_mapping.py       # 字段映射配置
│   ├── import_data.py         # 数据导入模块
│   ├── import_platform_source.py  # 平台源数据导入
│   ├── store_mapper.py        # 门店映射处理
│   ├── validate_and_import.py # 验证并导入
│   └── validate_etl_data.py   # ETL数据验证
├── scripts/                    # 辅助脚本
│   ├── backup_etl_data.py     # 备份数据
│   ├── check_missing_columns.py  # 检查缺失列
│   ├── cleanup_duplicates.py  # 清理重复数据
│   ├── delete_period_data.py  # 删除时间段数据
│   ├── fix_conversion_rates.py  # 修复转化率
│   └── restore_fixed_data.py  # 恢复修复的数据
├── data/                       # 数据目录
│   ├── sources/               # 源数据文件
│   │   ├── 目标源数据/
│   │   ├── 下载源文件/
│   │   └── 目标源文件/
│   └── backup/                # 备份数据
├── logs/                       # 日志文件目录
└── reports/                    # 报告目录
```

---

## 🚀 快速开始

### 运行ETL主程序

从项目根目录运行：

```bash
python run_etl.py
```

或直接运行模块：

```bash
python -m etl.core.etl_main
```

---

## 📋 配置说明

所有配置都在 `etl/config/config.py` 中：

| 配置项 | 说明 |
|--------|------|
| 数据库配置 | 主机、端口、用户名、密码、数据库名 |
| 表名配置 | daily_orders |
| 平台配置 | 美团、饿了么、京东 |
| 路径配置 | 日志、数据、备份、报告目录 |
| 批处理配置 | 批次大小(1000)、去重检查天数(90) |

---

## 🔄 ETL流程

```
1. 提取(Extract)
   ↓ 从Excel/CSV文件读取源数据
   
2. 转换(Transform)
   ↓ 字段映射 → 数据清洗 → 格式转换 → 百分比处理 → 门店映射
   
3. 加载(Load)
   ↓ 写入MySQL数据库（INSERT IGNORE去重）
```

---

## 📊 支持的平台

| 平台 | 文件格式 | 编码 | Sheet名 |
|------|----------|------|---------|
| 美团 | CSV | GBK | - |
| 饿了么 | Excel | UTF-8 | data |
| 京东 | Excel | UTF-8 | 数据 |

---

## 🛠️ 辅助脚本

```bash
# 备份数据
python etl/scripts/backup_etl_data.py

# 清理重复数据
python etl/scripts/cleanup_duplicates.py

# 删除特定时间段数据
python etl/scripts/delete_period_data.py

# 修复转化率数据
python etl/scripts/fix_conversion_rates.py
```

---

## 📝 字段映射

字段映射定义在 `etl/core/field_mapping.py` 中，支持：

- **基础信息**: date, platform, brand_store_name, platform_store_name
- **财务指标**: actual_income, turnover, expense, net_margin_rate 等
- **订单数量**: valid_orders, invalid_orders, merchant_cancelled_orders
- **转化率**: store_entry_rate, order_conversion_rate 等
- **流量数据**: exposure_count, entry_count, order_people 等
- **评分数据**: store_score, new_merchant_score 等

---

## 🔧 故障排查

### 导入错误
- 检查Python路径是否正确
- 确保所有 `__init__.py` 文件存在
- 验证依赖包是否已安装

### 数据库连接失败
- 检查MySQL服务是否运行
- 验证数据库配置（host、port、user、password）
- 确认数据库已创建

### 数据导入失败
- 检查源文件格式和编码
- 验证字段映射配置
- 查看日志文件获取详细错误信息

---

**最后更新**: 2026-02-18