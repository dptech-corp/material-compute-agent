# Agent Framework

基于 CAMEL/Google adk 和 DP agent framework 实现的科学计算智能助手，专注于材料领域论文解析和 VASP 配置生成与计算。
本项目通过多智能体协作系统，实现了从材料科学论文中自动提取实验参数、生成 VASP 计算配置、提交计算任务到结果分析的全流程自动化。系统特别适用于高通量材料筛选、计算材料科学研究等场景，可以显著提高材料发现和优化的效率。

## 项目简介

本项目是一个智能科学计算系统，通过 AI 代理（Agents）自动化处理材料计算和 VASP 配置生成过程。系统主要功能包括：

- 自动解析材料结构和计算参数
- 智能生成 VASP 输入文件
- 结构验证和优化
- 计算结果分析和报告生成

## 技术架构

- 基于 CAMEL/Google-adk 多智能体框架
- 集成 science-agent-sdk 工具包
- 使用 pymatgen 进行材料结构处理
- 支持多种数据库查询（Materials Project, DP Database）

## 主要功能

1. VASP 配置生成
   - 自动生成 VASP 输入文件
   - 支持多种计算类型
   - 参数自动验证

2. 结构处理
   - CIF 文件解析
   - 结构优化
   - 空间群验证

3. 计算结果分析
   - vasprun.xml 解析
   - 能带结构分析
   - 自动报告生成

## 安装方法

1. 克隆项目并初始化子模块
```bash
git clone --recursive https://github.com/yourusername/bohr-science-agent-framework.git
cd bohr-science-agent-framework
```

2. 创建并激活虚拟环境
```bash
conda create -n bohr-agent python=3.11
conda activate bohr-agent
```

3. 安装依赖
```bash
pip install -e .
```

## 依赖说明

- Python >= 3.11
- pymatgen
- openai
- pandas >= 2.2.2
- camel-ai
- google-adk
- litellm

- 其他依赖见 setup.py

## 如何自定义Science任务

1. 定义Tools
    - 参考CalculationMCPServer.py 定义MCP端工具
    - 参考vasp_function.py 定义本地运行工具
2. 描述任务
    - 参考Agent prompt 写法，清晰简单描述任务流程与任务，启动human in the loop模块，与模型交互
    - 任务过程越详细，越清晰，任务越容易成功
3. 执行参考
    google-adk框架，Single agent framework
        material-compute-googleadk.ipynb
    camel-agent框架，Multiagent framework
        material-compute-camel.ipynb

```

