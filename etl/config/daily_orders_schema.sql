-- 外卖数据看板 - 每日订单汇总表
CREATE TABLE daily_orders (
    -- 主键和系统字段
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    import_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '数据导入时间',

    -- 基础信息字段
    `date` DATE NOT NULL COMMENT '订单日期',
    brand_store_name VARCHAR(100) COMMENT '品牌门店名称',
    platform VARCHAR(20) NOT NULL COMMENT '平台（美团/饿了么/京东）',
    platform_store_name VARCHAR(100) COMMENT '平台门店名称',

    -- 财务指标字段（金额统一使用 DECIMAL(10,2)，精度为元，支持到分）
    actual_income DECIMAL(10,2) COMMENT '商家实收',
    expense DECIMAL(10,2) COMMENT '支出',
    turnover DECIMAL(10,2) COMMENT '营业额',
    net_margin_rate DECIMAL(5,2) COMMENT '到手率（百分比）',
    original_price DECIMAL(10,2) COMMENT '商品原价',
    packaging_fee DECIMAL(10,2) COMMENT '包装费',
    customer_delivery_fee DECIMAL(10,2) COMMENT '顾客配送费（跑腿/自配送）',
    customer_paid DECIMAL(10,2) COMMENT '顾客实付',
    avg_paid_price DECIMAL(10,2) COMMENT '实付单均价',
    activity_subsidy DECIMAL(10,2) COMMENT '活动补贴',
    platform_service_fee DECIMAL(10,2) COMMENT '平台服务费(含佣金和配送服务费)',
    real_actual_income DECIMAL(10,2) COMMENT '真实实收',
    promotion_cost DECIMAL(10,2) COMMENT '推广花费',
    gift_sausage_cost DECIMAL(10,2) COMMENT '赠红肠成本',
    real_net_margin_rate DECIMAL(5,2) COMMENT '真实到手率（百分比）',

    -- 订单数量字段（整数）
    valid_orders INT DEFAULT 0 COMMENT '有效订单',
    invalid_orders INT DEFAULT 0 COMMENT '无效订单',
    merchant_cancelled_orders INT DEFAULT 0 COMMENT '商责取消订单',

    -- 转化率字段（百分比，保留2位小数）
    merchant_cancellation_rate DECIMAL(5,2) COMMENT '商责取消率（百分比）',
    store_entry_rate DECIMAL(5,2) COMMENT '入店转化率（百分比）',
    order_conversion_rate DECIMAL(5,2) COMMENT '下单转化率（百分比）',
    new_customer_entry_rate DECIMAL(5,2) COMMENT '新客入店转化率（百分比）',
    new_customer_order_rate DECIMAL(5,2) COMMENT '新客下单转化率（百分比）',
    old_customer_entry_rate DECIMAL(5,2) COMMENT '老客入店转化率（百分比）',
    old_customer_order_rate DECIMAL(5,2) COMMENT '老客下单转化率（百分比）',
    repurchase_rate DECIMAL(5,2) COMMENT '复购率（百分比）',

    -- 流量数据字段（整数）
    exposure_count INT DEFAULT 0 COMMENT '曝光人数',
    entry_count INT DEFAULT 0 COMMENT '入店人数',
    exposure_new_customer INT DEFAULT 0 COMMENT '曝光新客',
    entry_new_customer INT DEFAULT 0 COMMENT '入店新客',
    exposure_old_customer INT DEFAULT 0 COMMENT '曝光老客',
    entry_old_customer INT DEFAULT 0 COMMENT '入店老客',
    exposure_times INT DEFAULT 0 COMMENT '曝光次数',
    entry_times INT DEFAULT 0 COMMENT '入店次数',
    order_people INT DEFAULT 0 COMMENT '下单人数',
    order_new_customer INT DEFAULT 0 COMMENT '下单新客',
    order_old_customer INT DEFAULT 0 COMMENT '下单老客',
    uv INT DEFAULT 0 COMMENT 'UV',

    -- 评分字段（分数，通常为0-10或0-100，保留2位小数）
    store_score DECIMAL(5,2) COMMENT '店铺分',
    peak_duration_score DECIMAL(5,2) COMMENT '高峰营业时长得分',
    quality_product_rate_score DECIMAL(5,2) COMMENT '优质商品率得分',
    activity_richness_score DECIMAL(5,2) COMMENT '有效活动丰富度得分',
    reject_order_rate_score DECIMAL(5,2) COMMENT '商家不接单率得分',
    bad_review_reply_rate_score DECIMAL(5,2) COMMENT '差评回复率得分',
    online_reply_rate_score DECIMAL(5,2) COMMENT '在线联系回复率得分',
    new_merchant_score DECIMAL(5,2) COMMENT '新商家评分',
    menu_richness_score DECIMAL(5,2) COMMENT '菜单丰富度得分',
    decoration_richness_score DECIMAL(5,2) COMMENT '装修丰富度得分',
    service_function_score DECIMAL(5,2) COMMENT '服务功能丰富度得分',
    overall_experience_score DECIMAL(5,2) COMMENT '综合体验分',
    product_quality_score DECIMAL(5,2) COMMENT '商品质量分',
    service_experience_score DECIMAL(5,2) COMMENT '服务体验分',
    product_satisfaction DECIMAL(5,2) COMMENT '商品满意度',
    packaging_satisfaction DECIMAL(5,2) COMMENT '包装满意度',
    old_merchant_score DECIMAL(5,2) COMMENT '旧商家评分',

    -- 指标得分字段（保留2位小数）
    repurchase_rate_score DECIMAL(5,2) COMMENT '复购率指标得分',
    message_reply_rate_score DECIMAL(5,2) COMMENT '消息回复率指标得分',
    service_negative_feedback_score DECIMAL(5,2) COMMENT '服务负反馈率指标得分',
    food_safety_negative_feedback_score DECIMAL(5,2) COMMENT '食品安全负反馈率指标得分',

    -- 回复率字段（百分比，保留4位小数）
    five_min_reply_rate DECIMAL(5,4) DEFAULT 0 COMMENT '5分钟回复率',
    one_min_reply_rate DECIMAL(5,4) DEFAULT 0 COMMENT '1分钟回复率',
    message_reply_rate DECIMAL(5,4) DEFAULT 0 COMMENT '消息回复率',
    food_safety_negative_feedback_rate DECIMAL(5,4) DEFAULT 0 COMMENT '食品安全负反馈率',

    -- 时间字段（小时数，保留1位小数）
    basic_duration DECIMAL(6,1) COMMENT '基础营业时长（小时）',

    -- 完成率字段（百分比，保留2位小数）
    meal_completion_report_rate DECIMAL(5,2) COMMENT '出餐完成上报率（百分比）',

    -- 索引优化
    INDEX idx_date (`date`),
    INDEX idx_platform (`platform`),
    INDEX idx_brand_store (`brand_store_name`),
    INDEX idx_date_platform (`date`, `platform`),
    INDEX idx_import_time (`import_time`),

    -- 唯一约束：防止重复导入
    UNIQUE KEY uk_date_platform_store (`date`, `platform`, `brand_store_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='外卖数据看板 - 每日订单汇总表';