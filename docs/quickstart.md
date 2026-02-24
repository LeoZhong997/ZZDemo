# 🚀 快速启动指南

本指南帮助你快速启动外卖数据看板系统。

---

## 目录

- [环境准备](#环境准备)
- [安装 MySQL](#安装-mysql)
- [数据库初始化](#数据库初始化)
- [安装依赖](#安装依赖)
- [配置数据库连接](#配置数据库连接)
- [运行ETL导入数据](#运行etl导入数据)
- [启动数据看板](#启动数据看板)
- [常见问题](#常见问题)

---

## 环境准备

### 系统要求

- **Python**: 3.8+ (推荐使用 Conda 管理)
- **MySQL**: 5.7+ 或 8.x
- 至少 2GB 内存
- 至少 1GB 磁盘空间

### 验证 Python 版本

```bash
python --version  # 需要 3.8+
```

### 推荐使用 Conda 环境

```bash
# 创建新环境
conda create -n env_dev python=3.10

# 激活环境
conda activate env_dev
```

---

## 安装 MySQL

### Windows 系统

1. **下载 MySQL**
   - 访问 https://dev.mysql.com/downloads/mysql/
   - 选择 Windows 版本，下载 MSI 安装包

2. **安装配置**
   - 运行安装程序，选择 "Developer Default" 或 "Server only"
   - 设置 root 密码（建议使用 `1024Asdf` 与配置一致）
   - 端口保持默认 `3306`

3. **验证安装**
   ```bash
   # 在新的命令行窗口中
   mysql -u root -p
   # 输入密码后进入 MySQL 命令行
   ```

### 检查端口占用

如果端口 3306 被占用：

```bash
# Windows - 查看端口占用
netstat -ano | findstr :3306

# 停止现有 MySQL 服务
net stop mysql
```

---

## 数据库初始化

### 方式一：使用初始化脚本（推荐）

```bash
# 1. 初始化数据库和主表
python etl/scripts/init_db.py

# 2. 初始化门店映射表
python etl/scripts/init_store_mapping.py
```

### 方式二：手动执行 SQL

```bash
# 1. 创建数据库
mysql -u root -p -e "CREATE DATABASE waimai_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 2. 导入主表结构
mysql -u root -p waimai_db < etl/config/daily_orders_schema.sql

# 3. 导入门店映射表
mysql -u root -p waimai_db < etl/config/store_schema.sql
```

### 验证表结构

```bash
mysql -u root -p waimai_db -e "SHOW TABLES;"
```

预期输出：
```
+---------------------+
| Tables_in_waimai_db |
+---------------------+
| brand_stores        |
| daily_orders        |
| store_mapping       |
+---------------------+
```

---

## 安装依赖

### 激活 Conda 环境

```bash
conda activate env_dev
```

### 安装依赖

```bash
pip install -r requirements.txt
```

### 依赖列表

| 包名 | 用途 |
|------|------|
| streamlit | Web 看板 |
| pandas | 数据处理 |
| sqlalchemy | 数据库 ORM |
| pymysql | MySQL 驱动 |
| openpyxl | Excel 处理 |
| numpy | 数值计算 |
| plotly | 图表绑定 |
| cryptography | 加密支持 |

### 验证安装

```bash
python -c "import pandas, sqlalchemy, streamlit, pymysql; print('✅ 所有依赖安装成功！')"
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

**Windows CMD:**
```bash
set DB_HOST=localhost
set DB_PORT=3306
set DB_USER=root
set DB_PASSWORD=your_password
set DB_NAME=waimai_db
```

**Windows PowerShell:**
```powershell
$env:DB_HOST="localhost"
$env:DB_PASSWORD="your_password"
```

**Linux/Mac:**
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
├── 门店_全部门店_*.csv        # 美团数据
├── 门店下载_*.xlsx            # 饿了么数据
└── 门店_*_jd_*.xlsx           # 京东数据
```

### 运行ETL程序

```bash
# 确保已激活环境
conda activate env_dev

# 运行 ETL
python run_etl.py
```

### 预期输出

```
============================================================
🍔 外卖数据看板 ETL 主程序
============================================================

📡 步骤 1/4: 创建数据库连接...
✅ 数据库连接成功

📂 步骤 2/4: 读取和处理Excel文件...
✅ 美团 数据清洗完成，共 91 行
✅ 饿了么 数据清洗完成，共 91 行
✅ 京东 数据清洗完成，共 112 行

🔗 步骤 3/4: 合并所有平台数据...
✅ 数据合并完成，共 294 行

💾 步骤 4/4: 写入数据库...
✅ 导入完成:
   - 成功插入: 280 条
   - 跳过重复: 14 条

🎉 ETL 流程完成！
```

---

## 启动数据看板

### 启动命令

```bash
# 确保已激活环境
conda activate env_dev

# 启动看板
streamlit run app.py

# 或使用 Python 模块方式
python -m streamlit run app.py
```

### 访问地址

看板启动后，在浏览器中访问：

- **本地**: http://localhost:8501
- **局域网**: http://<你的IP>:8501

### 后台运行（可选）

```bash
# 不自动打开浏览器
streamlit run app.py --server.headless true
```

---

## 常见问题

### 1. mysql 命令未找到

**问题**: `'mysql' is not recognized as a name of a cmdlet...`

**解决**: MySQL 未添加到 PATH，使用 Python 脚本初始化：
```bash
python etl/scripts/init_db.py
python etl/scripts/init_store_mapping.py
```

### 2. store_mapping 表不存在

**问题**: `Table 'waimai_db.store_mapping' doesn't exist`

**解决**: 初始化门店映射表：
```bash
python etl/scripts/init_store_mapping.py
```

### 3. 看板启动失败

**检查 Python 版本**
```bash
python --version  # 需要 3.8+
```

**检查依赖安装**
```bash
pip list | findstr streamlit
```

**检查数据库连接**
```bash
python -c "from etl.config import get_connection_string; print(get_connection_string())"
```

### 4. 数据加载失败

**检查数据库是否有数据**
```sql
SELECT COUNT(*) FROM daily_orders;
```

**检查日期范围**
```sql
SELECT MIN(date), MAX(date) FROM daily_orders;
```

### 5. 端口被占用

```bash
# Windows - 查找占用8501端口的进程
netstat -ano | findstr :8501

# 杀死进程
taskkill /F /PID <PID>

# 或使用其他端口
streamlit run app.py --server.port 8502
```

### 6. Conda 环境问题

```bash
# 查看所有环境
conda env list

# 重新创建环境
conda create -n env_dev python=3.10
conda activate env_dev
pip install -r requirements.txt
```

### 7. 清除 Streamlit 缓存

```bash
# Windows
rmdir /s /q %USERPROFILE%\.streamlit\cache

# Linux/Mac
rm -rf ~/.streamlit/cache
```

---

## 常用命令速查

| 操作 | 命令 |
|------|------|
| 激活环境 | `conda activate env_dev` |
| 启动看板 | `streamlit run app.py` |
| 运行 ETL | `python run_etl.py` |
| 初始化数据库 | `python etl/scripts/init_db.py` |
| 初始化门店映射 | `python etl/scripts/init_store_mapping.py` |
| 查看已安装包 | `pip list` |
| 检查数据库 | `mysql -u root -p waimai_db -e "SELECT COUNT(*) FROM daily_orders;"` |

---

## 完整启动流程

```bash
# 1. 激活 Conda 环境
conda activate env_dev

# 2. 初始化数据库（首次运行）
python etl/scripts/init_db.py
python etl/scripts/init_store_mapping.py

# 3. 运行 ETL 导入数据
python run_etl.py

# 4. 启动看板
streamlit run app.py
```

---

## 下一步

- 📖 阅读 [项目规格说明书](project-specification.md) 了解完整技术细节
- 📊 查看 [门店映射指南](store-mapping-guide.md) 了解门店管理
- 🔧 配置定时任务自动运行 ETL

---

**最后更新**: 2026-02-24