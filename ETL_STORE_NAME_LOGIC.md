# ETL门店名称处理逻辑确认

生成时间: 2026-02-14 15:46

---

## ✅ 已确认的信息

### 三个平台的源文件实际列名

**重要发现**: 三个平台的源文件都只有"门店名称"列，没有独立的"品牌门店名称"和"平台门店名称"列！

#### 1. 美团平台

**源文件**: `etl/data/sources/下载源文件/门店_全部门店_20260112_20260118_PPZH2669_2026-02-10+16_16_14.csv`

**实际列名**:
- ✅ **门店名称** (第2列) - 示例: `['雪乡情东北菜（塘朗店）', '雪乡情大地锅(信和广场店)', '雪乡情铁锅炖（后海店）']`
- ❌ **品牌门店名称** - 不存在
- ❌ **平台门店名称** - 不存在

**数据量**: 91 行, 83 列

#### 2. 京东平台

**源文件**: `etl/data/sources/下载源文件/门店_20260112_20260118_jd_szsxxqc_2026-02-10 16_17_24.xlsx`

**实际列名**:
- ✅ **门店名称** (第1列) - 示例: `['念东北铁锅炖（长兴店）', '雪乡情东北菜（塘朗店）', '雪乡情东北菜（蛇口店）']`
- ❌ **品牌门店名称** - 不存在
- ❌ **平台门店名称** - 不存在

**数据量**: 112 行, 28 列

#### 3. 饿了么平台

**源文件**: `etl/data/sources/下载源文件/门店下载_20260112至20260118_全部门店_5296290467_20260210161649743.xlsx`

**实际列名**:
- ✅ **门店名称** (第2列) - 示例: `['雪乡情东北菜(梅林店)', '雪乡情东北菜(壹方城店)', '雪乡情东北菜(大冲店)']`
- ❌ **品牌门店名称** - 不存在
- ❌ **平台门店名称** - 不存在

**数据量**: 91 行, 124 列

### 关键结论

**所有三个平台的源文件都只包含"门店名称"列**，这意味着：
1. ✅ **必须使用映射表** - 源文件只提供平台门店名称，需要通过映射表找到品牌门店名称
2. ❌ **当前ETL映射配置错误** - 试图映射不存在的"品牌门店名称"和"平台门店名称"列
3. ✅ **映射表系统是必要的** - 用于建立平台门店名称到品牌门店名称的对应关系

---

## 🔄 当前ETL处理流程

### 步骤1: 读取源文件
从各平台源文件读取原始数据

### 步骤2: 字段映射转换
使用 `field_mapping.py` 中的映射规则，将中文列名转换为英文列名：

```python
# 美团示例
原始列名 "品牌门店名称" → 数据库列名 "brand_store_name"
原始列名 "平台门店名称" → 数据库列名 "platform_store_name"
```

### 步骤3: 门店映射处理 (etl_main.py)
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

### 步骤4: 依赖的映射表
当前ETL流程依赖以下数据库表：
- `brand_stores` - 品牌门店表
- `store_mapping` - 平台门店名称到品牌门店名称的映射表

映射查询逻辑：
```sql
SELECT 
    sm.platform,
    sm.platform_store_name,
    bs.brand_store_name,
    bs.id as brand_store_id
FROM store_mapping sm
INNER JOIN brand_stores bs ON sm.brand_store_id = bs.id
WHERE sm.is_active = 1
```

---

## ❌ 发现的问题

### 问题1: 映射逻辑冗余

**现状**:
- 美团源文件**已经包含**正确的 `brand_store_name`（品牌门店名称）
- 但ETL仍然使用 `platform_store_name` 去映射表查找 `brand_store_name`
- 这导致：
  1. 如果映射表中有记录，会用映射表的值**覆盖**源文件的品牌门店名称
  2. 如果映射表中没有记录，会**跳过**这条数据

**示例**:
```
源文件:
  brand_store_name: "车公庙店"
  platform_store_name: "雪乡情春饼东北菜(车公庙店)"

映射表:
  (美团, "雪乡情春饼东北菜(车公庙店)") → "信和店"

ETL结果:
  brand_store_name: "信和店"  ← 被映射表覆盖
  platform_store_name: "雪乡情春饼东北菜(车公庙店)"
```

**影响**:
- 如果映射表的数据不正确，会导致错误的品牌门店名称
- 如果映射表缺失记录，会丢失数据

### 问题2: 饿了么和京东的配置不一致

**饿了么配置**:
```python
"brand_store_name": "门店名称"      # 与platform_store_name相同
"platform_store_name": "门店名称"  # 与brand_store_name相同
```

**京东配置**:
```python
"brand_store_name": "门店名称"      # 与platform_store_name相同
"platform_store_name": "门店名称"  # 与brand_store_name相同
```

**问题**:
- 如果饿了么/京东源文件只有"门店名称"列，两个字段会得到相同的值
- 无法区分品牌门店名称和平台门店名称
- 需要确认饿了么/京东源文件的实际结构

---

## 💡 建议的修正方案

### 方案A: 简化ETL逻辑（推荐）

**如果源文件已经包含正确的品牌门店名称**，直接使用源文件的值，不需要映射表：

#### 修改1: 移除门店映射处理

在 `etl_main.py` 的 `process_single_file()` 函数中，注释掉门店映射代码：

```python
# 门店映射处理
# if 'platform_store_name' in df_processed.columns:
#     store_mapper = get_store_mapper()
#     # ... 映射逻辑 ...
```

#### 修改2: 确保字段映射正确

```python
# 美团
"brand_store_name": "品牌门店名称"      # ✅ 直接使用源文件值
"platform_store_name": "平台门店名称"    # ✅ 直接使用源文件值

# 饿了么（需要确认源文件是否有"品牌门店名称"列）
"brand_store_name": "品牌门店名称"      # 或 "门店名称"
"platform_store_name": "门店名称"

# 京东（需要确认源文件是否有"品牌门店名称"列）
"brand_store_name": "品牌门店名称"      # 或 "门店名称"
"platform_store_name": "门店名称"
```

**优点**:
- ✅ 不依赖额外的映射表
- ✅ 简化ETL流程
- ✅ 与简化版门店映射页面一致
- ✅ 直接使用源文件的权威数据
- ✅ 减少维护成本

### 方案B: 优化映射逻辑（如果必须使用映射表）

**如果确实需要映射表**，应该：

1. **只映射品牌门店名称缺失的数据**
   ```python
   if 'brand_store_name' in df_processed.columns:
       # 只处理brand_store_name为空的记录
       mask = df_processed['brand_store_name'].isna()
       for idx in df_processed[mask].index:
           # 使用映射表查找
   ```

2. **保留源文件的品牌门店名称**
   - 如果源文件有品牌门店名称，优先使用源文件的值
   - 只有当源文件为空时，才使用映射表

3. **改进映射表的用途**
   - 映射表用于验证和补充，而不是覆盖
   - 可以检查源文件的品牌门店名称是否正确

---

## 📋 下一步行动

### 1. 确认饿了么/京东源文件结构

需要检查：
- 饿了么源文件是否有"品牌门店名称"列？
- 京东源文件是否有"品牌门店名称"列？
- 是否只有"门店名称"一列？

### 2. 决定采用哪种方案

**方案A**: 简化ETL逻辑（推荐）
- 条件: 源文件已经包含正确的品牌门店名称
- 优点: 简单、直接、易于维护

**方案B**: 优化映射逻辑
- 条件: 需要映射表进行验证或补充
- 优点: 更灵活，但复杂度高

### 3. 实施修改

根据确认的信息，修改：
- `etl/core/field_mapping.py` - 字段映射配置
- `etl/core/etl_main.py` - 数据处理逻辑

### 4. 测试验证

修改后需要：
- 运行ETL测试数据
- 验证门店名称是否正确
- 确认数据完整性

---

## 📊 当前映射关系统计

根据简化版门店映射页面的数据（2026-01-05 到 2026-01-11）：

**总计**: 48 条映射关系

**按平台分布**:
- 美团: 21 条
- 饿了么: 13 条  
- 京东: 14 条

**品牌门店数量**: 14 家

**示例**:
```
美团:
  信和店 -> 雪乡情大地锅(信和广场店), 雪乡情铁锅炖(信和广场店)
  车公庙店 -> 雪乡情春饼东北菜(车公庙店), 雪乡情东北菜(车公庙店)

饿了么:
  信和店 -> 雪乡情铁锅炖(信和广场店)
  车公庙店 -> 雪乡情东北菜(车公庙店)

京东:
  信和店 -> 雪乡情铁锅炖（信和广场店）
  车公庙店 -> 雪乡情东北菜（车公庙店）
```

---

## 📝 总结

### 已确认
- ✅ 美团源文件包含"品牌门店名称"和"平台门店名称"两列
- ✅ 美团的ETL映射配置正确
- ✅ 当前ETL流程依赖 `store_mapping` 和 `brand_stores` 表

### 待确认
- ❓ 饿了么源文件的列名结构
- ❓ 京东源文件的列名结构
- ❓ 是否需要使用映射表

### 待决策
- 🤔 采用方案A（简化）还是方案B（优化）
- 🤔 映射表的作用是什么？

---

**版本**: 1.0  
**状态**: ⏳ 等待确认饿了么/京东源文件结构