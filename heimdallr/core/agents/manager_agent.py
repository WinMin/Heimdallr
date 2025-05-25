from typing import Dict, Any, List
import json # 用于解析 LLM 可能返回的 JSON 格式的子任务

from heimdallr.core.agents.base_agent import BaseAgent
from heimdallr.core.llm_connector import LLMConnector
from heimdallr.core.prompts import MANAGER_SYSTEM_PROMPT
from heimdallr.core.agents.auditor_agent import AuditorAgent # 稍后会创建
from heimdallr.core.agents.checker_agent import CheckerAgent # 稍后会创建

class ManagerAgent(BaseAgent):
    """
    Manager Agent 负责:
    - 接收用户输入 (代码/文件路径)
    - 宏观理解代码，分解任务
    - 将任务分配给 Auditor Agents
    - 收集 Auditor Agents 的结果
    - 请求 Checker Agent 校验
    - 生成最终报告
    """
    def __init__(self, llm_connector: LLMConnector, model_name: str, auditor_model_name: str, checker_model_name: str):
        super().__init__(llm_connector, model_name, MANAGER_SYSTEM_PROMPT)
        self.auditors: List[AuditorAgent] = []
        self.checker: CheckerAgent = None
        self.auditor_model_name = auditor_model_name
        self.checker_model_name = checker_model_name
        # 在实际使用中，可能需要动态创建或配置 Auditor
        # 这里只是一个基本框架

    def _initialize_auditors(self, num_auditors: int = 1):
        """根据需要初始化 Auditor Agents"""
        self.auditors = [
            AuditorAgent(self.llm_connector, model_name=self.auditor_model_name)
            for _ in range(num_auditors)
        ]

    def _initialize_checker(self):
        """初始化 Checker Agent"""
        self.checker = CheckerAgent(self.llm_connector, model_name=self.checker_model_name)

    async def process_task(self, code_content: str, file_path: str = None) -> Dict[str, Any]:
        """
        Manager Agent 的核心处理流程。

        参数:
            code_content (str): 要分析的源代码内容。
            file_path (str, optional): 源代码的文件路径，用于上下文。

        返回:
            Dict[str, Any]: 包含审计结果的报告。
        """
        self.clear_history() # 开始新任务前清空历史
        self._initialize_auditors(num_auditors=1) # 简化：暂时只用一个 auditor
        self._initialize_checker()

        initial_analysis_prompt = (
            f"请分析以下位于 '{file_path if file_path else 'unknown file'}' 的代码。\n"
            f"首先，对代码的核心功能进行概述。\n"
            f"然后，识别出需要重点审计的关键代码区域或函数，并说明为什么这些区域是关键的。\n"
            f"最后，请将审计任务分解成1到3个具体的子任务，说明每个子任务要审计的代码片段（可以直接引用或描述定位方式），以及需要 Auditor Agent 特别关注的潜在漏洞类型。\n"
            f"以JSON格式返回子任务列表，每个子任务包含 'code_snippet' (字符串，相关代码), 'focus' (字符串，审计关注点), 'target_vulnerabilities' (列表字符串，如 ['Buffer Overflow', 'SQL Injection'])。 \n"
            f"代码如下:\n```\n{code_content}\n```"
        )

        print("MANAGER: 正在进行初步分析和任务分解...")
        llm_response_str = self.chat(initial_analysis_prompt, max_tokens=3072)

        if not llm_response_str:
            return {"error": "Manager Agent 未能从 LLM 获取初步分析结果。"}

        print(f"MANAGER: 初步分析和任务分解结果:\n{llm_response_str}")

        # 解析 LLM 的响应以提取子任务
        # 这部分比较脆弱，LLM 可能不总是完美遵循格式
        try:
            # 尝试找到 JSON 部分
            json_start = llm_response_str.find('```json')
            json_end = llm_response_str.rfind('```')
            sub_tasks_json_str = ""
            if json_start != -1 and json_end != -1 and json_start < json_end:
                sub_tasks_json_str = llm_response_str[json_start + 7 : json_end].strip()
            else: # 如果没有 ```json ... ```, 尝试直接解析整个字符串或特定部分
                # 这是一个简化的回退，实际中可能需要更复杂的解析逻辑
                if 'sub_tasks' in llm_response_str.lower() or 'subtasks' in llm_response_str.lower():
                     # 尝试从包含特定关键词的字典结构中提取
                    potential_json_part = llm_response_str[llm_response_str.find('{'):llm_response_str.rfind('}')+1]
                    if potential_json_part:
                        sub_tasks_json_str = potential_json_part
                    else: # 最后尝试，看整个回复是否就是json列表
                        if llm_response_str.strip().startswith('[') and llm_response_str.strip().endswith(']'):
                            sub_tasks_json_str = llm_response_str.strip()
            
            if not sub_tasks_json_str:
                 print("MANAGER: 未能在LLM响应中找到有效的JSON子任务列表。将尝试把整个响应作为任务描述。")
                 # 如果无法解析 JSON，可以将整个回复视为一个大的审计任务描述
                 # 或者提示用户/开发者需要LLM返回更精确的格式
                 sub_tasks = [{
                     "code_snippet": code_content, # 整个代码
                     "focus": "全面审计以下代码，识别潜在安全漏洞。",
                     "target_vulnerabilities": ["All common web vulnerabilities", "Logic errors"],
                     "original_llm_response_for_auditor": llm_response_str # 传递原始响应给Auditor参考
                 }]
            else:
                parsed_response = json.loads(sub_tasks_json_str)
                # 假设 LLM 返回的 JSON 中有一个名为 'sub_tasks' 或 'subtasks' 的列表
                # 或者直接返回一个列表
                if isinstance(parsed_response, list):
                    sub_tasks = parsed_response
                elif isinstance(parsed_response, dict):
                    sub_tasks = parsed_response.get('sub_tasks', parsed_response.get('subtasks', []))
                else:
                    sub_tasks = [] # 或者抛出错误
                
                if not sub_tasks:
                    print("MANAGER: 解析出的 JSON 不包含有效的子任务列表。将使用默认任务。")
                    # Fallback if JSON is present but not in the expected structure
                    sub_tasks = [{
                        "code_snippet": code_content, # 整个代码
                        "focus": "LLM未能正确分解任务，请全面审计以下代码。",
                        "target_vulnerabilities": ["All common web vulnerabilities", "Logic errors"],
                        "original_llm_response_for_auditor": llm_response_str
                    }]

        except json.JSONDecodeError as e:
            print(f"MANAGER: 解析 LLM 的子任务响应失败: {e}。将把整个代码作为一个任务。")
            sub_tasks = [{
                "code_snippet": code_content,
                "focus": "全面审计以下代码，由于任务分解失败，请特别关注所有潜在安全漏洞。",
                "target_vulnerabilities": ["All"],
                "original_llm_response_for_auditor": llm_response_str
            }]
        
        if not self.auditors:
            self._initialize_auditors(1) # 确保至少有一个auditor
        
        auditor_reports = []
        # 简化：目前只使用第一个 auditor，未来可以扩展到多个 auditors
        # 例如，轮询或根据任务类型选择 auditor
        current_auditor_index = 0 
        for i, task_data in enumerate(sub_tasks):
            print(f"MANAGER: 将任务 {i+1}/{len(sub_tasks)} 分配给 Auditor Agent...")
            auditor = self.auditors[current_auditor_index % len(self.auditors)] # 轮询使用Auditor
            
            # 确保 task_data 包含必要字段，如果 LLM 未提供，则使用默认值
            code_to_audit = task_data.get('code_snippet', code_content) # 如果没有代码片段，就用全部代码
            focus = task_data.get('focus', '未知关注点，请全面审计提供的代码片段。')
            target_vulnerabilities = task_data.get('target_vulnerabilities', ['General Security Review'])
            original_llm_context = task_data.get('original_llm_response_for_auditor', '')

            auditor_context = {
                "file_path": file_path,
                "task_focus": focus,
                "target_vulnerabilities": target_vulnerabilities,
                "manager_preliminary_analysis": original_llm_context if original_llm_context else llm_response_str
            }
            auditor_report = await auditor.process_task(code_to_audit, auditor_context)
            auditor_reports.append(auditor_report)
            print(f"MANAGER:收到 Auditor Agent 的报告:\n{auditor_report}")

        # 汇总 Auditor 报告
        print("MANAGER: 正在汇总 Auditor Agents 的报告...")
        combined_auditor_findings = "\n\n-- Auditor Reports Summary --\n"
        for i, report in enumerate(auditor_reports):
            combined_auditor_findings += f"\nReport from Auditor {i+1}:\n{report}\n"
        combined_auditor_findings += "\n-- End of Auditor Reports Summary --\n"

        print(f"MANAGER: 合并后的审计员发现:\n{combined_auditor_findings}")

        # 请求 Checker Agent 校验
        print("MANAGER: 正在请求 Checker Agent 进行校验...")
        checker_context = {
            "original_code": code_content,
            "file_path": file_path,
            "auditor_findings_summary": combined_auditor_findings,
            "manager_initial_analysis": llm_response_str
        }
        checker_feedback = await self.checker.process_task("请复核并验证以下代码审计发现和分析逻辑。", checker_context)
        print(f"MANAGER: 收到 Checker Agent 的反馈:\n{checker_feedback}")

        # 生成最终报告
        final_report = self._generate_final_report(code_content, file_path, llm_response_str, combined_auditor_findings, checker_feedback)
        print("MANAGER: 最终审计报告已生成。")
        return final_report

    def _generate_final_report(self, code, file_path, manager_analysis, auditor_summary, checker_feedback) -> Dict[str, Any]:
        """根据所有输入生成最终报告。"""
        report = {
            "file_path": file_path or "N/A",
            "summary": "Heimdallr 代码审计报告",
            "manager_preliminary_analysis": manager_analysis,
            "auditors_combined_findings": auditor_summary,
            "checker_validation_feedback": checker_feedback,
            "final_conclusion": "(Heimdallr 最终结论将基于以上所有信息综合判断)", # LLM 可以填充这部分
            "recommendations": "(Heimdallr 修复建议将在此处列出)" # LLM 可以填充这部分
        }
        
        # 可以再让 Manager LLM 基于所有信息生成一个更精炼的结论和建议
        final_summary_prompt = (
            f"基于以下代码审计的各个阶段的输出，请生成一份最终的总结陈述和具体的修复建议。\n"
            f"代码路径: {file_path if file_path else 'N/A'}\n"
            f"你的初步分析和任务分解:\n{manager_analysis}\n\n"
            f"Auditor Agents 的综合发现:\n{auditor_summary}\n\n"
            f"Checker Agent 的校验反馈:\n{checker_feedback}\n\n"
            f"请提供一个'final_conclusion'，总结代码的整体安全状况和主要风险点。"
            f"然后提供一个'recommendations'列表，针对每个关键发现给出具体的、可操作的修复建议。"
            f"以JSON对象格式返回，包含 final_conclusion (字符串) 和 recommendations (字符串列表) 两个键。"
        )
        
        print("MANAGER: 正在生成最终结论和建议...")
        final_llm_output_str = self.chat(final_summary_prompt, temperature=0.6, max_tokens=2048)
        
        if final_llm_output_str:
            print(f"MANAGER: LLM生成的最终结论和建议部分:\n{final_llm_output_str}")
            try:
                final_data = json.loads(final_llm_output_str)
                report["final_conclusion"] = final_data.get("final_conclusion", report["final_conclusion"])
                report["recommendations"] = final_data.get("recommendations", report["recommendations"])
            except json.JSONDecodeError:
                print(f"MANAGER: 解析最终结论JSON失败。将原始LLM输出作为结论。")
                # 如果解析失败，直接用原始文本，或者只更新一部分
                report["final_conclusion"] = f"LLM Raw Output (failed to parse JSON): {final_llm_output_str}"
                # report["recommendations"] could also be set similarly or retain default
        else:
            print("MANAGER: 未能从LLM获取最终结论和建议。")
            
        return report

    def _format_report_to_markdown(self, report_data: Dict[str, Any]) -> str:
        """将报告字典转换为 Markdown 格式的字符串。"""
        md = []
        md.append(f"# Heimdallr 代码审计报告")
        md.append(f"\n**文件路径:** `{report_data.get('file_path', 'N/A')}`")
        
        md.append(f"\n## 1. Manager Agent 初步分析与任务分解")
        md.append(f"\n```text\n{report_data.get('manager_preliminary_analysis', '未提供')}\n```")
        
        md.append(f"\n## 2. Auditor Agents 综合发现")
        # auditor_summary 已经是格式化好的字符串，包含多个报告
        auditor_findings = report_data.get('auditors_combined_findings', '未提供')
        # 为了更好的 Markdown 显示，我们将其放入一个代码块，或者直接附加
        # 如果 auditor_findings 内部已经有 Markdown 或适合直接渲染的格式，则直接添加
        # 否则，放入 text 代码块以保持原始格式
        if "\nReport from Auditor" in auditor_findings: # 假设这是我们之前添加的分隔符
             md.append(f"\n{auditor_findings}") # 直接添加，因为它可能包含子标题等
        else:
            md.append(f"\n```text\n{auditor_findings}\n```")

        md.append(f"\n## 3. Checker Agent 校验反馈")
        md.append(f"\n```text\n{report_data.get('checker_validation_feedback', '未提供')}\n```")
        
        md.append(f"\n## 4. 最终审计结论")
        conclusion = report_data.get('final_conclusion', '未提供')
        # 如果结论是简单字符串，可以直接放，如果是复杂结构或包含换行，代码块更好
        if isinstance(conclusion, str) and '\n' in conclusion:
            md.append(f"\n```text\n{conclusion}\n```")
        else:
            md.append(f"\n{conclusion}")

        md.append(f"\n## 5. 修复建议")
        recommendations = report_data.get('recommendations', '未提供')
        if isinstance(recommendations, list):
            if recommendations:
                for i, rec in enumerate(recommendations):
                    md.append(f"- {rec}")
            else:
                md.append("无具体修复建议。")
        elif isinstance(recommendations, str):
             # 如果建议是单个字符串，但可能包含换行或列表标记，尝试智能处理
            if recommendations.strip().startswith("-") or "\n-" in recommendations or "\n*" in recommendations :
                 md.append(f"\n{recommendations}") # 假设它已经是markdown列表格式
            elif '\n' in recommendations:
                 md.append(f"\n```text\n{recommendations}\n```")
            else:
                md.append(f"\n{recommendations}")
        else:
            md.append(f"\n{str(recommendations)}")
            
        return "\n".join(md)

# 注意: AuditorAgent 和 CheckerAgent 此时还未定义。
# 需要先创建这些文件和类，才能完整运行。 