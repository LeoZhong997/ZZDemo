# ETL 脚本工具集

> 外卖数据管理脚本工具集，提供数据库管理、检查、修复、导出等功能

---

## 📁 脚本列表

| 脚本 | 功能 | 命令示例 |
|------|------|----------|
| `db_admin.py` | 数据库管理（初始化/清空/删除/备份/恢复） | `python scripts/etl/db_admin.py init` |
| `db_check.py` | 数据库检查（状态/映射/列/指标/验证） | `python scripts/etl/db_check.py status` |
| `data_fix.py` | 数据修复（转化率/重复数据/store_id） | `python scripts/etl/data_fix.py conversion` |
| `store_mapping.py` | 门店映射管理（初始化/列表） | `python scripts/etl/store_mapping.py init` |
| `export.py` | 数据导出到 Excel | `python scripts/etl/export.py --start 2026-01-11` |

---

## 🗄️ db_admin.py - 数据库管理

```bash
# 初始化数据库和表结构
python scripts/etl/db_admin.py init

# 清空 daily_orders 表（需确认）
python scripts/etl/db_admin.py clear

# 删除指定日期范围的数据
python scripts/etl/db_admin.py delete --start 2026-01-12 --end 2026-01-18

# 备份数据到 CSV 和数据库临时表
python scripts/etl/db_admin.py backup --start 2026-01-11 --end 2026-01-18

# 从备份文件恢复数据
python scripts/etl/db_admin.py restore --file backup.csv
```

---

## 🔍 db_check.py - 数据库检查

```bash
# 检查数据库当前状态（记录数、日期范围、平台分布、门店排名）
python scripts/etl/db_check.py status

# 检查未映射的门店记录
python scripts/etl/db_check.py unmapped

# 检查数据库表列是否完整
python scripts/etl/db_check.py columns

# 检查指标映射和数据覆盖率
python scripts/etl/db_check.py metrics

# 验证导入结果（重复检查、数据完整性）
python scripts/etl/db_check.py verify
```

---

## 🔧 data_fix.py - 数据修复

```bash
# 修复转化率格式（小数转百分比）
python scripts/etl/data_fix.py conversion

# 清理重复数据
python scripts/etl/data_fix.py duplicates

# 修复缺失的 store_id
python scripts/etl/data_fix.py store_id
```

---

## 🏪 store_mapping.py - 门店映射管理

```bash
# 初始化门店映射表（创建表并插入默认数据）
python scripts/etl/store_mapping.py init

# 列出所有门店映射
python scripts/etl/store_mapping.py list
```

---

## 📤 export.py - 数据导出

```bash
# 导出所有数据
python scripts/etl/export.py

# 导出指定日期范围的数据
python scripts/etl/export.py --start 2026-01-11 --end 2026-01-18

# 指定输出文件
python scripts/etl/export.py --output report.xlsx
```

---

## ⚠️ 注意事项

1. **危险操作**: `clear` 和 `delete` 命令会永久删除数据，请谨慎操作
2. **备份建议**: 执行删除操作前，建议先使用 `backup` 命令备份数据
3. **数据库连接**: 所有脚本都需要正确的数据库配置（`etl/config/config.py`）

---

## 📊 输出示例

### db_check.py status

```
======================================================================
📊 数据库状态检查
======================================================================

📌 总记录数: 1500
📅 日期范围: 2026-01-11 至 2026-01-18

📊 各平台数据统计:
   美团: 600 条
   饿了么: 500 条
   京东: 400 条

🏪 门店收入 Top 10:
   门店名称                  记录数     总收入
   --------------------------------------------------
   信和店                    50         ¥25,000.00
   ...
```

---

**最后更新**: 2026-02-25