# 🚀 快速启动指南

## 一键启动数据看板

```bash
cd ~/Desktop/20260210demo
./run_dashboard.sh
```

看板将在浏览器自动打开：http://localhost:8501

---

## 运行ETL导入数据

```bash
cd ~/Desktop/20260210demo
./run.sh
```

---

## 配置数据库密码

### 1. ETL程序配置
编辑 `etl_main.py`:
```python
DB_CONFIG = {
    'password': 'your_password',  # 修改这里
}
```

### 2. 看板配置
编辑 `app.py`:
```python
DB_CONFIG = {
    'password': 'your_password',  # 修改这里
}
```

---

## 目录结构

```
20260210demo/
├── app.py                    # Streamlit看板应用
├── etl_main.py               # ETL主程序
├── data_processor.py          # 数据处理逻辑
├── field_mapping.py          # 字段映射
├── daily_orders_schema.sql    # 数据库建表SQL
├── requirements.txt           # Python依赖
├── run.sh                   # ETL启动脚本
├── run_dashboard.sh         # 看板启动脚本
└── README.md                # 完整文档
```

---

## 常用命令

### 查看已安装的Python包
```bash
pip list | grep streamlit
```

### 重启Streamlit
在终端按 `Ctrl+C` 停止，然后重新运行：
```bash
./run_dashboard.sh
```

### 清除Streamlit缓存
```bash
rm -rf ~/.streamlit/cache
```

---

## 数据库表结构

表名: `daily_orders`

主要字段:
- 日期、平台、门店名称
- 实收、支出、营业额、到手率
- 有效订单、无效订单
- 曝光人数、入店人数、下单人数
- 店铺分、综合体验分
- ... 共63个字段

详细结构见 `daily_orders_schema.sql`

---

## 看板功能（第一阶段）

✅ 日期筛选
✅ 平台多选
✅ 数据统计卡片
✅ 原始数据预览
✅ 数据库查询缓存

---

## 故障排查

### 看板启动失败

1. 检查Python版本
```bash
python3 --version  # 需要 3.8+
```

2. 安装依赖
```bash
pip install streamlit pandas sqlalchemy pymysql
```

3. 检查数据库连接
```bash
mysql -u root -p waimai_db -e "SELECT COUNT(*) FROM daily_orders;"
```

### 数据加载失败

1. 检查数据库是否有数据
```sql
SELECT COUNT(*) FROM daily_orders;
```

2. 检查日期范围是否正确
```sql
SELECT MIN(date), MAX(date) FROM daily_orders;
```

### 端口被占用

```bash
# 查找占用8501端口的进程
lsof -i :8501

# 杀死进程
kill -9 <PID>
```

---

## 下一步

- [ ] 第二阶段：添加趋势图表
- [ ] 第二阶段：平台对比分析
- [ ] 第二阶段：门店排名
- [ ] 第三阶段：数据导出功能
- [ ] 第三阶段：移动端优化

---

**最后更新**: 2025-02-10
