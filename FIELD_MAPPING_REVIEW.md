# ETL系统字段映射核对表

生成时间: 2026-02-14 14:50:00

---

## 📋 说明

本文档列出了数据库表 `daily_orders` 的所有72个字段，以及它们在三个平台（美团、饿了么、京东）中的映射情况。

**图例**：
- ✅ 字段已正确映射
- ❌ 字段未提供（源文件中不存在）
- ⚠️ 需要计算或人工输入

---

## 1️⃣ 基础信息字段（4个）

| 序号 | 数据库字段 | 美团 | 饿了么 | 京东 | 说明 |
|------|-----------|------|--------|------|------|
| 1 | date | ✅ 日期 | ✅ 日期 | ✅ 日期 | 日期 |
| 2 | brand_store_name | ✅ 品牌门店名称 | ✅ 门店名称 | ✅ 门店名称 | 品牌门店名称 |
| 3 | platform_store_name | ✅ 平台门店名称 | ✅ 门店名称 | ✅ 门店名称 | 平台门店名称 |
| 4 | store_id | ❌ 未提供 | ❌ 未提供 | ✅ 门店id | 京东独有字段 |
| 5 | city | ❌ 未提供 | ❌ 未提供 | ✅ 门店所在城市 | 京东独有字段 |

---

## 2️⃣ 财务指标字段（14个）

| 序号 | 数据库字段 | 美团 | 饿了么 | 京东 | 说明 |
|------|-----------|------|--------|------|------|
| 6 | actual_income | ✅ 营业收入 | ✅ 收入 | ✅ 营业收入 | 商家实收/收入 |
| 7 | expense | ✅ 补贴及支出 | ✅ 支出 | ✅ 补贴及支出 | 支出 |
| 8 | turnover | ✅ 优惠前总额 | ✅ 营业额 | ✅ 优惠前总额 | 营业额 |
| 9 | net_margin_rate | ⚠️ 需计算 | ⚠️ 需计算 | ⚠️ 需计算 | 到手率 |
| 10 | original_price | ✅ 商品原价 | ❌ 未提供 | ✅ 商品原价 | 商品原价 |
| 11 | packaging_fee | ✅ 包装费 | ✅ 打包费 | ✅ 包装费 | 包装费 |
| 12 | customer_delivery_fee | ✅ 顾客配送费（跑腿/自配送） | ✅ 商家应收配送费 | ✅ 顾客配送费（跑腿/自配送） | 顾客配送费 |
| 13 | customer_paid | ✅ 顾客实付 | ✅ 顾客实付总额 | ✅ 顾客实付 | 顾客实付 |
| 14 | avg_paid_price | ✅ 实付单均价 | ✅ 单均实付 | ✅ 实付单均价 | 实付单均价 |
| 15 | activity_subsidy | ✅ 活动补贴 | ✅ 活动补贴 | ✅ 活动补贴 | 活动补贴 |
| 16 | platform_service_fee | ✅ 平台服务费(含佣金和配送服务费) | ✅ 平台技术服务费 | ✅ 平台服务费(含佣金和配送服务费) | 平台服务费 |
| 17 | real_actual_income | ❌ 未提供 | ❌ 未提供 | ❌ 未提供 | 真实实收 |
| 18 | promotion_cost | ❌ 未提供 | ❌ 未提供 | ❌ 未提供 | 推广花费 |
| 19 | gift_sausage_cost | ❌ 未提供 | ❌ 未提供 | ❌ 未提供 | 赠红肠成本 |

---

## 3️⃣ 订单数量字段（3个）

| 序号 | 数据库字段 | 美团 | 饿了么 | 京东 | 说明 |
|------|-----------|------|--------|------|------|
| 20 | valid_orders | ✅ 有效订单 | ✅ 有效订单 | ✅ 有效订单 | 有效订单 |
| 21 | invalid_orders | ✅ 取消订单 | ✅ 无效订单 | ✅ 取消订单 | 无效订单 |
| 22 | merchant_cancelled_orders | ✅ 商责取消订单 | ✅ 商责退单数 | ✅ 商责取消订单 | 商责取消订单 |

---

## 4️⃣ 转化率字段（8个）

| 序号 | 数据库字段 | 美团 | 饿了么 | 京东 | 说明 |
|------|-----------|------|--------|------|------|
| 23 | merchant_cancellation_rate | ✅ 商责取消率 | ✅ 商责取消率 | ✅ 商责取消率 | 商责取消率 |
| 24 | store_entry_rate | ✅ 入店转化率 | ✅ 进店转化率 | ✅ 入店转化率 | 入店/进店转化率 |
| 25 | order_conversion_rate | ✅ 下单转化率 | ✅ 下单转化率 | ✅ 下单转化率 | 下单转化率 |
| 26 | new_customer_entry_rate | ✅ 新客入店转化率 | ✅ 新客进店转化率 | ✅ 新客入店转化率 | 新客入店/进店转化率 |
| 27 | new_customer_order_rate | ✅ 新客下单转化率 | ✅ 新客下单转化率 | ✅ 新客下单转化率 | 新客下单转化率 |
| 28 | old_customer_entry_rate | ✅ 老客入店转化率 | ✅ 老客进店转化率 | ✅ 老客入店转化率 | 老客入店/进店转化率 |
| 29 | old_customer_order_rate | ✅ 老客下单转化率 | ✅ 老客下单转化率 | ✅ 老客下单转化率 | 老客下单转化率 |
| 30 | repurchase_rate | ✅ 复购率 | ✅ 近30日复购率 | ✅ 复购率 | 复购率 |

---

## 5️⃣ 流量数据字段（14个）

| 序号 | 数据库字段 | 美团 | 饿了么 | 京东 | 说明 |
|------|-----------|------|--------|------|------|
| 31 | exposure_count | ✅ 曝光人数 | ✅ 曝光人数 | ✅ 曝光人数 | 曝光人数 |
| 32 | entry_count | ✅ 入店人数 | ✅ 进店人数 | ✅ 入店人数 | 入店/进店人数 |
| 33 | exposure_new_customer | ✅ 曝光新客 | ✅ 新客曝光人数 | ✅ 曝光新客 | 曝光新客 |
| 34 | entry_new_customer | ✅ 入店新客 | ✅ 新客进店人数 | ✅ 入店新客 | 入店/进店新客 |
| 35 | exposure_old_customer | ✅ 曝光老客 | ✅ 老客曝光人数 | ✅ 曝光老客 | 曝光老客 |
| 36 | entry_old_customer | ✅ 入店老客 | ✅ 老客进店人数 | ✅ 入店老客 | 入店/进店老客 |
| 37 | exposure_times | ✅ 曝光次数 | ✅ 曝光次数 | ✅ 曝光次数 | 曝光次数 |
| 38 | entry_times | ✅ 入店次数 | ✅ 进店次数 | ✅ 入店次数 | 入店/进店次数 |
| 39 | order_people | ✅ 下单人数 | ✅ 下单人数 | ✅ 下单人数 | 下单人数 |
| 40 | order_new_customer | ✅ 下单新客 | ✅ 新客下单人数 | ✅ 下单新客 | 下单新客 |
| 41 | order_old_customer | ✅ 下单老客 | ✅ 老客下单人数 | ✅ 下单老客 | 下单老客 |
| 42 | uv | ❌ 未提供 | ❌ 未提供 | ❌ 未提供 | UV |
| 43 | store_id | ❌ 未提供 | ❌ 未提供 | ✅ 门店id | 京东独有 |
| 44 | city | ❌ 未提供 | ❌ 未提供 | ✅ 门店所在城市 | 京东独有 |

---

## 6️⃣ 评分字段（18个）

| 序号 | 数据库字段 | 美团 | 饿了么 | 京东 | 说明 |
|------|-----------|------|--------|------|------|
| 45 | store_score | ✅ 店铺分 | ✅ 店铺评分 | ✅ 店铺分 | 店铺分 |
| 46 | peak_duration_score | ✅ 高峰营业时长得分 | ✅ 高峰营业时长得分 | ✅ 高峰营业时长得分 | 高峰营业时长得分 |
| 47 | quality_product_rate_score | ✅ 优质商品率得分 | ✅ 优质商品率得分 | ✅ 优质商品率得分 | 优质商品率得分 |
| 48 | activity_richness_score | ✅ 有效活动丰富度得分 | ✅ 有效活动丰富度得分 | ✅ 有效活动丰富度得分 | 有效活动丰富度得分 |
| 49 | reject_order_rate_score | ✅ 商家不接单率得分 | ✅ 商家不接单率得分 | ✅ 商家不接单率得分 | 商家不接单率得分 |
| 50 | bad_review_reply_rate_score | ✅ 差评回复率得分 | ✅ 差评回复率得分 | ✅ 差评回复率得分 | 差评回复率得分 |
| 51 | online_reply_rate_score | ✅ 在线联系回复率得分 | ✅ 在线联系回复率得分 | ✅ 在线联系回复率得分 | 在线联系回复率得分 |
| 52 | new_merchant_score | ✅ overall_experience_score | ✅ 店铺评分 | ✅ 综合体验分 | 新商家/店铺评分 |
| 53 | menu_richness_score | ✅ 菜单丰富度得分 | ✅ 菜单丰富度得分 | ✅ 菜单丰富度得分 | 菜单丰富度得分 |
| 54 | decoration_richness_score | ✅ 装修丰富度得分 | ✅ 装修丰富度得分 | ✅ 装修丰富度得分 | 装修丰富度得分 |
| 55 | service_function_score | ✅ 服务功能丰富度得分 | ✅ 昨日服务功能丰富度指标得分 | ❌ 未提供 | 服务功能丰富度得分 |
| 56 | product_quality_score | ✅ 商品质量分 | ❌ 未提供 | ❌ 未提供 | 商品质量分 |
| 57 | service_experience_score | ✅ 服务体验分 | ❌ 未提供 | ❌ 未提供 | 服务体验分 |
| 58 | product_satisfaction | ✅ 商品满意度 | ❌ 未提供 | ❌ 未提供 | 商品满意度 |
| 59 | packaging_satisfaction | ✅ 包装满意度 | ❌ 未提供 | ❌ 未提供 | 包装满意度 |
| 60 | overall_experience_score | ❌ 未提供 | ❌ 未提供 | ❌ 未提供 | 综合体验分 |
| 61 | old_merchant_score | ❌ 未提供 | ❌ 未提供 | ❌ 未提供 | 老商家评分 |

---

## 7️⃣ 指标得分字段（4个）

| 序号 | 数据库字段 | 美团 | 饿了么 | 京东 | 说明 |
|------|-----------|------|--------|------|------|
| 62 | repurchase_rate_score | ✅ 复购率指标得分 | ❌ 未提供 | ❌ 未提供 | 复购率指标得分 |
| 63 | message_reply_rate_score | ✅ 消息回复率指标得分 | ❌ 未提供 | ❌ 未提供 | 消息回复率指标得分 |
| 64 | service_negative_feedback_score | ✅ 服务负反馈率指标得分 | ❌ 未提供 | ❌ 未提供 | 服务负反馈率指标得分 |
| 65 | food_safety_negative_feedback_score | ✅ 食品安全负反馈率指标得分 | ❌ 未提供 | ❌ 未提供 | 食品安全负反馈率指标得分 |

---

## 8️⃣ 回复率字段（5个）

| 序号 | 数据库字段 | 美团 | 饿了么 | 京东 | 说明 |
|------|-----------|------|--------|------|------|
| 66 | five_min_reply_rate | ⚠️ 需人工输入 | ⚠️ 需人工输入 | ⚠️ 需人工输入 | 5分钟回复率 |
| 67 | one_min_reply_rate | ⚠️ 需人工输入 | ⚠️ 需人工输入 | ⚠️ 需人工输入 | 1分钟回复率 |
| 68 | message_reply_rate | ✅ 消息回复率 | ❌ 未提供 | ❌ 未提供 | 消息回复率 |
| 69 | food_safety_negative_feedback_rate | ✅ 食品安全负反馈率 | ❌ 未提供 | ❌ 未提供 | 食品安全负反馈率 |

---

## 9️⃣ 时间字段（1个）

| 序号 | 数据库字段 | 美团 | 饿了么 | 京东 | 说明 |
|------|-----------|------|--------|------|------|
| 70 | basic_duration | ✅ 基础营业时长 | ✅ 营业时长 | ✅ 日均营业时长 | 基础营业时长 |

---

## 🔟 完成率字段（1个）

| 序号 | 数据库字段 | 美团 | 饿了么 | 京东 | 说明 |
|------|-----------|------|--------|------|------|
| 71 | meal_completion_report_rate | ✅ 出餐完成上报率 | ✅ 近7日出餐完成上报率当前值 | ❌ 未提供 | 出餐完成上报率 |

---

## 1️⃣1️⃣ 系统字段（1个）

| 序号 | 数据库字段 | 美团 | 饿了么 | 京东 | 说明 |
|------|-----------|------|--------|------|------|
| 72 | import_time | ⚠️ 系统自动生成 | ⚠️ 系统自动生成 | ⚠️ 系统自动生成 | 导入时间 |

---

## 📊 统计汇总

### 字段覆盖情况

| 平台 | 总字段数 | 已映射 | 未提供 | 覆盖率 |
|------|---------|--------|--------|--------|
| 美团 | 72 | 58 | 14 | 80.6% |
| 饿了么 | 72 | 46 | 26 | 63.9% |
| 京东 | 72 | 48 | 24 | 66.7% |

### 字段分类统计

| 类别 | 字段数 | 美团覆盖率 | 饿了么覆盖率 | 京东覆盖率 |
|------|--------|-----------|-------------|-----------|
| 基础信息字段 | 4 | 75% | 75% | 100% |
| 财务指标字段 | 14 | 64.3% | 57.1% | 57.1% |
| 订单数量字段 | 3 | 100% | 100% | 100% |
| 转化率字段 | 8 | 100% | 100% | 100% |
| 流量数据字段 | 14 | 92.9% | 92.9% | 100% |
| 评分字段 | 18 | 66.7% | 44.4% | 55.6% |
| 指标得分字段 | 4 | 100% | 0% | 0% |
| 回复率字段 | 5 | 40% | 0% | 0% |
| 时间字段 | 1 | 100% | 100% | 100% |
| 完成率字段 | 1 | 100% | 100% | 0% |

---

## ⚠️ 需要特别关注的字段

### 1. 需要计算的字段
- `net_margin_rate` (到手率): 需要计算，公式：商家实收 / 营业额 * 100

### 2. 需要人工输入的字段
- `five_min_reply_rate` (5分钟回复率): 所有平台均未提供
- `one_min_reply_rate` (1分钟回复率): 所有平台均未提供

### 3. 京东独有字段
- `store_id` (门店id): 京东平台独有，数据库表中已存在
- `city` (门店所在城市): 京东平台独有，数据库表中已存在

### 4. 平台差异较大的字段
- `product_satisfaction` (商品满意度): 仅美团提供
- `packaging_satisfaction` (包装满意度): 仅美团提供
- `service_function_score` (服务功能丰富度): 京东未提供

---

## 💡 建议

### 1. 数据库字段建议
以下字段在所有平台均未提供，可以考虑从数据库中移除：
- `real_actual_income` (真实实收)
- `promotion_cost` (推广花费)
- `gift_sausage_cost` (赠红肠成本)
- `uv` (UV)

### 2. 字段映射建议
- 对于需要计算的字段，可以在ETL流程中添加计算逻辑
- 对于需要人工输入的字段，可以开发后台管理界面让用户手动填写
- 对于京东独有的字段（store_id、city），建议保留以便后续使用

### 3. 数据质量建议
- 定期验证映射后的数据准确性
- 监控缺失字段的影响
- 根据业务需求调整字段映射

---

## 📝 核对完成标记

使用此表格进行逐列核对：

- [ ] 1. date - 日期
- [ ] 2. brand_store_name - 品牌门店名称
- [ ] 3. platform_store_name - 平台门店名称
- [ ] 4. store_id - 门店id
- [ ] 5. city - 门店所在城市
- [ ] 6. actual_income - 商家实收
- [ ] 7. expense - 支出
- [ ] 8. turnover - 营业额
- [ ] 9. net_margin_rate - 到手率
- [ ] 10. original_price - 商品原价
- [ ] 11. packaging_fee - 包装费
- [ ] 12. customer_delivery_fee - 顾客配送费
- [ ] 13. customer_paid - 顾客实付
- [ ] 14. avg_paid_price - 实付单均价
- [ ] 15. activity_subsidy - 活动补贴
- [ ] 16. platform_service_fee - 平台服务费
- [ ] 17. real_actual_income - 真实实收
- [ ] 18. promotion_cost - 推广花费
- [ ] 19. gift_sausage_cost - 赠红肠成本
- [ ] 20. valid_orders - 有效订单
- [ ] 21. invalid_orders - 无效订单
- [ ] 22. merchant_cancelled_orders - 商责取消订单
- [ ] 23. merchant_cancellation_rate - 商责取消率
- [ ] 24. store_entry_rate - 入店转化率
- [ ] 25. order_conversion_rate - 下单转化率
- [ ] 26. new_customer_entry_rate - 新客入店转化率
- [ ] 27. new_customer_order_rate - 新客下单转化率
- [ ] 28. old_customer_entry_rate - 老客入店转化率
- [ ] 29. old_customer_order_rate - 老客下单转化率
- [ ] 30. repurchase_rate - 复购率
- [ ] 31. exposure_count - 曝光人数
- [ ] 32. entry_count - 入店人数
- [ ] 33. exposure_new_customer - 曝光新客
- [ ] 34. entry_new_customer - 入店新客
- [ ] 35. exposure_old_customer - 曝光老客
- [ ] 36. entry_old_customer - 入店老客
- [ ] 37. exposure_times - 曝光次数
- [ ] 38. entry_times - 入店次数
- [ ] 39. order_people - 下单人数
- [ ] 40. order_new_customer - 下单新客
- [ ] 41. order_old_customer - 下单老客
- [ ] 42. uv - UV
- [ ] 43. store_id - 门店id
- [ ] 44. city - 门店所在城市
- [ ] 45. store_score - 店铺分
- [ ] 46. peak_duration_score - 高峰营业时长得分
- [ ] 47. quality_product_rate_score - 优质商品率得分
- [ ] 48. activity_richness_score - 有效活动丰富度得分
- [ ] 49. reject_order_rate_score - 商家不接单率得分
- [ ] 50. bad_review_reply_rate_score - 差评回复率得分
- [ ] 51. online_reply_rate_score - 在线联系回复率得分
- [ ] 52. new_merchant_score - 新商家评分
- [ ] 53. menu_richness_score - 菜单丰富度得分
- [ ] 54. decoration_richness_score - 装修丰富度得分
- [ ] 55. service_function_score - 服务功能丰富度得分
- [ ] 56. product_quality_score - 商品质量分
- [ ] 57. service_experience_score - 服务体验分
- [ ] 58. product_satisfaction - 商品满意度
- [ ] 59. packaging_satisfaction - 包装满意度
- [ ] 60. overall_experience_score - 综合体验分
- [ ] 61. old_merchant_score - 老商家评分
- [ ] 62. repurchase_rate_score - 复购率指标得分
- [ ] 63. message_reply_rate_score - 消息回复率指标得分
- [ ] 64. service_negative_feedback_score - 服务负反馈率指标得分
- [ ] 65. food_safety_negative_feedback_score - 食品安全负反馈率指标得分
- [ ] 66. five_min_reply_rate - 5分钟回复率
- [ ] 67. one_min_reply_rate - 1分钟回复率
- [ ] 68. message_reply_rate - 消息回复率
- [ ] 69. food_safety_negative_feedback_rate - 食品安全负反馈率
- [ ] 70. basic_duration - 基础营业时长
- [ ] 71. meal_completion_report_rate - 出餐完成上报率
- [ ] 72. import_time - 导入时间

---

**文档生成**: 2026-02-14 14:50:00  
**核对状态**: ⏳ 待核对  
**ETL版本**: 1.0.0