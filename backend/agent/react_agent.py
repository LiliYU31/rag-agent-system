import sqlite3
import os
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain.agents import create_agent
from model.factory import chat_model
from utils.prompt_loader import load_system_prompts
from agent.tools.agent_tools import (
    rag_summarize,
    get_month_plans, create_month_plan, update_month_plan, delete_month_plan,
    get_week_plans, create_week_plan, update_week_plan, delete_week_plan,
    get_schedules, analyze_monthly_load, create_schedule, update_schedule, delete_schedule,
    get_reports, update_report, delete_report,get_current_date
)
from agent.tools.middleware import monitor_tool, log_before_model, report_prompt_switch

# 确保 data 目录存在
os.makedirs("data", exist_ok=True)
conn = sqlite3.connect("data/memory.db", check_same_thread=False)
# 使用 SqliteSaver 替换 MemorySaver
checkpointer = SqliteSaver(conn)

class ReactAgent:
    def __init__(self):
        self.agent = create_agent(
            model=chat_model,
            system_prompt=load_system_prompts(),
            tools=[
                rag_summarize,
                get_month_plans, create_month_plan, update_month_plan, delete_month_plan,
                get_week_plans, create_week_plan, update_week_plan, delete_week_plan,
                get_schedules, analyze_monthly_load, create_schedule, update_schedule, delete_schedule,
                get_reports, update_report, delete_report,get_current_date
            ],
            middleware=[monitor_tool, log_before_model, report_prompt_switch],
            checkpointer=checkpointer, # 绑定持久化记忆
        )

    #  3. 接收 session_id
    def execute_stream(self, query: str, session_id: str = "default"):
        input_dict = {
            "messages": [{"role": "user", "content": query}]
        }

        #  4. 配置 thread_id，LangGraph 会根据这个 ID 自动加载历史
        config = {
            "configurable": {"thread_id": session_id},
            "recursion_limit": 5
        }

        #  5. 把 config 传给 agent.stream
        for chunk in self.agent.stream(input_dict, config=config, stream_mode="values", context={"report": False}):
            latest_message = chunk["messages"][-1]
            if latest_message.content:
                yield latest_message.content.strip() + "\n"
