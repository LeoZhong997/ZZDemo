-- 门店管理系统 - 数据库表结构
-- 创建时间: 2026-02-14
-- 更新时间: 2026-02-18 (修正门店映射)

-- 1. 品牌门店表
CREATE TABLE IF NOT EXISTS brand_stores (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    brand_store_name VARCHAR(100) NOT NULL UNIQUE COMMENT '品牌门店名称',
    store_address VARCHAR(200) COMMENT '门店地址',
    store_type VARCHAR(50) COMMENT '门店类型（如：直营店/加盟店）',
    open_date DATE COMMENT '开店时间',
    contact_phone VARCHAR(20) COMMENT '联系电话',
    contact_person VARCHAR(50) COMMENT '联系人',
    status ENUM('营业中', '关闭', '筹备中') DEFAULT '营业中' COMMENT '门店状态',
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_status (status),
    INDEX idx_name (brand_store_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='品牌门店信息表';

-- 2. 门店映射表
CREATE TABLE IF NOT EXISTS store_mapping (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    brand_store_id INT NOT NULL COMMENT '品牌门店ID',
    platform VARCHAR(20) NOT NULL COMMENT '平台（美团/饿了么/京东）',
    platform_store_name VARCHAR(100) NOT NULL COMMENT '平台门店名称',
    platform_store_id VARCHAR(50) COMMENT '平台门店ID（如京东的门店id）',
    city VARCHAR(100) COMMENT '门店所在城市',
    is_active TINYINT(1) DEFAULT 1 COMMENT '是否启用（0禁用/1启用）',
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_platform_store (platform, platform_store_name),
    FOREIGN KEY (brand_store_id) REFERENCES brand_stores(id) ON DELETE CASCADE,
    INDEX idx_brand_store (brand_store_id),
    INDEX idx_platform (platform),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='门店映射关系表';

-- 3. 插入品牌门店数据
INSERT INTO brand_stores (brand_store_name, store_address, store_type, contact_phone, status) VALUES
('信和店', '深圳市南山区信和广场', '直营店', '0755-12345678', '营业中'),
('龙华店', '深圳市龙华区龙华大道', '直营店', '0755-12345679', '营业中'),
('壹方城店', '深圳市南山区壹方城购物中心', '直营店', '0755-12345680', '营业中'),
('新洲店', '深圳市福田区新洲路', '直营店', '0755-12345681', '营业中'),
('塘朗店', '深圳市南山区塘朗路', '直营店', '0755-12345682', '营业中'),
('蛇口店', '深圳市南山区蛇口海上世界', '直营店', '0755-12345683', '营业中'),
('梅林店', '深圳市福田区梅林路', '直营店', '0755-12345684', '营业中'),
('马家龙店', '深圳市南山区马家龙路', '直营店', '0755-12345685', '营业中'),
('皇庭店', '深圳市福田区皇庭广场', '直营店', '0755-12345686', '营业中'),
('登良店', '深圳市南山区登良路', '直营店', '0755-12345687', '营业中'),
('车公庙店', '深圳市福田区车公庙', '直营店', '0755-12345688', '营业中'),
('大冲店', '深圳市南山区大冲', '直营店', '0755-12345689', '营业中'),
('壹方天地店', '深圳市壹方天地店', '直营店', '0755-12345680', '营业中'),
('长兴店', '深圳市长兴店', '直营店', '0755-12345679', '营业中'),
('后海店', '深圳市后海店', '直营店', '0755-12345679', '营业中');

-- 4. 插入门店映射数据（美团）- 使用实际的平台门店名称
INSERT INTO store_mapping (brand_store_id, platform, platform_store_name, is_active) VALUES
((SELECT id FROM brand_stores WHERE brand_store_name = '信和店'), '美团', '雪乡情大地锅(信和广场店)', 1),
((SELECT id FROM brand_stores WHERE brand_store_name = '龙华店'), '美团', '雪乡情东北菜馆(龙华店)', 1),
((SELECT id FROM brand_stores WHERE brand_store_name = '壹方城店'), '美团', '雪乡情东北菜馆（壹方城店）', 1),
((SELECT id FROM brand_stores WHERE brand_store_name = '壹方天地店'), '美团', '雪乡情东北菜馆(壹方天地店)', 1),
((SELECT id FROM brand_stores WHERE brand_store_name = '新洲店'), '美团', '雪乡情东北菜（新洲店）', 1),
((SELECT id FROM brand_stores WHERE brand_store_name = '塘朗店'), '美团', '雪乡情东北菜（塘朗店）', 1),
((SELECT id FROM brand_stores WHERE brand_store_name = '蛇口店'), '美团', '雪乡情东北菜（蛇口店）', 1),
((SELECT id FROM brand_stores WHERE brand_store_name = '梅林店'), '美团', '雪乡情东北菜馆（梅林店）', 1),
((SELECT id FROM brand_stores WHERE brand_store_name = '马家龙店'), '美团', '雪乡情东北菜（马家龙店）', 1),
((SELECT id FROM brand_stores WHERE brand_store_name = '皇庭店'), '美团', '雪乡情东北菜馆（皇庭广场店）', 1),
((SELECT id FROM brand_stores WHERE brand_store_name = '登良店'), '美团', '雪乡情东北菜（登良店）', 1),
((SELECT id FROM brand_stores WHERE brand_store_name = '车公庙店'), '美团', '雪乡情东北菜（车公庙店）', 1),
((SELECT id FROM brand_stores WHERE brand_store_name = '后海店'), '美团', '雪乡情铁锅炖（后海店）', 1),
((SELECT id FROM brand_stores WHERE brand_store_name = '大冲店'), '美团', '雪乡情东北菜馆（大冲店）', 1);

-- 5. 插入门店映射数据（京东）
INSERT INTO store_mapping (brand_store_id, platform, platform_store_name, platform_store_id, city, is_active) VALUES
((SELECT id FROM brand_stores WHERE brand_store_name = '车公庙店'), '京东', '念东北铁锅炖（车公庙店）', 'PPZH2680', '深圳市', 1),
((SELECT id FROM brand_stores WHERE brand_store_name = '马家龙店'), '京东', '念东北铁锅炖（马家龙店）', 'PPZH2681', '深圳市', 1),
((SELECT id FROM brand_stores WHERE brand_store_name = '长兴店'), '京东', '念东北铁锅炖（长兴店）', 'PPZH2682', '深圳市', 1),
((SELECT id FROM brand_stores WHERE brand_store_name = '车公庙店'), '京东', '雪乡情东北菜（车公庙店）', 'PPZH2683', '深圳市', 1),
((SELECT id FROM brand_stores WHERE brand_store_name = '大冲店'), '京东', '雪乡情东北菜（大冲店）', 'PPZH2684', '深圳市', 1),
((SELECT id FROM brand_stores WHERE brand_store_name = '登良店'), '京东', '雪乡情东北菜（登良旗舰店）', 'PPZH2685', '深圳市', 1),
((SELECT id FROM brand_stores WHERE brand_store_name = '皇庭店'), '京东', '雪乡情东北菜（皇庭广场店）', 'PPZH2686', '深圳市', 1),
((SELECT id FROM brand_stores WHERE brand_store_name = '马家龙店'), '京东', '雪乡情东北菜（马家龙店）', 'PPZH2687', '深圳市', 1),
((SELECT id FROM brand_stores WHERE brand_store_name = '梅林店'), '京东', '雪乡情东北菜（梅林店）', 'PPZH2688', '深圳市', 1),
((SELECT id FROM brand_stores WHERE brand_store_name = '蛇口店'), '京东', '雪乡情东北菜（蛇口店）', 'PPZH2689', '深圳市', 1),
((SELECT id FROM brand_stores WHERE brand_store_name = '塘朗店'), '京东', '雪乡情东北菜（塘朗店）', 'PPZH2690', '深圳市', 1),
((SELECT id FROM brand_stores WHERE brand_store_name = '新洲店'), '京东', '雪乡情东北菜（新洲店）', 'PPZH2691', '深圳市', 1),
((SELECT id FROM brand_stores WHERE brand_store_name = '壹方城店'), '京东', '雪乡情东北菜（壹方城店）', 'PPZH2692', '深圳市', 1),
((SELECT id FROM brand_stores WHERE brand_store_name = '壹方天地店'), '京东', '雪乡情东北菜（壹方天地店）', 'PPZH2693', '深圳市', 1),
((SELECT id FROM brand_stores WHERE brand_store_name = '后海店'), '京东', '雪乡情铁锅炖（后海店）', 'PPZH2694', '深圳市', 1),
((SELECT id FROM brand_stores WHERE brand_store_name = '信和店'), '京东', '雪乡情铁锅炖（信和广场店）', 'PPZH2695', '深圳市', 1);

-- 6. 添加饿了么门店映射
INSERT INTO store_mapping (brand_store_id, platform, platform_store_name, is_active) VALUES
((SELECT id FROM brand_stores WHERE brand_store_name = '车公庙店'), '饿了么', '雪乡情东北菜(车公庙店)', 1),
((SELECT id FROM brand_stores WHERE brand_store_name = '大冲店'), '饿了么', '雪乡情东北菜(大冲店)', 1),
((SELECT id FROM brand_stores WHERE brand_store_name = '登良店'), '饿了么', '雪乡情东北菜(登良店)', 1),
((SELECT id FROM brand_stores WHERE brand_store_name = '皇庭店'), '饿了么', '雪乡情东北菜(皇庭广场店)', 1),
((SELECT id FROM brand_stores WHERE brand_store_name = '马家龙店'), '饿了么', '雪乡情东北菜(马家龙店)', 1),
((SELECT id FROM brand_stores WHERE brand_store_name = '梅林店'), '饿了么', '雪乡情东北菜(梅林店)', 1),
((SELECT id FROM brand_stores WHERE brand_store_name = '蛇口店'), '饿了么', '雪乡情东北菜(蛇口店)', 1),
((SELECT id FROM brand_stores WHERE brand_store_name = '塘朗店'), '饿了么', '雪乡情东北菜(塘朗店)', 1),
((SELECT id FROM brand_stores WHERE brand_store_name = '新洲店'), '饿了么', '雪乡情东北菜(新洲店)', 1),
((SELECT id FROM brand_stores WHERE brand_store_name = '壹方城店'), '饿了么', '雪乡情东北菜(壹方城店)', 1),
((SELECT id FROM brand_stores WHERE brand_store_name = '壹方天地店'), '饿了么', '雪乡情东北菜(壹方天地店)', 1),
((SELECT id FROM brand_stores WHERE brand_store_name = '后海店'), '饿了么', '雪乡情铁锅炖(后海店)', 1),
((SELECT id FROM brand_stores WHERE brand_store_name = '信和店'), '饿了么', '雪乡情铁锅炖(信和广场店)', 1);
