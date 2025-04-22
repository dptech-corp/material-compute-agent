#!/bin/bash

# ========= 可选传入分支名参数 ============
BRANCH="${1:-main}"  # 默认为 main 分支，也可以传入 dev / feat/xxx

OS="$(uname)"
GITHUB_URL="https://github.com/dptech-corp/material-compute-agent.git"

echo "🚀 开始安装 Science Agent Framework（分支: $BRANCH）..."

# ========= 检查 Python 环境 ============
check_python() {
    if command -v python3 &>/dev/null; then
        echo "✅ 检测到 Python3"
        return 0
    elif command -v python &>/dev/null; then
        echo "✅ 检测到 Python"
        return 1
    else
        echo "❌ 未检测到 Python，请先安装 Python 3.8 或更高版本"
        exit 1
    fi
}

# ========= 安装依赖 ============
install_dependencies() {
    local python_cmd=$1
    echo "📦 安装依赖..."

    # 升级 pip
    $python_cmd -m pip install --upgrade pip

    echo "📦 安装基础包..."
    $python_cmd -m pip install --force-reinstall --no-cache-dir \
        numpy==2.0.0 \
        scipy==1.14.1 \
        pandas==2.2.2 \
        h5py==3.12.1

    echo "📦 安装其他依赖..."
    $python_cmd -m pip install \
        openai \
        docstring_parser \
        mcp \
        requests_oauthlib \
        pymatgen \
        PyPDF2 \
        tiktoken

    echo "📦 安装项目（分支: $BRANCH）..."
    $python_cmd -m pip install -e git+${GITHUB_URL}@${BRANCH}#egg=science-agent-framework
}

# ========= 主安装流程 ============
main() {
    if [ "$OS" == "Linux" ] || [ "$OS" == "Darwin" ]; then
        echo "💻 检测到操作系统: $OS"
        if check_python; then
            install_dependencies "python3"
        else
            install_dependencies "python"
        fi
    elif [ "$OS" == "Windows_NT" ] || [[ "$OS" == MINGW* ]] || [[ "$OS" == CYGWIN* ]]; then
        echo "💻 检测到操作系统: Windows"
        install_dependencies "python"
    else
        echo "❌ 不支持的操作系统: $OS"
        exit 1
    fi
}

# ========= 运行安装 ============
main

# ========= 验证结果 ============
if [ $? -eq 0 ]; then
    echo ""
    echo "✨ Science Agent Framework 安装成功！"
    echo "📚 使用方法："
    echo "   1. 在 Python 中导入: from science_agent_framework import *"
    echo "   2. 查看示例: examples/vasp_experiment.ipynb"
else
    echo "❌ 安装过程中出现错误，请检查错误信息"
    exit 1
fi