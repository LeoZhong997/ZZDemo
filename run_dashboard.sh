#!/bin/bash

# Streamlit 外卖数据看板启动脚本
# 创建日期: 2025-02-10

echo "============================================================"
echo "🍔 启动外卖数据看板"
echo "============================================================"
echo ""

# 检查 Streamlit 是否安装
if ! python3 -c "import streamlit" 2>/dev/null; then
    echo "⚠️  Streamlit 未安装，正在安装..."
    pip install -q streamlit
    echo "✅ Streamlit 安装完成"
fi

echo "🚀 启动 Streamlit 应用..."
echo ""
echo "浏览器将自动打开看板页面"
echo "按 Ctrl+C 停止应用"
echo ""

# 启动 Streamlit
streamlit run app.py --browser.gatherUsageStats=false
