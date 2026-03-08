# UV + Hatchling 迁移指南

## 概述

本文档详细说明如何将当前项目从 Python 官方 setuptools 构建模式迁移到现代化的 uv + hatchling 构建模式。

### 迁移目标
- **前端工具**: uv (Python 包管理器和依赖管理)
- **构建后端**: hatchling (现代化的构建系统)
- **依赖管理**: 统一使用 pyproject.toml
- **Python 版本**: 3.12.9 (Conda 环境)

### 为什么选择 uv + hatchling？
- **uv**: 超高速的依赖解析和包管理（比 pip 快 10-100 倍）
- **hatchling**: PyPA 推荐的现代构建后端，替代老旧的 setuptools
- **协同优势**: 前端高性能 + 后端现代化，最佳组合

### 重要说明
- **uv 虚拟环境**: uv 会自动管理虚拟环境，通过 `uv venv` 或 `uv sync` 创建
- **hatchling 安装**: 作为构建后端，hatchling 需要作为项目依赖安装

## 第一步：安装必要工具

### 1.1 安装 pipx (如果尚未安装)

```bash
# macOS (使用 Homebrew)
brew install pipx

# 或者使用 pip
python -m pip install --user pipx
python -m pipx ensurepath

# 验证安装
pipx --version
```

### 1.2 安装 uv

```bash
# 使用 pipx 安装 uv (推荐)
pipx install uv

# 或者使用 curl (官方推荐)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 验证安装
uv --version
```


## 第二步：配置 uv

```bash
# 设置项目使用 Python 3.12.9
uv python pin 3.12.9

# 配置 uv 全局设置
uv config set global.python-preference managed

# 验证配置
uv python list
```

### uv 虚拟环境管理说明

uv 提供多种创建虚拟环境的方式：

```bash
# 方法1：显式创建虚拟环境
uv venv

# 方法2：通过 sync 自动创建（当存在 pyproject.toml 时）
uv sync

# 方法3：通过 add 命令自动创建（首次添加依赖时）
uv add package-name

# 激活虚拟环境
uv shell

# 查看虚拟环境信息
uv info
```

## 第三步：项目迁移步骤

### 3.1 备份当前配置

```bash
# 备份现有文件
cp pyproject.toml pyproject.toml.backup
cp requirements.txt requirements.txt.backup
```

### 3.2 创建新的 pyproject.toml

```bash
# 备份并删除现有的 pyproject.toml
mv pyproject.toml pyproject.toml.backup

# 创建新的 pyproject.toml 配置
cat > pyproject.toml << 'EOF'
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "multi-agent-financial-assistant"
version = "0.1.0"
description = "Multi-agent financial assistant system"
readme = "README.md"
license = "MIT"
requires-python = ">=3.12"
authors = [
    {name = "Your Name", email = "your.email@example.com"},
]
keywords = ["ai", "finance", "multi-agent", "langchain"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.12",
]
dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=8.4.1",
    "pytest-asyncio>=1.1.0",
]

[tool.hatch.version]
path = "app/__init__.py"

[tool.hatch.build.targets.sdist]
include = [
    "/app",
    "/config",
    "/scripts",
]

[tool.hatch.build.targets.wheel]
packages = ["app"]
EOF
```

### 3.4 分析并迁移依赖

根据 requirements.txt 分析，识别出以下主要依赖分类：

#### 核心框架依赖
- **langchain** (0.3.27) - 核心 AI 框架
- **langgraph** (0.6.2) - 图形工作流
- **langsmith** (0.4.9) - 调试和监控
- **fastapi** (0.115.14) - Web 框架
- **uvicorn** (0.35.0) - ASGI 服务器

#### AI/ML 服务
- **openai** (1.98.0) - OpenAI API
- **anthropic** (0.60.0) - Anthropic API

#### 数据处理
- **pandas** (2.3.1) - 数据分析
- **numpy** (2.3.2) - 数值计算
- **pydantic** (2.10.1) - 数据验证

#### 数据库
- **sqlalchemy** (2.0.25) - ORM
- **psycopg2-binary** (2.9.9) - PostgreSQL 驱动
- **redis** (6.2.0) - Redis 客户端
- **pymilvus** (2.5.14) - 向量数据库

#### UI 框架
- **chainlit** (2.6.3) - 聊天界面
- **streamlit** (1.47.1) - Web 应用

#### 工具库
- **requests** (2.32.4) - HTTP 客户端
- **pyyaml** (6.0.2) - YAML 处理
- **python-dotenv** (1.1.1) - 环境变量

#### 测试工具
- **pytest** (8.4.1) - 测试框架
- **pytest-asyncio** (1.1.0) - 异步测试

### 3.3 初始化 uv 虚拟环境和添加依赖

```bash
# 方法1：明确创建虚拟环境
uv venv

# 方法2：或者通过 sync 自动创建（推荐）
uv sync

# 首先安装 hatchling（构建后端）
uv add "hatchling"

# 添加核心 AI 框架依赖
uv add "langchain==0.3.27" "langgraph==0.6.2" "langsmith==0.4.9"

# 添加 Web 框架依赖
uv add "fastapi==0.115.14" "uvicorn==0.35.0"

# 添加 AI 服务依赖
uv add "openai==1.98.0" "anthropic==0.60.0"

# 添加数据处理依赖
uv add "pandas==2.3.1" "numpy==2.3.2" "pydantic==2.10.1"

# 添加数据库依赖
uv add "sqlalchemy==2.0.25" "psycopg2-binary==2.9.9" "redis==6.2.0" "pymilvus==2.5.14"

# 添加 UI 框架依赖
uv add "chainlit==2.6.3" "streamlit==1.47.1"

# 添加工具库依赖
uv add "requests==2.32.4" "pyyaml==6.0.2" "python-dotenv==1.1.1" "loguru==0.7.3"

# 添加其他重要依赖
uv add "akshare==1.17.26" "celery==5.5.3" "beautifulsoup4==4.13.4" "lxml==6.0.0" "jieba==0.42.1" "mysql-connector-python==8.3.0"

# 添加开发依赖
uv add --dev "pytest==8.4.1" "pytest-asyncio==1.1.0"
```

## 第四步：验证和测试

### 4.1 验证环境

```bash
# 检查 Python 版本
uv python list

# 检查依赖树
uv tree

# 检查项目信息
uv info

# 验证 hatchling 构建配置
uv run python -c "import hatchling; print('Hatchling is working!')"
```

### 4.2 测试应用启动

```bash
# 使用 uv 运行应用
uv run python app/main.py

# 或者进入虚拟环境后运行
uv shell
python app/main.py
```

### 4.3 运行测试

```bash
# 使用 uv 运行测试
uv run pytest

# 运行特定测试
uv run pytest tests/ -v
```

### 4.4 测试构建功能

```bash
# 使用 hatchling 构建项目
uv build

# 检查构建结果
ls -la dist/
```

## 第五步：清理工作

### 5.1 更新 .gitignore

```bash
# 添加新的忽略规则
echo "
# UV 相关文件
.python-version
uv.lock
.venv/

# Hatchling 构建产物
dist/
build/
*.egg-info/

# 旧的配置文件备份
requirements.txt.backup
pyproject.toml.backup
" >> .gitignore
```

### 5.2 删除旧配置文件

```bash
# 删除或重命名旧文件
mv requirements.txt requirements.txt.old
# 或者直接删除
# rm requirements.txt
```

### 5.3 更新文档和脚本

更新项目中的安装说明和部署脚本，使其使用新的 uv + hatchling 工作流。

## 第六步：新的工作流程

### 6.1 日常开发命令

```bash
# 安装依赖
uv sync

# 添加新依赖
uv add package-name

# 添加开发依赖
uv add --dev package-name

# 运行应用
uv run python app/main.py

# 运行测试
uv run pytest

# 进入虚拟环境
uv shell
```

### 6.2 项目构建和发布

```bash
# 使用 hatchling 构建项目
uv build

# 发布到 PyPI (如需要)
uv publish

# 在其他环境安装项目
uv pip install dist/*.whl

# 或者从源代码安装
uv pip install -e .
```

## 项目结构说明

迁移后的项目结构将包含：

```
multi-agent-financial-assistant/
├── pyproject.toml          # 统一的项目配置文件
├── uv.lock                 # UV 锁定文件
├── .python-version         # Python 版本固定
├── .venv/                  # 虚拟环境目录
├── requirements.txt.old    # 备份的旧依赖文件
└── [其他项目文件...]
```

## 优势总结

### uv + hatchling 组合的优势
1. **超高性能**: uv 的依赖解析速度比 pip 快 10-100 倍
2. **现代化构建**: hatchling 是 PyPA 推荐的新一代构建后端
3. **简化工具链**: 前端 + 后端，避免过度复杂
4. **标准兼容**: 完全遵循 PEP 标准，兼容性更好
5. **配置简洁**: hatchling 的配置比 setuptools 更简洁明了
6. **更好的开发体验**: uv 的命令更直观，错误信息更清晰

## 注意事项

1. **团队协作**: 确保团队所有成员都安装了 uv
2. **CI/CD 更新**: 更新流水线以使用 uv 和 hatchling
3. **依赖兼容性**: 某些复杂依赖可能需要额外配置
4. **备份保留**: 保留 requirements.txt.old 作为备份，直到确认迁移成功
5. **版本控制**: 将 app/__init__.py 中的版本号与 pyproject.toml 保持同步

## 回滚计划

如果迁移过程中遇到问题，可以快速回滚：

```bash
# 恢复原始文件
mv pyproject.toml.backup pyproject.toml
mv requirements.txt.old requirements.txt

# 使用 pip 重新安装依赖
pip install -r requirements.txt
```
