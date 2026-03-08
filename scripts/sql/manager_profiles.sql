CREATE TABLE IF NOT EXISTS manager_profiles (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    manager_id VARCHAR(255) NOT NULL UNIQUE COMMENT '客户经理唯一标识符',
    conversation_style TEXT COMMENT '对话风格信息',
    emotional_patterns TEXT COMMENT '情感模式数据',
    response_patterns TEXT COMMENT '响应模式数据',
    tags TEXT COMMENT '客户经理标签',
    formality_level VARCHAR(50) COMMENT '形式化程度',
    response_speed VARCHAR(50) COMMENT '响应速度',
    sentiment_tone VARCHAR(50) COMMENT '情感基调',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='客户经理画像信息表';
