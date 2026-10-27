"""
工具拿不到上下文，所以放到中间件实现
"""

from langchain.agents import AgentState
from langchain.agents.middleware import wrap_tool_call, before_model, dynamic_prompt, ModelRequest
from langchain.tools.tool_node import ToolCallRequest
from typing import Callable
import re
from langgraph.runtime import Runtime
from langgraph.types import Command
from utils.logger_handler import logger
from utils.prompt_loader import load_system_prompts,load_report_prompts
from langchain_core.messages import ToolMessage


@wrap_tool_call
def monitor_tool(request, handle):
    tool_name = request.tool_call['name']
    state = request.runtime.state
    messages = state.get("messages", [])
    last_human_content = ""
    for msg in reversed(messages):
        if msg.type == "human":
            last_human_content = msg.content
            break

    # 定义哪些是危险操作（增删改）
    write_tools = [
        "create_schedule", "update_schedule", "delete_schedule",
        "create_week_plan", "update_week_plan", "delete_week_plan",
        "create_month_plan", "update_month_plan", "delete_month_plan",
        "update_report", "delete_report"
    ]

    # Normalize an omitted year to the real current year. The model may otherwise
    # invent a historical year when the user says only "10月份".
    if tool_name == "analyze_monthly_load":
        args = request.tool_call.get("args", {})
        if isinstance(args, dict):
            from agent.tools.agent_tools import get_current_date

            current_date_text = get_current_date.func()
            current_year, current_month = map(int, current_date_text[:7].split("-")[:2])
            explicit_years = re.findall(r"(?<!\d)(20\d{2})(?!\d)", last_human_content)
            relative_year = current_year
            if re.search(r"前年|前两年", last_human_content):
                relative_year -= 2
            elif re.search(r"去年|上一年", last_human_content):
                relative_year -= 1
            elif re.search(r"明年|下一年", last_human_content):
                relative_year += 1
            args["year"] = int(explicit_years[-1]) if explicit_years else relative_year

            month_match = re.search(r"(?<!\d)(1[0-2]|0?[1-9]|十二|十一|十|[一二三四五六七八九])\s*月", last_human_content)
            if month_match:
                month_text = month_match.group(1)
                chinese_months = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10, "十一": 11, "十二": 12}
                args["month"] = chinese_months.get(month_text, int(month_text) if month_text.isdigit() else None)
            elif re.search(r"上个月|上月", last_human_content):
                month_index = current_year * 12 + current_month - 2
                args["year"], args["month"] = month_index // 12, month_index % 12 + 1
            elif re.search(r"下个月|下月", last_human_content):
                month_index = current_year * 12 + current_month
                args["year"], args["month"] = month_index // 12, month_index % 12 + 1
            elif re.search(r"本月|这个月|当月", last_human_content):
                args["month"] = current_month

    if tool_name in write_tools:
        # 如果用户没发确认词，直接拦截！
        confirm_words = ["确认", "同意", "可以", "是的", "是"]
        if not any(word in last_human_content for word in confirm_words):
            logger.info(f"[monitor_tool]拦截了未经确认的写操作：{tool_name}")
            # 伪造一个工具返回值，强行打断大模型的执行意图
            return ToolMessage(
                content="操作被系统拦截。你必须先列出表单让用户确认！请对用户说：请回复【确认】以执行操作。",
                tool_call_id=request.tool_call['id']
            )

    # 如果通过了确认，或者是不需要确认的查询工具，正常执行
    logger.info(f"[monitor_tool]执行工具：{tool_name}")
    result = handle(request)
    return result

#模型执行前输出日志
@before_model
def log_before_model(
        state:AgentState, #整个agent智能体中的状态记录
        runtime:Runtime,  #整个执行过程中的上下文信息
):
    logger.info(f"[log_before_model]即将结束，带有{len(state['messages'])}条消息")
    #[-1]表示只取最新一条模型返回的消息
    logger.debug(f"[log_before_model]{type(state['messages'][-1]).__name__}|{state['messages'][-1].content.strip()}")

    return None

#动态切换提示词，默认为False，回到主任务->如果调用，又回到报告提示词
@dynamic_prompt     #每一次在生成提示词之前，调用此函数
def report_prompt_switch(request:ModelRequest):
    is_report=request.runtime.context.get("report",False)
    if is_report:  #是报告生成场景，返回报告生成提示词内容
        print("*"*30)
        return load_report_prompts()

    return load_system_prompts()
