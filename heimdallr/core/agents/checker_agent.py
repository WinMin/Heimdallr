from typing import Dict, Any

from heimdallr.core.agents.base_agent import BaseAgent
from heimdallr.core.llm_connector import LLMConnector
from heimdallr.core.prompts import CHECKER_SYSTEM_PROMPT

class CheckerAgent(BaseAgent):
    """
    Checker Agent 负责:
    - 接收 Manager 汇总的 Auditor 发现和分析逻辑
    - 复核整个审计流程和结论
    - 查找误报和漏报
    - 提供反馈给 Manager
    """
    def __init__(self, llm_connector: LLMConnector, model_name: str):
        super().__init__(llm_connector, model_name, CHECKER_SYSTEM_PROMPT)

    async def process_task(self, task_description: str, context: Dict[str, Any] = None) -> str:
        """
        Checker Agent 处理校验任务。

        参数:
            task_description (str): 通常是 Manager 请求校验的指令。
            context (Dict[str, Any], optional):
                包含原始代码 (original_code), 文件路径 (file_path),
                Auditor 的发现摘要 (auditor_findings_summary),
                以及 Manager 的初步分析 (manager_initial_analysis)。

        返回:
            str: 包含校验反馈的文本。
        """
        self.clear_history()

        original_code_info = f"原始代码 (文件: {context.get('file_path', 'N/A')}):\n```\n{context.get('original_code', '[代码未提供]')}\n```\n" if context else ""
        manager_analysis_info = f"Manager 的初步分析:\n{context.get('manager_initial_analysis', 'N/A')}\n" if context else ""
        auditor_summary_info = f"Auditor Agents 的综合发现:\n{context.get('auditor_findings_summary', 'N/A')}\n" if context else ""

        prompt = (
            f"{task_description}\n\n"
            f"以下是相关的审计材料，请仔细复核：\n"
            f"1. Manager Agent 的初步分析和任务分解逻辑:\n{manager_analysis_info}\n"
            f"2. Auditor Agents 提交的审计发现摘要:\n{auditor_summary_info}\n"
            f"3. 相关的原始代码片段 (如果适用，通常 Manager 的分析和 Auditor 的报告中会引用):\n{original_code_info}\n"
            f"\n你的任务是批判性地评估以上信息。请指出：\n"
            f"- 是否存在明显的误报 (False Positives)？请说明理由。\n"
            f"- 是否有 Auditor 可能遗漏的潜在漏洞 (False Negatives) 或风险点？特别注意不同代码部分交互可能产生的问题。\n"
            f"- Auditor 的分析逻辑是否合理、一致、充分？\n"
            f"- Manager 的任务分解和整体分析是否恰当？\n"
            f"- 对于发现的漏洞，其风险评估是否准确？\n"
            f"请提供具体的、可操作的反馈，帮助 Manager 提高最终审计报告的质量。"
        )
        
        print(f"CHECKER ({self.model_name}): 正在校验审计结果...")

        feedback = self.chat(prompt, context=None, temperature=0.3, max_tokens=2048) # 上下文已在 prompt 中构建

        if not feedback:
            feedback = "Checker Agent 未能从 LLM 生成校验反馈。"
            print(f"CHECKER ({self.model_name}): 未能生成反馈。")
        else:
            print(f"CHECKER ({self.model_name}): 校验完成。")

        return feedback 