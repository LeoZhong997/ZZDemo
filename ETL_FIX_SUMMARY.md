# ETL门店名称处理逻辑修正总结

生成时间: 2026-02-14 15:52

---

## ✅ 修正完成

### 问题发现

1. **源文件位置错误**
   - ❌ 之前配置的文件路径不正确
   - ✅ 已修正为正确的路径

2. **字段映射配置错误**
   - ❌ 之前配置试图映射不存在的"品牌门店名称"和"平台门店名称"列
   - ✅ 已修正为映射"门店名称"列，并通过映射表获取品牌门店名称

---

## 📋 修正内容

### 1. 源文件路径修正

**文件**: `etl/core/etl_main.py`

**修正前**:
```python
FILES_TO_PROCESS = [
    (PLATFORM_MEITUAN, 'meituan', 'etl/data/sources/目标源数据/外卖源数据.xlsx', 0),
    # 饿了么文件被注释掉
    (PLATFORM_JD, 'jd', 'etl/data/sources/下载源文件/门店_全部门店_20260112_20260118_PPZH2669_2026-02-10+16_16_14.csv', 0),
]
```

**修正后**:
```python
FILES_TO_PROCESS = [
    (PLATFORM_MEITUAN, 'meituan', 'etl/data/sources/下载源文件/门店_全部门店_20260112_20260118_PPZH2669_2026-02-10+16_16_14.csv', 0),
    (PLATFORM_ELEME, 'eleme', 'etl/data/sources/下载源文件/门店下载_20260112至20260118_全部门店_5296290467_20260210161649743.xlsx', 0),
    (PLATFORM_JD, 'jd', 'etl/data/sources/下载源文件/门店_20260112_20260118_jd_szsxxqc_2026-02-10 16_17_24.xlsx', 0),
]
```

### 2. 字段映射配置修正

**文件**: `etl/core/field_mapping.py`

#### 美团平台
**修正前**:
```python
"brand_store_name": "品牌门店名称",
"platform_store_name": "平台门店名称",
```

**修正后**:
```python
"brand_store_name": None,  # 通过映射表获取
"platform_store_name": "门店名称",  # 从源文件的"门店名称"列读取
```

#### 饿了么平台
**修正前**:
```python
"brand_store_name": "门店名称",
"platform_store_name": "门店名称",  # 两者相同，无法区分
```

**修正后**:
```python
"brand_store_name": None,  # 通过映射表获取
"platform_store_name": "门店名称",  # 从源文件的"门店名称"列读取
```

#### 京东平台
**修正前**:
```python
"brand_store_name": "门店名称",
"platform_store_name": "门店名称",  # 两者相同，无法区分
```

**修正后**:
```python
"brand_store_name": None,  # 通过映射表获取
"platform_store_name": "门店名称",  # 从源文件的"门店名称"列读取
```

---

## 🔄 ETL处理流程（修正后）

### 步骤1: 读取源文件
从各平台源文件读取原始数据

### 步骤2: 字段映射转换
- `platform_store_name`: 从源文件的"门店名称"列读取
- `brand_store_name`: 不从源文件读取（标记为 None）

### 步骤3: 门店映射处理
```python
if 'platform_store_name' in df_processed.columns:
    store_mapper = get_store_mapper()
    
    # 为每条记录获取品牌门店名称
    for idx, row in df_processed.iterrows():
        platform_store = row['platform_store_name']
        brand_store = store_mapper.get_brand_store_name(platform_name, platform_store)
        
        if brand_store:
            brand_store_names.append(brand_store)
        else:
            # 未找到映射，跳过该记录
            skipped_count += 1
            brand_store_names.append(None)
    
    df_processed['brand_store_name'] = brand_store_names
    
    # 过滤掉未映射的门店记录
    df_processed = df_processed[df_processed['brand_store_name'].notna()]
```

### 步骤4: 数据库写入
将包含正确品牌门店名称的数据写入 `daily_orders` 表

---

## 📊 源文件结构确认

### 三个平台的源文件都只包含"门店名称"列

| 平台 | 文件 | 行数 | 列数 | 门店名称示例 |
|------|------|------|------|------------|
| 美团 | 门店_全部门店_20260112_20260118_PPZH2669_2026-02-10+16_16_14.csv | 91 | 83 | 雪乡情东北菜（塘朗店） |
| 饿了么 | 门店下载_20260112至20260118_全部门店_5296290467_20260210161649743.xlsx | 91 | 124 | 雪乡情东北菜(梅林店) |
| 京东 | 门店_20260112_20260118_jd_szsxxqc_2026-02-10 16_17_24.xlsx | 112 | 28 | 雪乡情东北菜（塘朗店） |

### 关键发现
- ✅ 所有平台都只有"门店名称"列
- ❌ 没有"品牌门店名称"列
- ❌ 没有"平台门店名称"列
- ✅ 必须使用映射表来获取品牌门店名称

---

## 💡 ETL逻辑说明

### 为什么需要映射表？

因为源文件只提供平台门店名称（如"雪乡情东北菜（塘朗店）"），而数据库需要统一的品牌门店名称（如"塘朗店"），所以需要通过映射表建立对应关系。

### 映射表的作用

1. **建立平台门店名称到品牌门店名称的映射**
   - 例如：`("美团", "雪乡情东北菜（塘朗店）") → "塘朗店"`

2. **验证数据完整性**
   - 如果某个门店名称没有映射，该记录会被跳过
   - 避免导入未知的门店数据

3. **统一品牌门店名称**
   - 不同平台对同一品牌门店可能有不同的命名
   - 通过映射表统一为标准的品牌门店名称

### 映射表结构

```sql
-- 品牌门店表
brand_stores:
  - id
  - brand_store_name (品牌门店名称)

-- 映射表
store_mapping:
  - platform (平台)
  - platform_store_name (平台门店名称)
  - brand_store_id (品牌门店ID)
  - is_active (是否启用)
```

---

## 🎯 下一步操作

### 1. 测试ETL流程
```bash
cd /Users/lucifer/Desktop/20260210demo
python3 -m etl.core.etl_main
```

### 2. 验证映射关系
确保 `store_mapping` 表中包含所有必要的映射关系

### 3. 检查未映射门店
运行ETL后，查看日志中是否有未映射的门店提示，及时补充映射关系

### 4. 使用门店管理界面
通过 `pages/store_management.py` 管理和维护门店映射关系

---

## 📝 注意事项

### CSV编码问题
美团CSV文件使用 `gbk` 编码，已在 `etl_main.py` 中正确配置：
```python
if filepath.endswith('.csv'):
    df = pd.read_csv(filepath, header=header, encoding='gbk')
```

### 映射表依赖
ETL流程必须依赖映射表，如果映射表为空或缺少映射，会导致数据跳过。

### 数据完整性
运行ETL前，请确保：
1. 映射表中有所有必要的映射关系
2. 映射关系的 `is_active` 字段为 1（启用）
3. 品牌门店表中有对应的品牌门店记录

---

## ✅ 修正完成清单

- [x] 确认三个平台的源文件实际列名
- [x] 修正字段映射配置（field_mapping.py）
- [x] 修正源文件路径配置（etl_main.py）
- [x] 更新文档说明（ETL_STORE_NAME_LOGIC.md）
- [ ] 测试ETL流程
- [ ] 验证数据导入结果

---

**版本**: 2.0  
**状态**: ✅ 修正完成，等待测试