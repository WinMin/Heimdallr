from typing import Dict, Any

from heimdallr.core.agents.base_agent import BaseAgent
from heimdallr.core.llm_connector import LLMConnector
from heimdallr.core.prompts import AUDITOR_SYSTEM_PROMPT

class AuditorAgent(BaseAgent):
    """
    Auditor Agent 负责:
    - 接收 Manager 分配的代码片段和上下文
    - 深入分析代码，查找具体漏洞
    - 报告发现给 Manager
    """
    def __init__(self, llm_connector: LLMConnector, model_name: str):
        super().__init__(llm_connector, model_name, AUDITOR_SYSTEM_PROMPT)

    async def process_task(self, code_snippet: str, context: Dict[str, Any] = None) -> str:
        """
        Auditor Agent 处理单个代码审计任务。

        参数:
            code_snippet (str): 要审计的代码片段。
            context (Dict[str, Any], optional):
                包含任务重点 (task_focus), 目标漏洞类型 (target_vulnerabilities),
                文件路径 (file_path), 和 Manager 的初步分析 (manager_preliminary_analysis) 等。

        返回:
            str: 包含审计发现的文本报告。
        """
        self.clear_history() # 每个独立审计任务开始前，可以考虑清空或选择性保留历史

        file_path_info = f"代码片段来源文件: {context.get('file_path', 'N/A')}\n" if context and context.get('file_path') else ""
        task_focus_info = f"Manager 指示的审计重点: {context.get('task_focus', 'N/A')}\n" if context and context.get('task_focus') else ""
        vulnerabilities_info = f"Manager 要求特别关注的漏洞类型: {', '.join(context.get('target_vulnerabilities', ['N/A']))}\n" if context and context.get('target_vulnerabilities') else ""
        manager_analysis_info = f"Manager 的初步分析摘要:\n{context.get('manager_preliminary_analysis', 'N/A')}\n" if context and context.get('manager_preliminary_analysis') else ""

        prompt = (
            f"{file_path_info}"
            f"{task_focus_info}"
            f"{vulnerabilities_info}"
            f"{manager_analysis_info}"
            f"\n请仔细审计以下代码片段:\n```\n{code_snippet}\n```\n"
            f"请详细报告你发现的任何潜在安全漏洞，包括漏洞类型、具体位置（如行号，如果适用）、"
            f"触发条件、潜在影响和可能的利用方式。"
            f"如果没有发现明显漏洞，请明确说明，并简要解释原因。"
            f"请确保你的分析是基于提供的上下文信息，并且尽可能深入和具体。"
        )

        print(f"AUDITOR ({self.model_name}): 正在分析代码片段... Focus: {context.get('task_focus', 'N/A') if context else 'N/A'}")
        
        # 为了模拟异步行为，实际的 LLM 调用已经是阻塞的
        # 在一个真正的异步应用中，llm_connector.invoke_llm 也会是 awaitable
        # 这里我们保持 process_task 为 async，以便将来可以集成真正的异步I/O
        
        report = self.chat(prompt, context=None, temperature=0.4, max_tokens=2048) # 上下文已在 prompt 中

        if not report:
            report = "Auditor Agent 未能从 LLM 生成审计报告。这可能是一个网络问题或 LLM 服务端错误。"
            print(f"AUDITOR ({self.model_name}):未能生成报告。")
        else:
            print(f"AUDITOR ({self.model_name}): 分析完成。")
            
        return report 