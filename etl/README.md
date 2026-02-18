# ETL系统 - 外卖数据提取、转换、加载

## 📁 目录结构

```
etl/
├── __init__.py                 # ETL包初始化文件
├── README.md                   # 本文档
├── config/                     # 配置模块
│   ├── __init__.py
│   └── config.py              # 数据库、路径、常量配置
├── core/                       # 核心ETL模块
│   ├── __init__.py
│   ├── data_processor.py      # 数据处理器
│   ├── etl_main.py            # ETL主程序
│   ├── field_mapping.py       # 字段映射配置
│   ├── import_data.py         # 数据导入模块
│   ├── import_platform_source.py  # 平台源数据导入
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
│   │   ├── 目标源文件/
│   │   └── 下载源文件/
│   └── backup/                # 备份数据
│       └── backup/
├── logs/                       # 日志文件目录
└── reports/                    # 报告目录
```

## 🚀 快速开始

### 1. 运行ETL主程序

从项目根目录运行：

```bash
python run_etl.py
```

或者直接使用包导入：

```python
from etl import etl_main
etl_main()
```

### 2. 验证数据

```python
from etl import validate_etl
validate_etl()
```

### 3. 检查缺失列

```python
from etl import check_missing_columns
check_missing_columns()
```

## 📋 配置说明

所有配置都在 `etl/config/config.py` 中：

- **数据库配置**: 主机、端口、用户名、密码、数据库名
- **表名配置**: daily_orders
- **平台配置**: 美团、饿了么、京东
- **路径配置**: 日志、数据、备份、报告目录
- **批处理配置**: 批次大小、去重检查天数

## 🔄 ETL流程

1. **提取(Extract)**: 从Excel/CSV文件读取源数据
2. **转换(Transform)**:
   - 字段映射
   - 数据清洗
   - 格式转换
   - 百分比处理
3. **加载(Load)**: 将处理后的数据写入MySQL数据库

## 📊 支持的平台

- **美团**: 从Excel文件导入
- **饿了么**: 映射表（非数据源）
- **京东**: 从CSV文件导入

## 🛠️ 辅助脚本

### 备份数据
```bash
python etl/scripts/backup_etl_data.py
```

### 清理重复数据
```bash
python etl/scripts/cleanup_duplicates.py
```

### 删除特定时间段数据
```bash
python etl/scripts/delete_period_data.py
```

### 修复转化率数据
```bash
python etl/scripts/fix_conversion_rates.py
```

## 📝 字段映射

字段映射定义在 `etl/core/field_mapping.py` 中：

- **基础信息**: date, platform, brand_store_name, platform_store_name
- **财务指标**: revenue, order_amount, discount_amount, 等
- **订单数量**: total_orders, valid_orders, completed_orders
- **转化率**: exposure_conversion_rate, browse_conversion_rate, 等
- **流量数据**: exposure_count, browse_count, add_to_cart_count, 等
- **评分数据**: store_rating, food_rating, delivery_rating, 等
- **回复率**: merchant_reply_rate, system_reply_rate, 等

## 📈 数据验证

验证脚本会检查：

1. 数据完整性（必需字段是否存在）
2. 数据格式（日期、数值、百分比）
3. 数据范围（转化率0-100%，评分0-5分）
4. 数据一致性（平台名称、日期格式）

## 🔧 故障排查

### 导入错误
- 检查Python路径是否正确
- 确保所有__init__.py文件存在
- 验证依赖包是否已安装

### 数据库连接失败
- 检查MySQL服务是否运行
- 验证数据库配置（host、port、user、password）
- 确认数据库已创建

### 数据导入失败
- 检查源文件格式
- 验证字段映射配置
- 查看日志文件获取详细错误信息

## 📄 许可证

内部使用