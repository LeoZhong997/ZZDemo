# 🚀 快速启动指南

本指南帮助你快速启动外卖数据看板系统。

---

## 目录

- [环境准备](#环境准备)
- [数据库初始化](#数据库初始化)
- [安装依赖](#安装依赖)
- [配置数据库连接](#配置数据库连接)
- [运行ETL导入数据](#运行etl导入数据)
- [启动数据看板](#启动数据看板)
- [常见问题](#常见问题)

---

## 环境准备

### 系统要求

- Python 3.8+
- MySQL 5.7+
- 至少 2GB 内存
- 至少 1GB 磁盘空间

### 验证 Python 版本

```bash
python3 --version  # 需要 3.8+
```

---

## 数据库初始化

### 步骤1：创建数据库

```bash
mysql -u root -p
```

在 MySQL 命令行中执行：

```sql
CREATE DATABASE waimai_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```

### 步骤2：创建表结构

```bash
mysql -u root -p waimai_db < etl/config/daily_orders_schema.sql
```

### 步骤3：验证表结构

```bash
mysql -u root -p waimai_db -e "DESCRIBE daily_orders;"
```

---

## 安装依赖

### 方式一：使用 requirements.txt（推荐）

```bash
pip install -r requirements.txt
```

### 方式二：手动安装

```bash
pip install streamlit pandas sqlalchemy pymysql openpyxl numpy
```

### 验证安装

```bash
python -c "import pandas, sqlalchemy, streamlit; print('所有依赖安装成功！')"
```

---

## 配置数据库连接

### 方式一：修改配置文件（开发环境）

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

### 方式二：使用环境变量（推荐）

```bash
export DB_HOST=localhost
export DB_PORT=3306
export DB_USER=root
export DB_PASSWORD=your_password
export DB_NAME=waimai_db
```

---

## 运行ETL导入数据

### 准备源数据文件

将三个平台的导出文件放入 `etl/data/sources/下载源文件/` 目录：

```
etl/data/sources/下载源文件/
├── 美团数据.csv
├── 饿了么数据.xlsx
└── 京东数据.xlsx
```

### 运行ETL程序

```bash
# 方式一：使用入口脚本
python run_etl.py

# 方式二：直接运行模块
python -m etl.core.etl_main
```

---

## 启动数据看板

### 方式一：使用启动脚本

```bash
./run_dashboard.sh
```

### 方式二：手动启动

```bash
streamlit run app.py
```

看板将在浏览器中自动打开：**http://localhost:8501**

---

## 常见问题

### 1. 看板启动失败

**检查Python版本**
```bash
python3 --version  # 需要 3.8+
```

**安装依赖**
```bash
pip install streamlit pandas sqlalchemy pymysql
```

**检查数据库连接**
```bash
mysql -u root -p waimai_db -e "SELECT COUNT(*) FROM daily_orders;"
```

### 2. 数据加载失败

**检查数据库是否有数据**
```sql
SELECT COUNT(*) FROM daily_orders;
```

**检查日期范围**
```sql
SELECT MIN(date), MAX(date) FROM daily_orders;
```

### 3. 端口被占用

```bash
# 查找占用8501端口的进程
lsof -i :8501

# 杀死进程
kill -9 <PID>

# 或使用其他端口
streamlit run app.py --server.port 8502
```

### 4. 模块导入错误

```bash
# 确保在项目根目录
cd /path/to/ZZDemo

# 检查Python路径
python -c "import sys; print('\n'.join(sys.path))"

# 重新安装依赖
pip install --upgrade -r requirements.txt
```

### 5. 清除Streamlit缓存

```bash
rm -rf ~/.streamlit/cache
```

---

## 常用命令速查

| 操作 | 命令 |
|------|------|
| 启动看板 | `streamlit run app.py` |
| 运行ETL | `python run_etl.py` |
| 查看已安装包 | `pip list \| grep streamlit` |
| 清除缓存 | `rm -rf ~/.streamlit/cache` |
| 检查数据库 | `mysql -u root -p waimai_db -e "SELECT COUNT(*) FROM daily_orders;"` |

---

## 下一步

- 📖 阅读 [项目规格说明书](project-specification.md) 了解完整技术细节
- 📊 查看 [门店映射指南](store-mapping-guide.md) 了解门店管理
- 🔧 配置定时任务自动运行ETL

---

**最后更新**: 2026-02-18