# 外卖数据看板 - 多平台字段映射配置
# Key: MySQL表字段名 (daily_orders)
# Value: 平台原始Excel列名

FIELD_MAPPING = {
    # ========== 美团 ==========
    "meituan": {
        # 基础信息字段
        "date": "日期",
        "brand_store_name": None,  # 通过映射表获取
        "platform_store_name": "门店名称",  # 从源文件的"门店名称"列读取
        "store_id": "门店id",
        "city": "门店所在城市",

        # 财务指标字段
        "actual_income": "营业收入",
        "expense": "补贴及支出",
        "turnover": "优惠前总额",  # 修正：使用优惠前总额作为营业额
        "net_margin_rate": None,  # 到手率需要计算，原始数据无
        "original_price": "商品原价",
        "packaging_fee": "包装费",
        "customer_delivery_fee": "顾客配送费（跑腿/自配送）",
        "customer_paid": "顾客实付",
        "avg_paid_price": "实付单均价",
        "activity_subsidy": "活动补贴",
        "platform_service_fee": "平台服务费(含佣金和配送服务费)",
        "real_actual_income": None,  # 真实实收未单独列出
        "promotion_cost": None,  # 推广花费未列出
        "gift_sausage_cost": None,  # 赠红肠成本未列出
        "real_net_margin_rate": None,  # 真实到手率需要计算

        # 订单数量字段
        "valid_orders": "有效订单",
        "invalid_orders": "取消订单",  # 修正：使用取消订单作为无效订单
        "merchant_cancelled_orders": "商责取消订单",

        # 转化率字段
        "merchant_cancellation_rate": "商责取消率",  # 修正：使用商责取消率
        "store_entry_rate": "入店转化率",
        "order_conversion_rate": "下单转化率",
        "new_customer_entry_rate": "新客入店转化率",
        "new_customer_order_rate": "新客下单转化率",
        "old_customer_entry_rate": "老客入店转化率",
        "old_customer_order_rate": "老客下单转化率",
        "repurchase_rate": "复购率",

        # 流量数据字段
        "exposure_count": "曝光人数",
        "entry_count": "入店人数",
        "exposure_new_customer": "曝光新客",
        "entry_new_customer": "入店新客",
        "exposure_old_customer": "曝光老客",
        "entry_old_customer": "入店老客",
        "exposure_times": "曝光次数",
        "entry_times": "入店次数",
        "order_people": "下单人数",
        "order_new_customer": "下单新客",
        "order_old_customer": "下单老客",
        "uv": None,  # UV未列出

        # 评分字段
        "store_score": "店铺分",
        "peak_duration_score": "高峰营业时长得分",
        "quality_product_rate_score": "优质商品率得分",
        "activity_richness_score": "有效活动丰富度得分",
        "reject_order_rate_score": "商家不接单率得分",
        "bad_review_reply_rate_score": "差评回复率得分",
        "online_reply_rate_score": "在线联系回复率得分",
        "new_merchant_score": "overall_experience_score",  # 美团新商家评分映射为综合体验分
        "menu_richness_score": "菜单丰富度得分",
        "decoration_richness_score": "装修丰富度得分",
        "service_function_score": "服务功能丰富度得分",
        "product_quality_score": "商品质量分",
        "service_experience_score": "服务体验分",
        "product_satisfaction": "商品满意度",  # 添加：商品满意度
        "packaging_satisfaction": "包装满意度",  # 添加：包装满意度

        # 指标得分字段
        "repurchase_rate_score": "复购率指标得分",
        "message_reply_rate_score": "消息回复率指标得分",
        "service_negative_feedback_score": "服务负反馈率指标得分",
        "food_safety_negative_feedback_score": "食品安全负反馈率指标得分",

        # 回复率字段
        "five_min_reply_rate": None,  # 5分钟回复率需要人工输入
        "one_min_reply_rate": None,  # 1分钟回复率需要人工输入
        "message_reply_rate": "消息回复率",
        "food_safety_negative_feedback_rate": "食品安全负反馈率",

        # 时间字段
        "basic_duration": "基础营业时长",  # 修正：添加基础营业时长

        # 完成率字段
        "meal_completion_report_rate": "出餐完成上报率",
    },

    # ========== 饿了么 ==========
    "eleme": {
        # 基础信息字段
        "date": "日期",
        "brand_store_name": None,  # 通过映射表获取
        "platform_store_name": "门店名称",  # 从源文件的"门店名称"列读取
        "store_id": "门店编号",
        "city": "城市名称",

        # 财务指标字段
        "actual_income": "收入",
        "expense": "支出",
        "turnover": "营业额",
        "net_margin_rate": None,  # 到手率需要计算
        "original_price": None,  # 商品原价未列出
        "packaging_fee": "打包费",
        "customer_delivery_fee": "商家应收配送费",
        "customer_paid": "顾客实付总额",
        "avg_paid_price": "单均实付",
        "activity_subsidy": "活动补贴",
        "platform_service_fee": "平台技术服务费",
        "real_actual_income": None,  # 真实实收未单独列出
        "promotion_cost": None,  # 推广花费未列出
        "gift_sausage_cost": None,  # 赠红肠成本未列出
        "real_net_margin_rate": None,  # 真实到手率需要计算

        # 订单数量字段
        "valid_orders": "有效订单",
        "invalid_orders": "无效订单",
        "merchant_cancelled_orders": "商责退单数",

        # 转化率字段
        "merchant_cancellation_rate": "商责取消率",
        "store_entry_rate": "进店转化率",
        "order_conversion_rate": "下单转化率",
        "new_customer_entry_rate": "新客进店转化率",
        "new_customer_order_rate": "新客下单转化率",
        "old_customer_entry_rate": "老客进店转化率",
        "old_customer_order_rate": "老客下单转化率",
        "repurchase_rate": "近30日复购率",  # 修正：使用近30日复购率

        # 流量数据字段
        "exposure_count": "曝光人数",
        "entry_count": "进店人数",
        "exposure_new_customer": "新客曝光人数",
        "entry_new_customer": "新客进店人数",
        "exposure_old_customer": "老客曝光人数",
        "entry_old_customer": "老客进店人数",
        "exposure_times": "曝光次数",
        "entry_times": "进店次数",
        "order_people": "下单人数",
        "order_new_customer": "新客下单人数",
        "order_old_customer": "老客下单人数",
        "uv": None,  # UV未列出

        # 评分字段
        "new_merchant_score": "店铺评分",
        "peak_duration_score": "高峰营业时长得分",
        "quality_product_rate_score": "优质商品率得分",
        "activity_richness_score": "有效活动丰富度得分",
        "reject_order_rate_score": "商家不接单率得分",
        "bad_review_reply_rate_score": "差评回复率得分",
        "online_reply_rate_score": "在线联系回复率得分",
        "menu_richness_score": "菜单丰富度得分",
        "decoration_richness_score": "装修丰富度得分",
        "service_function_score": "昨日服务功能丰富度指标得分",
        "product_quality_score": None,
        "service_experience_score": None,
        "product_satisfaction": None,
        "packaging_satisfaction": None,

        # 指标得分字段
        "repurchase_rate_score": None,  # 复购率指标得分未列出
        "message_reply_rate_score": None,  # 消息回复率指标得分未列出
        "service_negative_feedback_score": None,  # 服务负反馈率指标得分未列出
        "food_safety_negative_feedback_score": None,  # 食品安全负反馈率指标得分未列出

        # 回复率字段
        "five_min_reply_rate": None,  # 5分钟回复率需要人工输入
        "one_min_reply_rate": None,  # 1分钟回复率需要人工输入
        "message_reply_rate": None,
        "food_safety_negative_feedback_rate": None,

        # 时间字段
        "basic_duration": "营业时长",

        # 完成率字段
        "meal_completion_report_rate": "近7日出餐完成上报率当前值",
    },

    # ========== 京东 ==========
    "jd": {
        # 基础信息字段
        "date": "日期",
        "brand_store_name": None,  # 通过映射表获取
        "platform_store_name": "门店名称",  # 从源文件的"门店名称"列读取
        "store_id": "门店id",
        "city": "门店所在城市",
        
        # 财务指标字段
        "actual_income": "收入",
        "expense": "支出",
        "turnover": "营业额",
        "original_price": None,
        "packaging_fee": None,
        "customer_delivery_fee": None,
        "customer_paid": "顾客实付",
        "avg_paid_price": "实付单均价",
        "activity_subsidy": "活动补贴",
        "platform_service_fee": "佣金",
        
        # 订单数量字段
        "valid_orders": "有效订单",
        "invalid_orders": None,
        "merchant_cancelled_orders": None,
        
        # 转化率字段
        "store_entry_rate": "入店转化率",
        "order_conversion_rate": "下单转化率",
        "merchant_cancellation_rate": None,
        "new_customer_entry_rate": None,
        "new_customer_order_rate": None,
        "old_customer_entry_rate": None,
        "old_customer_order_rate": None,
        "repurchase_rate": None,
        
        # 流量数据字段
        "exposure_count": "曝光人数",
        "entry_count": "入店人数",
        "exposure_times": "曝光次数",
        "entry_times": "入店次数",
        "exposure_new_customer": None,
        "entry_new_customer": None,
        "exposure_old_customer": None,
        "entry_old_customer": None,
        "order_people": None,
        "order_new_customer": None,
        "order_old_customer": None,
        
        # 评分字段
        "store_score": None,
        "peak_duration_score": None,
        "quality_product_rate_score": None,
        "activity_richness_score": None,
        "reject_order_rate_score": None,
        "bad_review_reply_rate_score": None,
        "online_reply_rate_score": None,
        "new_merchant_score": None,
        "menu_richness_score": None,
        "decoration_richness_score": None,
        "service_function_score": None,
        "product_quality_score": None,
        "service_experience_score": None,
        "product_satisfaction": None,
        "packaging_satisfaction": None,
        
        # 指标得分字段
        "repurchase_rate_score": None,
        "message_reply_rate_score": None,
        "service_negative_feedback_score": None,
        "food_safety_negative_feedback_score": None,
        
        # 回复率字段
        "message_reply_rate": None,
        "food_safety_negative_feedback_rate": None,
        
        # 时间字段
        "basic_duration": "日均营业时长",
        
        # 完成率字段
        "meal_completion_report_rate": None,
        
        # 未提供字段（设置为 None）
        "net_margin_rate": None,
        "real_actual_income": None,
        "promotion_cost": None,
        "gift_sausage_cost": None,
        "real_net_margin_rate": None,
        "merchant_activity_cost": None,
        "commission": None,
        "delivery_service_fee": None,
        "peak_duration": None,
        "on_time_rate": None,
        "avg_fulfillment_time": None,
        "merchant_intervention_rate": None,
        "activity_orders": None,
        "activity_strength": None,
        "roi": None,
        "uv": None,
        "five_min_reply_rate": None,
        "one_min_reply_rate": None,
        "old_merchant_score": None,
        "overall_experience_score": None,
    },
}

# 字段数据类型映射（用于Excel读取时的数据类型转换）
FIELD_TYPES = {
    # 日期类型
    "date": "date",

    # 字符串类型
    "brand_store_name": "str",
    "platform_store_name": "str",
    "platform": "str",

    # 金额类型（使用Decimal）
    "actual_income": "decimal",
    "expense": "decimal",
    "turnover": "decimal",
    "net_margin_rate": "decimal",
    "original_price": "decimal",
    "packaging_fee": "decimal",
    "customer_delivery_fee": "decimal",
    "customer_paid": "decimal",
    "avg_paid_price": "decimal",
    "activity_subsidy": "decimal",
    "platform_service_fee": "decimal",
    "real_actual_income": "decimal",
    "promotion_cost": "decimal",
    "gift_sausage_cost": "decimal",
    "real_net_margin_rate": "decimal",

    # 整数类型
    "valid_orders": "int",
    "invalid_orders": "int",
    "merchant_cancelled_orders": "int",
    "exposure_count": "int",
    "entry_count": "int",
    "exposure_new_customer": "int",
    "entry_new_customer": "int",
    "exposure_old_customer": "int",
    "entry_old_customer": "int",
    "exposure_times": "int",
    "entry_times": "int",
    "order_people": "int",
    "order_new_customer": "int",
    "order_old_customer": "int",
    "uv": "int",

    # 百分比类型（Decimal）
    "merchant_cancellation_rate": "decimal",
    "store_entry_rate": "decimal",
    "order_conversion_rate": "decimal",
    "new_customer_entry_rate": "decimal",
    "new_customer_order_rate": "decimal",
    "old_customer_entry_rate": "decimal",
    "old_customer_order_rate": "decimal",
    "repurchase_rate": "decimal",
    "five_min_reply_rate": "decimal",
    "one_min_reply_rate": "decimal",
    "message_reply_rate": "decimal",
    "food_safety_negative_feedback_rate": "decimal",
    "meal_completion_report_rate": "decimal",

    # 评分类型（Decimal）
    "store_score": "decimal",
    "peak_duration_score": "decimal",
    "quality_product_rate_score": "decimal",
    "activity_richness_score": "decimal",
    "reject_order_rate_score": "decimal",
    "bad_review_reply_rate_score": "decimal",
    "online_reply_rate_score": "decimal",
    "new_merchant_score": "decimal",
    "menu_richness_score": "decimal",
    "decoration_richness_score": "decimal",
    "service_function_score": "decimal",
    "overall_experience_score": "decimal",
    "product_quality_score": "decimal",
    "service_experience_score": "decimal",
    "product_satisfaction": "decimal",
    "packaging_satisfaction": "decimal",
    "old_merchant_score": "decimal",
    "repurchase_rate_score": "decimal",
    "message_reply_rate_score": "decimal",
    "service_negative_feedback_score": "decimal",
    "food_safety_negative_feedback_score": "decimal",

    # 时长类型（Decimal）
    "basic_duration": "decimal",

    # 系统字段
    "import_time": "datetime",
}