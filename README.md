# Paper-Reproduce-Agent

基于CAMEL框架的论文复现智能助手，专注于VASP计算的自动化配置生成。

## 项目简介

本项目是一个智能论文复现系统，通过AI代理（Agents）自动化处理VASP计算的配置生成过程。系统包含两个主要角色：
- 博士生代理：负责阅读论文并生成VASP配置
- 导师代理：负责验证配置的正确性

## 功能特点

- 自动解析PDF格式的论文
- 智能提取实验参数和配置信息
- 自动生成VASP输入文件（POSCAR和配置文件）
- 实时验证配置的正确性
- 支持多轮交互式修正


## 使用方法

1. 准备论文PDF文件
2. 运行主程序
```bash
python paper_agent_workforce.py
```

## 项目结构

```
.
├── paper_agent_workforce.py   # 主程序文件
├── vasp_function.py          # VASP相关功能函数
├── prompt/                   # 提示词模板
│   ├── paper_prompt.txt      # 博士生角色提示词
│   └── check_prompt.txt      # 导师角色提示词
├── VASPTemplates/            # VASP模板文件
└── CALC/                     # 计算结果目录
```

## 核心功能

1. PDF解析（`read_pdf`）
   - 自动提取PDF文本内容
   - 按页面组织信息

2. VASP配置生成（`generate_vasp_input`）
   - 生成POSCAR文件
   - 生成配置文件
   - 参数自动验证

3. 配置验证（`generate_vasp_config`）
   - 检查参数合理性
   - 验证格式正确性

