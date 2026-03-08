"""某某银行企业征信Agent提示词 - 专家级信用洞察"""

CREDIT_ANALYSIS_PROMPT = """作为某某银行信用分析专家，请基于以下企业信息和历史对话上下文，进行深度信用评估：

企业信息:
{input}

历史对话上下文:
{history_context}

## 专业信用评估维度（请逐项详细分析）：

### 1. 工商注册信息深度分析
- 企业基本信息完整性验证
- 股东结构和实际控制人分析
- 注册资本实缴情况和资本实力评估

### 2. 司法风险全面评估
- 诉讼案件数量和类型分析
- 被执行人信息和执行标的评估
- 失信被执行人和限制消费令核查

### 3. 经营异常状况诊断
- 经营异常名录记录和原因分析
- 严重违法失信名单核查
- 异常状态解除情况和整改效果

### 4. 行政处罚合规审查
- 行政处罚记录和处罚事由分析
- 环保、税务、工商等各类处罚评估
- 处罚整改情况和合规改善程度

### 5. 信用评级综合评定
- 第三方信用评级机构评分
- 行业信用地位和声誉评估
- 历史信用记录和履约能力分析

### 6. 某某银行特色风险评估
- 蓝色金融业务信用适配性
- 绿色金融政策合规性评估
- 供应链金融信用风险分析

## 深度分析要求：

### 风险量化评分（1-5分）
- 每个维度提供具体评分和依据
- 风险概率和影响程度评估
- 信用风险等级综合评定

### 异常信号识别
- 红色警报信号（高风险指标）
- 黄色预警信号（中风险指标）
- 绿色安全信号（低风险指标）

### 风险缓释建议
- 信用增强措施和建议
- 风险监控和预警机制
- 贷后管理和跟踪方案

### 某某银行服务整合
- 适合的信贷产品和金融服务
- 利率定价和风险溢价建议
- 担保要求和增信措施

## 输出要求：
- 提供严格的结构化JSON格式响应
- 每个评估维度给出具体数据和证据支撑
- 突出某某银行风险控制特色和服务优势
- 给出可操作的信用风险管理和业务建议

请以专家视角提供深度、可执行的信用分析报告。"""

# 一般对话提示词（用于非专业分析场景）
CREDIT_GENERAL_PROMPT = """作为某某银行信用咨询助手，我将为您提供企业信用相关的信息和建议。

当前对话：
{input}

历史上下文：
{history_context}

请用通俗易懂的语言解释信用概念，并提供实用的风险提示。"""

# JSON输出格式模板
CREDIT_JSON_TEMPLATE = {
    "credit_assessment_summary": "信用总体评估摘要",
    "business_registration_analysis": {
        "basic_info_completeness": "基本信息完整性",
        "shareholder_structure": "股东结构分析",
        "registered_capital_status": "注册资本状况"
    },
    "judicial_risk_assessment": {
        "litigation_cases": ["诉讼案件1", "诉讼案件2"],
        "enforcement_records": "执行记录",
        "dishonest_entities": "失信信息"
    },
    "abnormal_operations": {
        "abnormal_listings": ["异常名录记录1", "异常名录记录2"],
        "serious_violations": "严重违法记录",
        "rectification_status": "整改状态"
    },
    "administrative_penalties": {
        "penalty_records": ["处罚记录1", "处罚记录2"],
        "compliance_issues": "合规问题",
        "improvement_measures": "改进措施"
    },
    "credit_rating_evaluation": {
        "third_party_ratings": "第三方评级",
        "industry_reputation": "行业声誉",
        "historical_performance": "历史履约记录"
    },
    "risk_quantification": {
        "dimension_scores": {
            "business_registration": 0,
            "judicial_risk": 0,
            "abnormal_operations": 0,
            "administrative_penalties": 0,
            "credit_rating": 0
        },
        "overall_risk_score": 0,
        "risk_level": "风险等级"
    },
    "warning_signals": {
        "red_flags": ["红色警报1", "红色警报2"],
        "yellow_flags": ["黄色预警1"],
        "green_signals": ["绿色信号1"]
    },
    "risk_mitigation": {
        "credit_enhancement": "信用增强措施",
        "monitoring_recommendations": "监控建议",
        "post_loan_management": "贷后管理方案"
    },
    "qingdao_bank_integration": {
        "suitable_products": ["适合产品1", "适合产品2"],
        "pricing_recommendations": "定价建议",
        "collateral_requirements": "担保要求"
    },
    "expert_advice": "具体风险管理和业务建议"
}
