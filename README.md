# Bohr Science Agent Framework

基于 CAMEL 框架的科学计算智能助手，专注于材料计算和 VASP 配置的自动化生成。

## 项目简介

本项目是一个智能科学计算系统，通过 AI 代理（Agents）自动化处理材料计算和 VASP 配置生成过程。系统主要功能包括：

- 自动解析材料结构和计算参数
- 智能生成 VASP 输入文件
- 结构验证和优化
- 计算结果分析和报告生成

## 技术架构

- 基于 CAMEL 多智能体框架
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
conda create -n bohr-agent python=3.8
conda activate bohr-agent
```

3. 安装依赖
```bash
pip install -e .
```

```

## 项目结构

```
.
├── vasp_function.py     # VASP 相关功能函数
├── server/              # 服务器端代码
├── camel/              # CAMEL 框架（子模块）
├── science-agent-sdk/  # SDK 工具包（子模块）
├── VASPTemplates/      # VASP 模板文件
└── prompt/            # 提示词模板
```
