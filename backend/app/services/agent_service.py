"""
Agent 服务：包装已有的 ReactAgent
"""
from agent.react_agent import ReactAgent
from langchain_core.messages import AIMessage, ToolMessage


class AgentService:
    """单例：全局只创建一个 Agent 实例"""

    def __init__(self):
        self._agent = None

    @property
    def agent(self):
        if self._agent is None:
            print("=" * 50)
            print("正在初始化 ReactAgent...")
            self._agent = ReactAgent()
            print(" ReactAgent 初始化完成")
            print("=" * 50)
        return self._agent

    def chat(self, query: str, session_id: str = "default") -> str:
        """普通对话：一次性返回完整回复"""
        result = []
        for chunk in self.agent.execute_stream(query, session_id=session_id):
            result.append(chunk)
        return "".join(result)

    def stream(self, query: str, session_id: str = "default"):
        """流式对话：逐块返回（纯字符串）"""
        yield from self.agent.execute_stream(query, session_id=session_id)

    def stream_with_phase(self, query: str, session_id: str = "default"):
        """流式对话，区分【思考】和【回答】

        yield 两种事件：(phase, content)
        - phase='thinking': 思考过程（包含工具调用、检索结果等）
        - phase='answer': 正式回答
        """
        agent = self.agent

        # 构建输入和带有 thread_id 的配置（用于记忆）
        input_dict = {"messages": [{"role": "user", "content": query}]}
        config = {"configurable": {"thread_id": session_id}}

        last_content = ""
        answer_started = False

        #  注意这里加了 config 参数，LangGraph 才能记住上下文
        for chunk in agent.agent.stream(
                input_dict, config=config, stream_mode="values", context={"report": False}
        ):
            latest = chunk["messages"][-1]

            # ToolMessage：工具返回的结果，属于思考
            if isinstance(latest, ToolMessage):
                if latest.content:
                    yield ("thinking", latest.content + "\n")
                continue

            # AIMessage：模型输出
            if isinstance(latest, AIMessage):
                content = latest.content or ""
                if not content:
                    continue

                # 有 tool_calls 说明还在思考（决定调用工具）
                if getattr(latest, "tool_calls", None):
                    yield ("thinking", content + "\n")
                    continue

                # 没有 tool_calls 就是最终回答
                # 计算新增部分（因为 LangGraph 的 values 模式每次返回的都是全量内容）
                if content.startswith(last_content):
                    new_part = content[len(last_content):]
                else:
                    new_part = content

                if new_part:
                    if not answer_started:
                        answer_started = True
                    yield ("answer", new_part)
                last_content = content

    def get_history(self, session_id: str) -> list:
        """通过 LangGraph 原生接口获取历史消息"""
        try:
            # 这里的 config 和你流式请求里的一致
            config = {"configurable": {"thread_id": session_id}}
            # 原生方法：获取当前 thread 的 checkpoint 状态
            state = self.agent.agent.get_state(config)

            if not state or not state.values:
                return []

            messages = state.values.get("messages", [])
            result = []
            for msg in messages:
                # 区分用户和AI
                role = "user" if msg.type == "human" else "ai"
                content = msg.content
                if content:
                    result.append({"role": role, "content": content})
            return result
        except Exception as e:
            print(f"读取历史记录失败: {e}")
            return []


# 全局单例
agent_service = AgentService()