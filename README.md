# 蓝绿金融助手系统 (Multi-Agent Financial Assistant)

蓝绿金融助手系统是一个基于LangGraph 0.6.2的智能体协作平台，通过多个专业智能体的协同工作，提供全面的金融分析服务，特别专注于蓝绿金融（绿色金融）领域。系统采用有状态的手动图架构设计，支持人工中断恢复，使用封装的tools进行智能体调用，基于session_id进行状态管理。

## 🏗️ 系统架构

### 有状态的手动图架构设计

系统采用有状态的手动图架构设计，不需要分布式部署智能体，所有智能体调用通过封装工具进行，基于session_id进行状态管理：

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Web Server                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                  /api/agents/main_graph               │  │
│  └───────────────────────────────────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 React Team Selection Agent                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                  LangGraph React Agent                │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │          Team Selection Tools                   │  │  │
│  │  │  - enterprise_profile_team_tool                 │  │  │
│  │  │  - blue_green_access_team_tool                  │  │  │
│  │  │  - blue_green_policy_team_tool                  │  │  │
│  │  │  - blue_green_product_team_tool                 │  │  │
│  │  │  - blue_green_solution_team_tool                │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 React Agent Execution Layer                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                  LangGraph React Agent                │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │            Encapsulated Tools                   │  │  │
│  │  │  - financial_tool                               │  │  │
│  │  │  - enterprise_profile_tool                      │  │  │
│  │  │  - credit_tool                                  │  │  │
│  │  │  - counterparty_tool                            │  │  │
│  │  │  - blue_green_access_tool                       │  │  │
│  │  │  - ... (所有封装工具)                           │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    Encapsulated Tools Layer                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  │ financial_tool  │  │ enterprise_     │  │ credit_tool     │
│  │                 │  │ profile_tool    │  │                 │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  │ counterparty_   │  │ blue_green_     │  │ policy_lib_     │
│  │ tool            │  │ access_tool     │  │ tool            │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘
└─────────────────────────────────────────────────────────────┘
```

### 架构优势

1. **无需分布式部署**: 所有智能体通过封装工具本地调用，无需HTTP API调用，减少网络开销
2. **有状态设计**: 基于session_id的状态管理，支持人工中断恢复和上下文保持
3. **简化架构**: 去除HTTP agent层，直接使用封装工具调用本地智能体功能
4. **高效执行**: 工具调用在本地进行，提高执行效率和响应速度

### 架构职责划分

#### 1. 团队选择层 (React Team Selection Agent)
- **职责**: 分析用户输入，根据问题意图智能选择最合适的一个或多个专业团队来解决用户问题
- **工具**: 5个团队选择工具，每个对应一个专业团队
- **决策机制**: LLM基于用户输入意图和团队工具描述，动态选择单个或多个团队组合来全面解决复杂问题
- **并行支持**: parallel_tool_calls=True (支持并行选择多个团队，LLM基于问题复杂度和意图选择最优团队组合)

#### 2. Agent执行层 (React Agent Execution Layer)
- **职责**: 执行所选团队内的具体Agent分析任务
- **工具**: 所有Agent API调用工具，每个Agent一个专用工具
- **决策机制**: LLM基于工具描述选择调用哪些Agent
- **并行支持**: parallel_tool_calls=True (支持并行调用)

#### 3. 封装工具层 (Encapsulated Tools Layer)
- **职责**: 提供所有Agent功能的封装工具调用接口，直接调用本地Agent实现
- **实现方式**: 使用Python函数封装，无需HTTP API调用
- **优势**: 减少网络开销，提高执行效率，简化部署架构
- **工具类型**: 所有专业Agent功能都提供对应的封装工具

## 🔧 核心功能

### 团队分组设计

#### 企业画像分析团队 (enterprise_profile_team)
- **对应Agent**: FinancialAgent, EnterpriseProfileAgent, CreditAgent, CounterpartyAgent
- **职责**: 企业财务分析、画像分析、信用评估、交易对手分析

#### 蓝绿准入评估团队 (blue_green_access_team)
- **对应Agent**: BlueGreenAccessAgent, EnterpriseProfileAgent, PolicyLibAgent, CreditAgent
- **职责**: 蓝绿准入分析、企业画像查询、政策库查询、信用风险评估

#### 蓝绿政策分析团队 (blue_green_policy_team)
- **对应Agent**: PolicyLibAgent, BlueGreenPolicyAgent, CaseLibAgent
- **职责**: 政策库查询、蓝绿政策分析、案例库查询

#### 蓝绿产品推荐团队 (blue_green_product_team)
- **对应Agent**: ProductAgent, BlueGreenProductAgent, SupplyChainAgent
- **职责**: 金融产品匹配、蓝绿产品分析、供应链分析

#### 蓝绿解决方案生成团队 (blue_green_solution_team)
- **对应Agent**: 所有相关Agent工具
- **职责**: 综合解决方案生成，多维度复杂问题处理

## 📋 执行流程

### 统一React代理工作流

系统采用统一的React代理工作流，整合团队选择和执行，使用顺序工具调用（`parallel_tool_calls=True`），最大迭代3次：

```
客户请求
  │
  ▼
FastAPI端点 (/api/agents/main_graph)
  │
  ▼
React Team Agent (统一代理)
  │  ┌─────────────────────────────────────────────────┐
  │  │           团队执行工具集                        │
  │  │  - enterprise_profile_team_tool                │
  │  │  - blue_green_access_team_tool                 │
  │  │  - blue_green_policy_team_tool                 │
  │  │  - blue_green_product_team_tool                │
  │  │  - blue_green_solution_team_tool               │
  │  └─────────────────────────────────────────────────┘
  │
  ▼
智能选择和执行团队工具 (基于用户输入意图)
  │
  ▼
封装工具执行 (直接调用本地Agent功能)
  │
  ▼
返回最终结果 → 客户
```

### 🎯 状态管理与中断恢复协调机制

#### 本地状态管理设计
- 采用轻量级状态管理，所有状态在内存中处理，无需分布式存储
- 状态通过函数参数传递，支持中断恢复和上下文保持

#### 状态持久化架构设计

**设计目标**: 实现高效的状态管理机制，支持人工中断恢复，使用本地内存存储，简化部署架构。

**状态存储服务架构**:
```
┌─────────────────────────────────────────────────────────────┐
│                    State Storage Service                    │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                  Memory Storage                       │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │          In-Memory Dictionary                  │  │  │
│  │  │  - session_id → state_data (with metadata)     │  │  │
│  │  │  - Automatic cleanup (optional)                │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**状态结构设计**:
```python
# 状态数据结构
{
    # 核心执行数据
    "input": str,                   # 用户原始输入或AI生成的指令
    "session_id": str,              # 会话标识符（关键：用于状态恢复）
    "metadata": Dict[str, Any],     # 元数据信息
    "results": Dict[str, Any],      # 各Agent执行结果（关键：用于进度跟踪）
    "messages": List[Dict],         # 完整的对话历史（关键：用于上下文恢复）
    
    # 执行上下文
    "current_team": str,            # 当前执行的团队
    "executed_tools": List[str],    # 已执行的工具列表
    "intervention_data": Dict,      # 中断相关数据
    
    # 存储元数据（由存储服务自动添加）
    "_storage_metadata": {
        "last_updated": str,        # ISO格式时间戳
        "version": str,             # 状态版本
        "size": int,                # 状态大小（字节）
        "ttl": int                  # 生存时间（秒）
    }
}
```

**状态存储服务接口设计**:
```python
class StateStorageService:
    """状态存储服务 - 提供状态持久化功能"""
    
    def save_state(self, session_id: str, state: Dict[str, Any]) -> bool:
        """保存状态到存储"""
        pass
    
    def load_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """从存储加载状态"""
        pass
    
    def delete_state(self, session_id: str) -> bool:
        """删除状态"""
        pass
    
    def get_all_sessions(self) -> Dict[str, Any]:
        """获取所有会话状态信息（用于监控和管理）"""
        pass
    
    def setup_redis(self, redis_client):
        """设置Redis客户端（用于后期扩展）"""
        pass
```

**阶段一：内存存储实现方案**:
- **存储机制**: 使用Python字典实现内存存储，键为session_id，值为包含状态数据和元数据的字典
- **数据序列化**: 状态数据直接存储为Python对象，无需序列化
- **内存管理**: 可选的自动清理机制，基于LRU算法或TTL过期
- **并发控制**: 使用线程锁确保多线程环境下的数据安全
- **监控接口**: 提供会话列表查询和状态信息统计功能

**阶段二：扩展性设计**:
- **接口抽象**: 存储服务提供统一的接口，支持未来扩展
- **内存优化**: 优化内存使用，支持大规模会话管理
- **持久化选项**: 可根据需要添加文件系统或其他轻量级持久化

#### 中断恢复的状态持久化流程

**中断检测与保存**:
```
Agent执行 → 检测中断条件 → 调用状态存储服务 → 保存完整状态 → 返回中断信息
    │           │               │                  │               │
    ▼           ▼               ▼                  ▼               ▼
业务逻辑    特定中断条件    StateStorageService   内存存储      客户端显示
执行        (如三证缺失)   .save_state()         (session_id    中断表单
                          → state_data)
```

**状态恢复与继续执行**:
```
客户端提交 → 加载保存状态 → 合并补充数据 → 继续执行 → 返回最终结果
补充数据    StateStorageService   状态合并    Agent执行
           .load_state()        算法
           → state_data
```

**分布式环境中的状态一致性保障**:
1. **序列化传递**: 整个request字典在工具请求中序列化传递
2. **深拷贝机制**: 每个Agent操作独立的状态副本，避免状态污染
3. **结果积累**: 执行结果通过`results`字段积累，提供隐式的执行进度跟踪
4. **外部存储**: 中断时将状态保存到状态存储服务，基于`session_id`进行检索

#### 中断恢复流程
```
中断检测 → 状态保存 → 客户端交互 → 状态恢复 → 继续执行
    │          │           │           │           │
    ▼          ▼           ▼           ▼           ▼
Agent发现   调用状态   用户提供   加载保存   从中断点
中断条件    存储服务   补充数据   的状态    继续执行
          保存状态             并合并数据
```

#### 分层回退的状态衔接
- **调度层**: 维护团队选择状态和整体执行进度
- **Agent层**: 检测业务逻辑特定的中断条件，调用状态存储服务
- **状态服务层**: 提供统一的状态持久化接口，支持多种存储后端
- **精准恢复**: 基于`session_id`和`results`字段确定恢复点

这种设计既保持了Agent的无状态特性，又通过统一的状态存储服务实现了中断恢复能力，同时为后期Redis集成提供了清晰的扩展路径。

### 并行团队选择机制

系统利用LLM的并行工具调用功能（`model.bind_tools(tools, parallel_tool_calls=True)`）实现动态团队选择：

- **并行选择**: LLM同时选择多个适合的团队处理复杂问题
- **动态路由**: 基于用户输入内容智能选择执行团队，而非固定团队
- **性能优化**: 减少团队选择和执行的整体延迟

### 状态管理设计

系统采用增强的状态管理机制确保工具调用时的状态安全性：

```python
{
    "input": str,           # 用户原始输入或AI生成的指令
    "session_id": str,      # 会话标识符
    "metadata": Dict[str, Any],  # 元数据信息
    "results": Dict[str, Any],   # 各Agent执行结果
    "messages": List[Dict]  # 完整的对话历史
}
```

**关键特性**:
- **深拷贝机制**: 每个Agent操作独立的状态副本，避免状态污染
- **消息字段支持**: 完整的对话上下文记录
- **执行进度跟踪**: 通过results字段隐式跟踪执行进度，支持精确恢复

### 正常传递流程

```
客户请求 
  │
  ▼
FastAPI端点 (/api/agents/main_graph)
  │
  ▼
React Team Agent (并行选择团队)
  │
  ▼
Agent执行层 (顺序工具调用)
  │
  ▼
封装工具执行 (直接调用本地Agent功能)
  │
  ▼
返回最终结果 → 客户
```

### 中断流程

```
客户请求
  │
  ▼
FastAPI端点
  │
  ▼
React Team Agent
  │
  ▼
封装工具执行 (直接调用本地Agent功能)
  │
  ▼
具体Agent执行 (如BlueGreenAccessAgent)
  │
  ▼
Agent发现需要中断条件 (如三证信息缺失)
  │
  ▼
抛出InterventionRequiredException
  │
  ▼
异常向上传播 → 调度层捕获
  │
  ▼
FastAPI层返回标准化中断信息 → 客户
```

### 恢复流程

```
客户提供补充数据
  │
  ▼
FastAPI端点 (/api/agents/intervention/resume)
  │
  ▼
调度层恢复状态 (基于results字段跟踪执行进度)
  │
  ▼
FastAPI层处理恢复请求
  │
  ▼
重新调用封装工具 (跳过已完成的Agent)
  │
  ▼
Agent完成剩余分析
  │
  ▼
返回最终结果 → 客户
```

### 人工中断机制

系统采用分布式中断处理机制，各个基础分析型agent负责检测自身业务逻辑中的中断条件，并通过统一的异常格式向上反馈中断信息。所有智能体调用通过封装工具进行，无需HTTP API调用：

```
开始蓝绿准入判断
  │
  ▼
调用封装工具 → blue_green_access_tool(request)
  │
  ▼
工具执行 → BlueGreenAccessAgent.run(request)
  │
  ▼
Agent检测三证信息缺失 → 触发人工中断异常
  │
  ▼
异常向上传播 → 调度层捕获并暂停执行
  │
  ▼
返回标准化中断信息给客户端
  │
  ▼
用户界面显示三证信息补充表单
  │
  ▼
用户填写并提交三证信息
  │
  ▼
客户端调用resume接口 → 提供补充信息
  │
  ▼
系统恢复执行 → 重新调用相应封装工具
  │
  ▼
工具完成剩余分析 → 返回最终结果
```

#### 中断处理原则

1. **Agent层面判断**: 每个基础分析型agent负责检测自身业务逻辑中的中断条件
2. **统一异常格式**: 使用标准化的中断异常格式向上反馈

#### 中断异常格式

```python
class InterventionRequiredException(Exception):
    def __init__(self, intervention_type: str, required_data: Dict, message: str):
        self.intervention_type = intervention_type  # 中断类型
        self.required_data = required_data          # 需要补充的数据结构
        self.message = message                      # 用户提示信息
```

#### 示例中断场景

- **三证信息缺失**: BlueGreenAccessAgent检测到企业营业执照、组织机构代码、税务登记证缺失
- **数据不完整**: 其他Agent检测到关键业务数据缺失
- **人工审核**: 需要人工介入的复杂决策场景

## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动服务

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 使用示例

#### 直接调用封装工具

```python
from app.multiAgent.dispatch.dispatch_teams import get_team_tools
from app.multiAgent.tools.calling import execute_tool

# 获取企业画像团队工具
team_tools = get_team_tools("enterprise_profile_team")

# 准备状态数据
request = {
    "input": "分析腾讯控股2023年财务情况"
}

# 直接调用封装工具
results = {}
for tool in team_tools:
    result = execute_tool(tool, request)
    results[tool.name] = result

print(results)
```

#### 使用React代理执行团队分析

```python
from app.multiAgent.dispatch.dispatch_graph_builder import build_analysis_graph

# 构建分析图
graph = build_analysis_graph()

# 准备输入状态
initial_request = {
    "input": "生成阿里巴巴集团全面企业画像"
}

# 执行图
final_request = graph.invoke(initial_request)
print(final_request["results"])
```

#### 处理中断恢复

```python
from app.multiAgent.dispatch.dispatch_graph_builder import build_analysis_graph

# 构建分析图
graph = build_analysis_graph()

# 从中断点恢复执行
resume_state = {
    "input": "继续企业画像分析",
    "session_id": "session_003",
    "provided_data": {
        "business_license": "123456789",
        "organization_code": "987654321",
        "tax_registration": "456789123"
    },
    "previous_results": {...}  # 之前保存的结果
}

final_request = graph.invoke(resume_state)
print(final_request["results"])
```

## 🔧 技术特性

- **并行执行**: 支持并行工具调用，提高执行效率
- **错误处理**: 统一的异常处理和重试机制
- **可扩展性**: 模块化架构，易于添加新团队和Agent
- **配置化管理**: 通过配置文件管理API端点和工作流参数

## 🛠️ 工具描述增强方案

### 工具描述设计原则

系统采用增强的工具描述机制，确保AI智能体能够生成准确的调用指令：

```python
@tool(
    description="[工具名称]：由AI智能体调用的[功能描述]。"
                "调用要求：AI智能体应根据当前对话上下文生成具体的[功能]指令。"
                "参数结构：request字典必须包含："
                "  - 'input': 字符串，由AI生成的[具体指令格式]"
                "  - 'session_id': 字符串，会话标识符用于上下文跟踪"
                "示例调用：{'input': '[具体示例指令]', 'session_id': 'sess_123456'}"
                "支持能力：[支持的具体功能列表]。"
                "注意：[特定的调用注意事项]。"
)
```

### 主要工具描述示例

#### 财务分析工具
```python
@tool(
    description="财务分析工具：由AI智能体调用的专业财务分析功能。"
                "调用要求：AI智能体应根据当前对话上下文生成具体的财务分析指令。"
                "参数结构：request字典必须包含："
                "  - 'input': 字符串，由AI生成的财务分析具体指令，例如：'计算某公司2023年流动比率'或'分析利润表趋势'"
                "  - 'session_id': 字符串，会话标识符用于上下文跟踪"
                "示例调用：{'input': '分析腾讯控股2023年第四季度净利润增长率', 'session_id': 'sess_123456'}"
                "支持能力：财务报表分析、财务比率计算、趋势分析、同业对比等专业财务分析功能。"
                "注意：input字段应由AI智能体基于用户查询和当前对话状态生成，不是直接的用户原始输入。"
)
```

#### 企业画像工具
```python
@tool(
    description="企业画像工具：由AI智能体调用的企业全面分析功能。"
                "调用要求：AI智能体应生成具体的企业分析指令。"
                "参数结构：request字典必须包含："
                "  - 'input': 字符串，由AI生成的企业分析指令，例如：'生成某公司全面画像报告'或'分析企业基本面情况'"
                "  - 'session_id': 字符串，会话标识符"
                "示例：{'input': '生成阿里巴巴集团全面企业画像', 'session_id': 'sess_123456'}"
                "支持能力：基本信息、财务状况、经营情况、风险评估、发展前景等全面分析。"
                "注意：input应明确指定目标企业和需要重点分析的方面。"
)
```

## 🤖 企业画像React代理设计

### 设计目标
创建专用的React代理来处理企业画像查询，使用并行工具调用（`parallel_tool_calls=True`），实现真实的工作流，去除模拟响应。

### 工具集设计
基于现有的企业画像agent，创建以下企业画像专用工具：

#### 工具列表
- `query_enterprise_basic_info_tool`: 查询企业基本信息（名称、类型、注册资本、成立日期等）
- `query_equity_structure_tool`: 查询股权结构信息
- `query_enterprise_api_tool`: 查询企业API信息（环保处罚、司法风险、经营异常等）
- `enterprise_profile_analysis_tool`: 综合企业画像分析工具

#### 工具实现原则
- 使用`@tool`装饰器定义
- 直接调用现有企业画像agent中的相应方法
- 返回结构化数据而不是模拟响应
- 支持并行工具调用（`parallel_tool_calls=True`）

### 代理创建方法
实现`create_react_enterprise_profile_agent`方法：
- 绑定企业画像专用工具列表
- 设置`parallel_tool_calls=True`启用并行工具调用
- 提供优化的提示词，指导代理如何并行使用工具
- 返回一个React代理实例

### 工作流设计
#### 并行工具调用策略
- 代理根据用户输入识别需要查询的信息维度
- 对于综合查询（如"企业全面信息"），并行调用多个相关工具
- 对于特定查询（如只问"经营范围"），可能只调用单个工具

#### 提示词设计
提示词指导代理：
- 识别用户意图和需要的信息类型
- 决定并行调用哪些工具
- 整合工具结果生成完整响应

### 集成与数据源
#### 数据源集成
- 工具调用现有的企业画像agent（`app/multiAgent/agents/enterprise_profile_agent.py`）
- 使用已有的API工具（如`app/multiAgent/tools/`中的查询工具）

#### 错误处理
- 实现健壮的错误处理机制
- 确保单个工具失败不影响其他工具的执行

## 📁 项目结构

```
app/
├── api/
│   └── agents.py              # API接口定义
├── multiAgent/
│   ├── agents/                # 各个专业Agent实现
│   ├── dispatch/              # 团队调度和工具调用
│   ├── analysis/              # 蓝绿分析相关Agent
│   └── tools/                 # 工具函数和API调用
└── utils/                     # 工具类和配置管理
```

## 📝 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 🔄 核心组件设计

### DispatchSupervisor

**调度主管组件** - 负责协调和管理多Agent系统的执行流程

```python
class DispatchSupervisor:
    """调度主管 - 负责Agent任务的分配、执行监控和结果汇总"""
    
    def __init__(self):
        self.team_registry = {}  # 团队注册表
        self.agent_pool = {}     # Agent实例池
        self.intervention_service = InterventionService()
        
    def register_team(self, team_name: str, agent_list: List[str]):
        """注册分析团队"""
        self.team_registry[team_name] = agent_list
        
    def get_team_agents(self, team_name: str) -> List[Any]:
        """获取指定团队的Agent实例"""
        if team_name not in self.team_registry:
            raise ValueError(f"未注册的团队: {team_name}")
            
        agents = []
        for agent_name in self.team_registry[team_name]:
            if agent_name not in self.agent_pool:
                # 动态创建Agent实例
                agent_class = self._get_agent_class(agent_name)
                self.agent_pool[agent_name] = agent_class()
            agents.append(self.agent_pool[agent_name])
            
        return agents
        
    def execute_team_workflow(self, team_name: str, request: Dict[str,Any]) -> Agentrequest:
        """执行团队工作流"""
        agents = self.get_team_agents(team_name)
        
        # 检查是否需要人工中断
        intervention_result = self.intervention_service.check_intervention(request)
        if intervention_result:
            return intervention_result
            
        # 执行团队Agent序列
        for agent in agents:
            try:
                request = agent.run(request)
            except Exception as e:
                logger.error(f"Agent {agent.__class__.__name__} 执行失败: {str(e)}")
                request["status"] = "error"
                request["error"] = str(e)
                break
                
        return request
```

### LangGraph工具绑定

**完整的团队工具映射规范**

```python
# 企业画像团队工具
ENTERPRISE_PROFILE_TEAM_TOOLS = [
    financial_analysis_tool,
    enterprise_profile_tool, 
    credit_analysis_tool,
    counterparty_analysis_tool,
    customer_manager_profile_tool
]

# 蓝绿金融准入评估团队工具
BLUE_GREEN_ACCESS_TEAM_TOOLS = [
    blue_green_access_tool,
    enterprise_profile_tool,
    policy_lib_analysis_tool,
    credit_analysis_tool
]

# 蓝绿政策分析团队工具  
BLUE_GREEN_POLICY_TEAM_TOOLS = [
    policy_lib_analysis_tool,
    blue_green_policy_tool,
    case_lib_analysis_tool
]

# 蓝绿产品推荐团队工具
BLUE_GREEN_PRODUCT_TEAM_TOOLS = [
    product_analysis_tool,
    blue_green_product_tool,
    enterprise_profile_tool
]

# 蓝绿服务方案生成团队工具
BLUE_GREEN_SOLUTION_TEAM_TOOLS = [
    # 集成所有相关团队工具
    *ENTERPRISE_PROFILE_TEAM_TOOLS,
    *BLUE_GREEN_ACCESS_TEAM_TOOLS,
    *BLUE_GREEN_POLICY_TEAM_TOOLS,
    *BLUE_GREEN_PRODUCT_TEAM_TOOLS,
    blue_green_solution_tool
]

# 工具绑定配置
bound_model = model.bind_tools(
    analysis_tools,
    parallel_tool_calls=True
)
```

### 人工中断机制

```python
class InterventionService:
    """人工中断服务，处理三证信息补充"""
    
    async def handle_certificate_intervention(self, request: Dict[Str,Any]):
        """检查并处理三证信息中断"""
        if self._needs_certificates(request):
            # 触发人工中断
            raise Interrupt(
                value={
                    "required_data": {
                        "business_license": "营业执照信息",
                        "organization_code": "组织机构代码证信息",
                        "tax_registration": "税务登记证信息"
                    },
                    "current_data": state.results.get("enterprise_profile", {}),
                    "reason": "企业三证信息缺失，需要用户补充完整信息"
                },
                resume=lambda provided_data: self._resume_with_certificates(request, provided_data)
            )
    
    def _needs_certificates(self, request: Agentrequest) -> bool:
        """检查是否需要三证信息"""
        enterprise_data = request.results.get("enterprise_profile_agent", {})
        return not all([
            enterprise_data.get("business_license"),
            enterprise_data.get("organization_code"), 
            enterprise_data.get("tax_registration")
        ])
```

## 🔄 三模块架构设计规范

### 模块职责划分

#### dispatch_teams.py - 团队结构定义模块
```python
# 职责：定义所有分析团队的工具映射，提供团队工具获取函数
# 不包含任何状态管理或图构建逻辑

def get_team_tools(team_name: str) -> List[BaseTool]:
    """根据团队名称获取对应的工具列表（严格按照remind.md规范）"""
    pass

def get_tool_by_name(tool_name: str) -> BaseTool:
    """根据工具名称获取工具实例"""
    pass

def get_team_for_tool(tool_name: str) -> str:
    """根据工具名称获取对应的团队"""
    pass
```

#### tools_calling.py - 工具调用封装模块
```python
# 职责：封装工具调用逻辑，直接从LangGraph request中获取参数
# 工具接口统一接收完整的request对象

@tool
def financial_analysis_tool(request: Dict[str, Any]) -> Dict[str, Any]:
    """财务分析工具 - 从request中获取input和session_id"""
    input_text = request.get("input", "")
    session_id = request.get("session_id")
    # 调用API并返回结果
```

#### dispatch_graph_builder.py - 图构建模块
```python
# 职责：构建LangGraph工作流图，使用原生state对象
# 集成团队路由、工具调用和人工中断机制

def build_analysis_graph() -> Graph:
    """构建分析型Agent工作流图"""
    pass
```

### 状态管理规范
- **使用LangGraph原生request**：不再需要自定义AnalysisAgentrequest TypedDict
- **状态传递**：所有状态通过request参数传递，确保分布式环境一致性
- **状态结构**：
  ```python
  {
      "input": "用户输入",
      "session_id": "会话ID",
      "context": {},      # 临时上下文
      "results": {},      # 执行结果
      "metadata": {}      # 元数据
  }
  ```

### 工具接口规范
```python
# 新接口（目标格式）
@tool  
def financial_analysis_tool(request: Dict[str, Any]) -> Dict[str, Any]:
    # 从request中获取参数
    input_text = request.get("input", "")
    session_id = request.get("session_id")
```

### API接口同步化规范
```python
# 同步接口（目标格式）
@router.post("/financial_agent")
def financial_agent(input_data: Dict[str, Any]):
    # 同步代码...
    return result
```

### Agent无状态化规范
```python
# 无状态agent（目标格式）
class FinancialAgent:
    def run(self, request):
        # 所有状态通过request参数传递
        return processed_request
```
### 工具编写声明规范
```python
@tool(description="行业分析工具：由AI智能体调用的行业趋势..." #尽可能编写大模型理解工具使用规范
)
def xxx_tool(request: Dict[str, Any]) -> Dict[str, Any]:
  # 内部逻辑
```
### 工具绑定规范
```python
# 统一工具绑定方式
bound_model = model.bind_tools(
    team_tools,  # 使用标准化的团队工具
    parallel_tool_calls=True
)
```

## 🧠 大模型调用规范

### 调用方式规范
- **统一使用agent.invoke**：所有大模型调用必须使用agent.invoke方式，直接返回大模型输出内容
- **去除file_session依赖**：移除所有agent中的file_session相关代码，使用统一的request管理
- **增加温度和重试配置**：所有调用必须配置temperature和max_retries参数

### 调用示例
```python
# 标准调用格式
response = agent.invoke(
    {
        "input": request.get("input", ""),
        "context": request.get("context", {}),
        "session_id": request.get("session_id")
    },
    config={
        "configurable": {
            "session_id": request.get("session_id", "default")
        }
    },
    temperature=0.7,  # 设置温度参数
    max_retries=3     # 设置重试次数
)

# 直接返回大模型输出内容
return response.content
```

### 参数配置规范
- **temperature**: 默认0.7，范围0.1-1.0，控制输出的创造性
- **max_retries**: 默认3次，确保调用可靠性
- **timeout**: 默认30秒，避免长时间阻塞

### 错误处理规范
```python
try:
    response = agent.invoke(
        # ... 参数
        temperature=0.7,
        max_retries=3
    )
    return response.content
except Exception as e:
    logger.error(f"大模型调用失败: {str(e)}")
    return f"调用失败: {str(e)}"
```

## 📊 实施路线图

### 第一阶段：基础架构改造
1. **创建dispatch_teams.py**：定义团队工具映射
2. **创建tools_calling.py**：重构工具接口，使用request参数
3. **创建dispatch_graph_builder.py**：构建基于团队的工作流图
4. **移除自定义状态类型**：使用LangGraph原生state

### 第二阶段：Redis迁移和调用规范更新
1. **移除Redis依赖**：从所有agent中删除Redis会话存储代码
2. **文件系统存储实现**：基于get_store实现文件系统存储
3. **更新大模型调用方式**：去除file_session依赖，使用agent.invoke
4. **增加温度和重试配置**：统一配置调用参数

### 第三阶段：测试验证
1. **功能测试**：验证所有agent功能正常
2. **性能测试**：测试同步接口的性能表现
3. **调用稳定性测试**：验证重试机制的有效性

### 第四阶段：部署上线
1. **生产环境部署**：部署到生产环境
2. **监控告警**：设置系统监控和告警机制
3. **参数调优**：根据实际使用情况调整温度和重试参数
