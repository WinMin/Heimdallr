from abc import ABC, abstractmethod
from typing import List, Dict, Any
from heimdallr.core.llm_connector import LLMConnector

class BaseAgent(ABC):
    """
    Agent 的抽象基类。
    每个 Agent 都有一个 LLM 连接器、一个角色和一个模型名称。
    """
    def __init__(self, llm_connector: LLMConnector, model_name: str, system_prompt: str = None):
        """
        初始化 BaseAgent。

        参数:
            llm_connector (LLMConnector): 用于与 LLM API 通信的连接器。
            model_name (str): 此 Agent 使用的 LLM 模型名称。
            system_prompt (str, optional): 此 Agent 的系统级提示。默认为 None。
        """
        self.llm_connector = llm_connector
        self.model_name = model_name
        self.system_prompt = system_prompt or "You are a helpful AI assistant."
        self.history: List[Dict[str, str]] = []

    def _construct_messages(self, user_query: str, context: Dict[str, Any] = None) -> List[Dict[str, str]]:
        """
        构建发送给 LLM 的消息列表，包括系统提示、历史记录和当前用户查询。
        子类可以覆盖此方法以添加更复杂的上下文处理。
        """
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self.history)
        
        # 子类可能需要以特定方式格式化上下文
        if context:
            # 简单的上下文添加方式，子类可以做得更精细
            context_str = "\nRelevant Context:\n"
            for key, value in context.items():
                context_str += f"{key}: {str(value)}\n"
            user_query_with_context = f"{user_query}{context_str}"
        else:
            user_query_with_context = user_query
            
        messages.append({"role": "user", "content": user_query_with_context})
        return messages

    def chat(self, user_query: str, context: Dict[str, Any] = None, temperature: float = 0.5, max_tokens: int = 2048) -> str | None:
        """
        与 LLM 进行单轮对话。

        参数:
            user_query (str): 用户的查询或指令。
            context (Dict[str, Any], optional): 提供给 LLM 的附加上下文信息。
            temperature (float, optional): LLM 的温度参数。默认为 0.5。
            max_tokens (int, optional): LLM 生成的最大 token 数。默认为 2048。

        返回:
            str | None: LLM 的响应文本，如果出错则为 None。
        """
        messages = self._construct_messages(user_query, context)
        
        # print(f"--- Sending to {self.model_name} ({self.__class__.__name__}) ---")
        # for msg in messages:
        #     print(f"{msg['role'].capitalize()}: {msg['content'][:200]}{'...' if len(msg['content']) > 200 else ''}")
        # print("----------------------------------------------------")

        response = self.llm_connector.invoke_llm(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        if response:
            # 将当前交互（不包括上下文，因为它已融入user_query）和响应添加到历史记录
            self.history.append({"role": "user", "content": user_query}) # 记录原始 user_query
            self.history.append({"role": "assistant", "content": response})
        return response

    def clear_history(self):
        """清空对话历史。"""
        self.history = []

    @abstractmethod
    async def process_task(self, task_description: str, context: Dict[str, Any] = None) -> Any:
        """
        处理特定任务的抽象方法。子类必须实现此方法。

        参数:
            task_description (str): 任务的描述。
            context (Dict[str, Any], optional): 任务相关的上下文。

        返回:
            Any: 任务处理的结果。
        """
        pass

# 可以在这里添加一个简单的测试或示例，如果需要的话
# 但由于是抽象基类，通常在子类中测试更合适 