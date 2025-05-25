import argparse
import os
import asyncio
import json
from dotenv import load_dotenv
from openai import OpenAI
from heimdallr.core.llm_connector import LLMConnector
from heimdallr.core.agents import ManagerAgent

# 尝试加载 .env 文件 (如果存在)
load_dotenv()

DEFAULT_MANAGER_MODEL = "gemini-1.5-flash-latest" # 例如 "gemini-1.5-flash-latest", "gemini-2.0-flash", "gpt-4o", "gpt-3.5-turbo"
DEFAULT_AUDITOR_MODEL = "gemini-1.5-flash-latest" # 例如 "gemini-1.5-flash-latest", "gemini-2.0-flash", "gpt-4", "gpt-3.5-turbo"
DEFAULT_CHECKER_MODEL = "gemini-1.5-pro-latest"   # 例如 "gemini-1.5-pro-latest", "gpt-4-turbo", "gpt-4"

async def run_audit(file_path: str, 
                  api_key: str = None, 
                  base_url: str = None, 
                  manager_model: str = None,
                  auditor_model: str = None,
                  checker_model: str = None,
                  debug: bool = False):
    """
    运行代码审计流程。
    """
    # 获取环境变量或使用默认值
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    base_url = base_url or os.getenv("OPENAI_BASE_URL")
    manager_model = manager_model or os.getenv("HEIMDALLR_MANAGER_MODEL", DEFAULT_MANAGER_MODEL)
    auditor_model = auditor_model or os.getenv("HEIMDALLR_AUDITOR_MODEL", DEFAULT_AUDITOR_MODEL)
    checker_model = checker_model or os.getenv("HEIMDALLR_CHECKER_MODEL", DEFAULT_CHECKER_MODEL)

    if debug:
        print("*** DEBUG MODE ENABLED ***")
        if api_key:
            print(f"DEBUG: API Key (Full String): {api_key}")
        else:
            print("DEBUG: API Key is not set.")
        print("************************")
        
    if not api_key:
        print("错误: OpenAI API 密钥未找到。请设置 OPENAI_API_KEY 环境变量或通过 --api-key 参数提供。")
        return

    print(f"--- Heimdallr 代码审计开始 ---")
    print(f"目标文件: {file_path}")
    print(f"Manager Model: {manager_model}")
    print(f"Auditor Model: {auditor_model}")
    print(f"Checker Model: {checker_model}")
    if base_url:
        print(f"API Base URL: {base_url}")
    print("--------------------------------")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code_content = f.read()
    except FileNotFoundError:
        print(f"错误: 文件 '{file_path}' 未找到。")
        return
    except Exception as e:
        print(f"错误: 读取文件 '{file_path}' 时发生错误: {e}")
        return

    try:
        llm_connector = LLMConnector(api_key=api_key, base_url=base_url)
        manager = ManagerAgent(
            llm_connector=llm_connector, 
            model_name=manager_model,
            auditor_model_name=auditor_model,
            checker_model_name=checker_model
        )

        # 运行 Manager Agent 的处理任务
        report = await manager.process_task(code_content, file_path=file_path)

        print("\n--- Heimdallr 最终审计报告 ---")
        # 使用 json.dumps 美化输出
        print(json.dumps(report, indent=4, ensure_ascii=False))
        
        # 保存 JSON 报告
        report_json_filename = f"{os.path.splitext(os.path.basename(file_path))[0]}_audit_report.json"
        with open(report_json_filename, 'w', encoding='utf-8') as rf_json:
            json.dump(report, rf_json, indent=4, ensure_ascii=False)
        print(f"\nJSON 报告已保存到: {report_json_filename}")

        # 生成并保存 Markdown 报告
        if report and not report.get("error"):
            markdown_report_str = manager._format_report_to_markdown(report)
            report_md_filename = f"{os.path.splitext(os.path.basename(file_path))[0]}_audit_report.md"
            with open(report_md_filename, 'w', encoding='utf-8') as rf_md:
                rf_md.write(markdown_report_str)
            print(f"Markdown 报告已保存到: {report_md_filename}")
        elif report.get("error"):
            print(f"由于处理过程中出现错误，Markdown 报告未生成: {report.get('error')}")

    except ValueError as ve:
        print(f"初始化错误: {ve}")
    except Exception as e:
        print(f"执行审计过程中发生意外错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("--- Heimdallr 代码审计结束 ---")

def main():
    parser = argparse.ArgumentParser(description="Heimdallr - LLM 代码审计工具")
    parser.add_argument("--file", "-f", type=str, required=True, help="需要审计的源代码文件路径")
    parser.add_argument("--api-key", type=str, help="OpenAI API 密钥 (覆盖环境变量 OPENAI_API_KEY)")
    parser.add_argument("--base-url", type=str, help="自定义 OpenAI API 基础 URL (覆盖环境变量 OPENAI_BASE_URL)")
    parser.add_argument("--manager-model", type=str, help=f"Manager Agent 使用的 LLM 模型 (默认: {DEFAULT_MANAGER_MODEL} 或环境变量 HEIMDALLR_MANAGER_MODEL)")
    parser.add_argument("--auditor-model", type=str, help=f"Auditor Agent 使用的 LLM 模型 (默认: {DEFAULT_AUDITOR_MODEL} 或环境变量 HEIMDALLR_AUDITOR_MODEL)")
    parser.add_argument("--checker-model", type=str, help=f"Checker Agent 使用的 LLM 模型 (默认: {DEFAULT_CHECKER_MODEL} 或环境变量 HEIMDALLR_CHECKER_MODEL)")
    parser.add_argument("--debug", action="store_true", help="启用调试模式，将打印包括 API 密钥在内的额外信息 (有安全风险，仅用于本地调试)")

    args = parser.parse_args()

    # Python 3.7+ 可以使用 asyncio.run
    asyncio.run(run_audit(
        file_path=args.file,
        api_key=args.api_key,
        base_url=args.base_url,
        manager_model=args.manager_model,
        auditor_model=args.auditor_model,
        checker_model=args.checker_model,
        debug=args.debug
    ))

if __name__ == "__main__":
    main() 