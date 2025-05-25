import os
from openai import OpenAI
import openai

class LLMConnector:
    """
    负责与 OpenAI 兼容的 LLM API 进行交互。
    支持自定义 api_key 和 base_url。
    """
    def __init__(self, api_key: str = None, base_url: str = None, timeout: int = 60):
        """
        初始化 LLMConnector。

        参数:
            api_key (str, optional): API 密钥。如果未提供，则从环境变量 OPENAI_API_KEY 中读取。
            base_url (str, optional): API 的基础 URL。如果未提供，则使用 OpenAI 默认 URL 或从 OPENAI_BASE_URL 环境变量读取。
            timeout (int, optional): API 请求的超时时间（秒）。默认为 60。
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        
        if not self.api_key:
            raise ValueError("API key must be provided either as an argument or via OPENAI_API_KEY environment variable.")

        client_args = {"api_key": self.api_key, "timeout": timeout}
        if self.base_url:
            client_args["base_url"] = self.base_url
        
        self.client = OpenAI(**client_args)

    def invoke_llm(self, model: str, messages: list[dict], temperature: float = 0.7, max_tokens: int = 2048) -> str | None:
        """
        调用 LLM API 生成聊天完成。

        参数:
            model (str): 要使用的模型名称，例如 "gpt-3.5-turbo" 或 "gemini-2.0-flash"。
            messages (list[dict]): 消息列表，格式应符合 OpenAI API 要求。
                                  例如: [{"role": "system", "content": "You are an assistant."}, {"role": "user", "content": "Hello!"}]
            temperature (float, optional): 控制生成文本的随机性。默认为 0.7。
            max_tokens (int, optional): 生成文本的最大 token 数。默认为 2048。

        返回:
            str | None: LLM 生成的文本内容，如果发生错误则返回 None。
        """
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            if response.choices and response.choices[0].message:
                return response.choices[0].message.content.strip()
            else:
                print("LLM API 响应中没有有效的 choices 或 message。")
                return None
        except openai.APITimeoutError:
            print(f"Error: API request timed out after {self.client.timeout}s.")
            return None
        except openai.APIConnectionError as e:
            print(f"Error: Could not connect to API: {e}")
            return None
        except openai.RateLimitError as e:
            print(f"Error: API rate limit exceeded: {e}")
            return None
        except openai.APIStatusError as e:
            error_details = "No additional details available."
            try:
                # 尝试将响应体解析为JSON，因为错误信息通常是JSON格式
                error_details = e.response.json()
            except Exception:
                # 如果解析JSON失败，尝试获取原始文本
                try:
                    error_details = e.response.text
                except Exception:
                    pass # 保留 "No additional details available."
            print(f"Error: API returned an error status: {e.status_code} - {e.response}\nDetails: {error_details}")
            return None
        except Exception as e:
            if isinstance(e, openai.APIError):
                print(f"An OpenAI API error occurred: {e}")
            else:
                print(f"An unexpected error occurred while invoking LLM: {e}")
            return None

if __name__ == '__main__':
    # 这是一个简单的使用示例
    # 在运行前，请确保设置了 OPENAI_API_KEY 环境变量
    # 如果使用自定义的 base_url (例如 Google AI Studio for Gemini)
    # 也请设置 OPENAI_BASE_URL 环境变量
    # export OPENAI_API_KEY="YOUR_GEMINI_API_KEY"
    # export OPENAI_BASE_URL="https://generativelanguage.googleapis.com/v1beta/openai/"

    print("开始 LLMConnector 测试...")
    
    # 尝试从环境变量加载 API 密钥和基础 URL
    custom_api_key = os.getenv("OPENAI_API_KEY")
    custom_base_url = os.getenv("OPENAI_BASE_URL") # "https://generativelanguage.googleapis.com/v1beta/openai/"

    if not custom_api_key:
        print("\n警告: OPENAI_API_KEY 环境变量未设置。测试将失败。")
        print("请设置 OPENAI_API_KEY 后重试。")
        if not custom_base_url:
            print("如果您使用的是 Gemini，还需要设置 OPENAI_BASE_URL。")
        exit(1)
    
    print(f"使用 API Key: {'*' * (len(custom_api_key) - 4) + custom_api_key[-4:] if custom_api_key else '未提供'}")
    print(f"使用 Base URL: {custom_base_url if custom_base_url else 'OpenAI 默认'}")

    try:
        connector = LLMConnector(api_key=custom_api_key, base_url=custom_base_url)
        
        # 根据您的 API 提供商选择合适的模型
        # 对于 OpenAI: "gpt-3.5-turbo", "gpt-4", etc.
        # 对于 Gemini (通过兼容API): "gemini-pro", "models/gemini-pro" (某些旧的Gemini教程URL可能用这个)
        # model_name = "gpt-3.5-turbo" # 如果使用 OpenAI
        # 如果您的 base_url 是 https://generativelanguage.googleapis.com/v1beta/openai/
        # 那么模型名称通常是 gemini-pro, gemini-1.5-flash-latest 等，而不是 models/gemini-pro
        model_name = "gemini-pro" 

        messages = [
            {"role": "system", "content": "You are a helpful code assistant."},
            {"role": "user", "content": "Explain the concept of a race condition in concurrent programming in simple terms."}
        ]
        
        print(f"\n正在调用模型: {model_name}...")
        response_content = connector.invoke_llm(model=model_name, messages=messages)
        
        if response_content:
            print("\nLLM 响应:")
            print(response_content)
        else:
            print("\n未能从 LLM 获取响应。")

    except ValueError as ve:
        print(f"\n初始化错误: {ve}")
    except Exception as e:
        print(f"\n测试过程中发生意外错误: {e}")

    print("\nLLMConnector 测试结束。") 