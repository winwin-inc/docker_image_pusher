#!/bin/bash
# 快速启动 Playwright 录制

echo "============================================================"
echo "Playwright 快速录制"
echo "============================================================"
echo ""

# 加载环境变量
if [ -f .env.beijing ]; then
    export $(cat .env.beijing | xargs)
    echo "✅ 环境变量已加载"
else
    echo "❌ 未找到 .env.beijing 文件"
    exit 1
fi

# 构建目标 URL
REGISTRY=${ALIYUN_REGISTRY:-registry.cn-beijing.aliyuncs.com}
NAMESPACE=${ALIYUN_NAME_SPACE:-winwin/tool}
REGION=$(echo $REGISTRY | sed 's/registry\.//' | sed 's/\.aliyuncs\.com//')
URL="https://cr.console.aliyun.com/repository/${REGION}/${NAMESPACE}/images"

echo "📹 将录制页面: $URL"
echo ""

# 检查登录状态
if [ -f ../data/aliyun_state.json ]; then
    echo "✅ 检测到登录状态,将使用已保存的状态"
    LOAD_STATE="--load-storage=../data/aliyun_state.json"
else
    echo "⚠️  未检测到登录状态,需要手动登录"
    LOAD_STATE=""
fi

echo ""
echo "📋 录制选项:"
echo "1. 带登录状态录制"
echo "2. 不带登录状态录制"
echo "3. 使用辅助工具"
echo ""
read -p "请选择 (1/2/3): " choice

case $choice in
    1)
        echo ""
        echo "启动录制(使用保存的登录状态)..."
        echo "💡 提示: 在浏览器中执行删除操作,然后关闭浏览器"
        echo ""
        uv run playwright codegen "$URL" $LOAD_STATE -o recorded_delete.py
        ;;
    2)
        echo ""
        echo "启动录制(手动登录)..."
        echo "💡 提示: 在浏览器中登录,然后执行删除操作,最后关闭浏览器"
        echo ""
        uv run playwright codegen "$URL" -o recorded_delete.py
        ;;
    3)
        echo ""
        echo "启动辅助工具..."
        echo ""
        PYTHONPATH=. python selector_helper.py
        ;;
    *)
        echo "无效选择"
        exit 1
        ;;
esac

echo ""
echo "============================================================"
echo "录制完成!"
echo "============================================================"
echo ""

if [ -f recorded_delete.py ]; then
    echo "📄 生成的代码: recorded_delete.py"
    echo ""
    echo "💡 下一步:"
    echo "1. 查看生成的代码: cat recorded_delete.py"
    echo "2. 运行代码: uv run python recorded_delete.py"
    echo "3. 提取选择器并更新到 browser_deleter.py"
fi
