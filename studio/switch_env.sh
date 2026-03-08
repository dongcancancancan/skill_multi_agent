#!/bin/bash
# LangGraph Studio 环境切换脚本
# 使用方法: ./switch_env.sh sit|uat

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ $# -eq 0 ]; then
    echo "错误: 请指定环境 (sit 或 uat)"
    echo "使用方法: ./switch_env.sh sit|uat"
    echo ""
    echo "示例:"
    echo "  ./switch_env.sh sit   # 切换到SIT环境"
    echo "  ./switch_env.sh uat   # 切换到UAT环境"
    exit 1
fi

ENV=$1

case $ENV in
    sit|SIT)
        ENV="sit"
        ;;
    uat|UAT)
        ENV="uat"
        ;;
    *)
        echo "错误: 不支持的环境 '$ENV'"
        echo "支持的环境: sit, uat"
        exit 1
        ;;
esac

SOURCE_FILE="$SCRIPT_DIR/.env.$ENV"
TARGET_FILE="$SCRIPT_DIR/.env"

if [ ! -f "$SOURCE_FILE" ]; then
    echo "错误: 环境配置文件不存在: $SOURCE_FILE"
    exit 1
fi

# 复制环境配置
cp "$SOURCE_FILE" "$TARGET_FILE"

echo "✅ 成功切换到 $ENV 环境"
echo ""
echo "💡 提示: 重启 LangGraph Studio 使配置生效"
