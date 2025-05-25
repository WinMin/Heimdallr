# Heimdallr - LLM 代码审计工具

Heimdallr 是一个利用大型语言模型（LLM）进行代码审计的工具。它通过多 Agent 协作（Manager, Auditor, Checker）来分析代码，发现潜在漏洞。

## 特性

- 支持 OpenAI 兼容的 LLM API
- 可自定义 API Key 和 Base URL
- 多 Agent 架构，实现任务分解与协作审计
- （计划中）可扩展的工具集支持，例如与 LSP 集成的代码阅读器

## 安装

首先，请确保您已安装 Python 3.8 或更高版本。

1.  克隆仓库 (如果您正在从 git 获取):
    ```bash
    git clone <repository_url>
    cd Heimdallr
    ```
2.  创建并激活虚拟环境 (推荐):
    ```bash
    python -m venv venv
    source venv/bin/activate  # macOS/Linux
    # venv\Scripts\activate    # Windows
    ```
3.  安装依赖:
    ```bash
    pip install -r requirements.txt
    ```

## 快速开始

（详细使用说明请参见 `docs/usage.md`）

```bash
export OPENAI_API_KEY="YOUR_API_KEY"
# export OPENAI_BASE_URL="YOUR_CUSTOM_BASE_URL" # 如果需要，取消注释并设置

python -m heimdallr.main --file examples/sample_code_to_audit.py
```

## 项目结构

```
Heimdallr/
├── heimdallr/              # 主要的 Python 包
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── llm_connector.py    # LLM API 通信
│   │   ├── agents/             # Agent 实现
│   │   │   ├── __init__.py
│   │   │   ├── base_agent.py
│   │   │   ├── manager_agent.py
│   │   │   ├── auditor_agent.py
│   │   │   └── checker_agent.py
│   │   └── prompts.py          # Prompt 模板
│   ├── tools/                  # 工具集
│   │   ├── __init__.py
│   │   └── code_reader.py      # 示例代码阅读器
│   └── main.py                 # 命令行入口
├── docs/
│   └── usage.md                # 使用教程
├── examples/
│   └── sample_code_to_audit.py # 示例待审计代码
├── README.md                   # 本文件
└── requirements.txt            # Python 依赖
```

## Agent 职责

1.  **Manager Agent**:
    *   用户的交互点，接收分析入口（如目标文件或函数）。
    *   从宏观层面理解任务，例如，判断函数核心功能，识别潜在的关键代码段。
    *   进行任务分解与分派，将不同的代码片段连同必要的上下文信息分发给多个 Auditor。
    *   汇总审计结果，并请求 Checker 对整个逻辑链条进行复核与验证。
    *   整合信息并输出最终审计报告。

2.  **Auditor Agent**:
    *   专注于分析来自 Manager 分配的、通常较为短小的代码片段。
    *   结合上下文信息，深入挖掘代码细节中可能存在的漏洞，如 Buffer Overflow, Use After Free 等。

3.  **Checker Agent**:
    *   在 Manager 汇总审计结果并输出最终结论前，对整个逻辑链条进行复核与验证，查漏补缺。

## 工具集

各 Agent 在执行任务过程中，均可按需调用预设的工具集。工具的使用时机和方式皆由 Agent 自主决策。后端工具集的有效运行依赖于对目标项目和环境的适配，例如，源码阅读器 (Code Reader) 的变量定位功能可能依赖于后端语言服务协议 (LSP) 所建立的源码索引功能。

## 贡献

欢迎贡献！请查阅 `CONTRIBUTING.md` (待创建) 了解更多信息。

## 许可证

本项目采用 MIT 许可证。 