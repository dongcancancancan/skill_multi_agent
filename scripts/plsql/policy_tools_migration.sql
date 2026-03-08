-- policy_tools 表 PostgreSQL 迁移脚本
-- 创建政策工具表

CREATE TABLE IF NOT EXISTS public.policy_tools (
    policy_tool VARCHAR(100) NOT NULL,
    tool_property VARCHAR(200) NOT NULL,
    tool_quota VARCHAR(50),
    supported_market_entities TEXT NOT NULL,
    investment_field TEXT NOT NULL,
    discount_arrangement TEXT NOT NULL,
    policy_standard_elements TEXT,
    highlights TEXT,
    business_points TEXT NOT NULL,
    support_objects TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (policy_tool)
);

-- 插入示例数据（与MySQL版本保持一致）
INSERT INTO public.policy_tools (
    policy_tool, 
    tool_property, 
    tool_quota, 
    supported_market_entities, 
    investment_field, 
    discount_arrangement, 
    policy_standard_elements, 
    highlights, 
    business_points, 
    support_objects
) VALUES (
    '（央行）碳减排支持工具',
    '央行推出的再贷款工具',
    '-',
    '可以支持大中小微企业的相关项目',
    '碳减排三大重点领域23个子领域',
    '央行资金支持为碳减排贷款本金的 60%，期限 1 年、可展期 2 次，利率 1.75%，有 25BP 省财政补贴（结合山东版情况）',
    '',
    '',
    '',
    '21 家全国性金融机构、13 家外资银行和 5 家地方法人银行'
),
(
    '山东省版碳减排政策工具',
    '山东省财政厅、中国人民银行济南分行推出的政策工具，有再贷款减碳引导专项额度',
    '每年安排再贷款减碳引导专项额度 100 亿元',
    '只支持涉农、民营、小微等符合支农支小再贷款的市场主体',
    '碳减排三大重点领域23个子领域和绿色贷款领域',
    '省财政对人民银行发放的 1 年期再贷款减碳引导专项额度给予 25BP 的贴息，再贷款展期期间予以贴息，每笔最多享受 3 年贴息支持',
    '1.符合支农支小范围内；（3000万以内民营小微）\n2.符合绿色产业目录；\n3.贷款利率不得高于5.5%。',
    '符合支小支农再贷款，可申请1.75%的再贷款，套用碳减排政策工具，还可享受省财政25BP的补贴，资金成本低至1.5%，成本与FTP的差额部分全部返还分支行。',
    '1.符合绿色金融分类的业务及时在信管系统打标；\n2.贸易合同、资金使用证明的资金用途一致，且必须要符合绿色信贷投向；\n3.总行公司部每月10日前向人民银行报送，人民银行不接受隔月申报的业务，申报的业务必须在当月支农支小再贷款范围内的上一个月放款的业务。\n4.申请碳减排政策工具的业务如提前还款，总行需退还相应金额的补贴或追加同等金额的业务。',
    '城商行、农商行等地方法人金融机构'
);
