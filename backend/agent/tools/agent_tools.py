import json
import pymysql
from datetime import date, time, timedelta
from calendar import monthrange
from math import sqrt
from zoneinfo import ZoneInfo
from langchain_core.tools import tool
from rag.rag_service import RagSummarizeService
from datetime import datetime

# 实例化 RAG 服务
rag = RagSummarizeService()

# ═══════════════════════════════════════════════════
# 数据库连接配置 (按你的实际情况修改密码)
# ═══════════════════════════════════════════════════
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "1234",
    "database": "schedwise",
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor
}


def get_db():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)


# ═══════════════════════════════════════════════════
# 1. 知识库与日报检索 (RAG)
# ═══════════════════════════════════════════════════
@tool(
    description="用于检索时间管理法则（如番茄工作法、GTD）、历史日报等专业参考资料。当用户询问时间规划建议、工作痛点分析或效率提升时，调用此工具。")
def rag_summarize(query: str) -> str:
    return rag.rag_summarize(query)


# ═══════════════════════════════════════════════════
# 2. 月计划工具
# ═══════════════════════════════════════════════════
@tool(description="查询所有的月计划。返回 JSON 字符串。")
def get_month_plans() -> str:
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, title, deadline FROM month_plans ORDER BY deadline")
            results = cursor.fetchall()
            for r in results:
                if r['deadline']: r['deadline'] = r['deadline'].isoformat()
            return json.dumps(results, ensure_ascii=False)


@tool(description="新建一个月计划。需要提供标题和截止日期(YYYY-MM-DD)。")
def create_month_plan(title: str, deadline: str = None) -> str:
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S') # 获取当前时间
    with get_db() as conn:
        with conn.cursor() as cursor:
            sql = "INSERT INTO month_plans (title, deadline, created_at) VALUES (%s, %s, %s)"
            cursor.execute(sql, (title, deadline, now_str))
            conn.commit()
    return "[UI_ACTION: /calendar] [调用工具: create_month_plan] 成功创建月计划。"


@tool(description="修改月计划。需要提供月计划ID，以及要修改的标题或截止日期(YYYY-MM-DD)。")
def update_month_plan(plan_id: int, title: str = None, deadline: str = None) -> str:
    with get_db() as conn:
        with conn.cursor() as cursor:
            updates = []
            params = []
            if title is not None:
                updates.append("title = %s")
                params.append(title)
            if deadline is not None:
                updates.append("deadline = %s")
                params.append(deadline)

            if updates:
                sql = f"UPDATE month_plans SET {', '.join(updates)} WHERE id = %s"
                params.append(plan_id)
                cursor.execute(sql, tuple(params))
                conn.commit()
    return "[UI_ACTION: /calendar] [调用工具: update_month_plan] 成功修改月计划。"


@tool(description="删除月计划。需要提供月计划ID。")
def delete_month_plan(plan_id: int) -> str:
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM month_plans WHERE id = %s", (plan_id,))
            conn.commit()
    return "[UI_ACTION: /calendar] [调用工具: delete_month_plan] 成功删除月计划。"


# ═══════════════════════════════════════════════════
# 3. 周计划工具
# ═══════════════════════════════════════════════════
@tool(description="查询所有的周计划。返回文本描述。")
def get_week_plans() -> str:
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, title, month_plan_id, start_date, deadline FROM week_plans ORDER BY deadline")
            results = cursor.fetchall()
            if not results:
                return "当前没有任何周计划。"

            lines = []
            for r in results:
                deadline = r['deadline'].isoformat() if r['deadline'] else "无"
                lines.append(f"- [ID:{r['id']}] {r['title']} (截止日期: {deadline})")
            return "现有的周计划如下：\n" + "\n".join(lines)


@tool(description="新建一个周计划。需要提供标题，可选的所属月计划ID、开始日期和截止日期(YYYY-MM-DD)。")
def create_week_plan(title: str, month_plan_id: int = None, start_date: str = None, deadline: str = None) -> str:
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S') # 获取当前时间
    with get_db() as conn:
        with conn.cursor() as cursor:
            sql = "INSERT INTO week_plans (title, month_plan_id, start_date, deadline, created_at) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql, (title, month_plan_id, start_date, deadline, now_str))
            conn.commit()
    return "[UI_ACTION: /calendar] [调用工具: create_week_plan] 成功创建周计划。"


@tool(description="修改周计划。需要提供周计划ID，以及要修改的字段（标题、月计划ID、截止日期）。")
def update_week_plan(plan_id: int, title: str = None, month_plan_id: int = None, deadline: str = None) -> str:
    with get_db() as conn:
        with conn.cursor() as cursor:
            updates = []
            params = []
            if title is not None:
                updates.append("title = %s")
                params.append(title)
            if month_plan_id is not None:
                updates.append("month_plan_id = %s")
                params.append(month_plan_id)
            if deadline is not None:
                updates.append("deadline = %s")
                params.append(deadline)

            if updates:
                sql = f"UPDATE week_plans SET {', '.join(updates)} WHERE id = %s"
                params.append(plan_id)
                cursor.execute(sql, tuple(params))
                conn.commit()
    return "[UI_ACTION: /calendar] [调用工具: update_week_plan] 成功修改周计划。"


@tool(description="删除周计划。需要提供周计划ID。")
def delete_week_plan(plan_id: int) -> str:
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM week_plans WHERE id = %s", (plan_id,))
            conn.commit()
    return "[UI_ACTION: /calendar] [调用工具: delete_week_plan] 成功删除周计划。"


# ═══════════════════════════════════════════════════
# 4. 日程工具
# ═══════════════════════════════════════════════════
@tool(description="查询所有的日程。返回 JSON 字符串。")
def get_schedules() -> str:
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, title, date, start_time, end_time, week_plan_id, color FROM schedules ORDER BY date, start_time")
            results = cursor.fetchall()
            for r in results:
                if r['date']: r['date'] = r['date'].isoformat()
                r['start_time'] = str(r['start_time']) if r['start_time'] else None
                r['end_time'] = str(r['end_time']) if r['end_time'] else None
            return json.dumps(results, ensure_ascii=False)


@tool(description="对指定年月进行计划负载分析。返回当月月计划、周计划、日程、安排时长、周计划关联率、每日负载、最忙日期、日均时长、波动及近六个月趋势。用户要求分析某月学习状态、计划安排、学习负载或总结月度安排时必须调用。该工具只能说明计划与安排，不能推断任务是否完成或实际学习时长。")
def analyze_monthly_load(year: int, month: int) -> str:
    if month < 1 or month > 12:
        return "月份无效，请提供 1 到 12 之间的月份。"

    selected_start = date(year, month, 1)
    selected_end = date(year + (month == 12), month % 12 + 1, 1)
    trend_index = year * 12 + month - 1 - 5
    trend_start = date(trend_index // 12, trend_index % 12 + 1, 1)

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, title, deadline FROM month_plans WHERE deadline >= %s AND deadline < %s ORDER BY deadline",
                (selected_start, selected_end),
            )
            month_plans = cursor.fetchall()
            cursor.execute(
                "SELECT w.id, w.title, w.month_plan_id, w.deadline, m.title AS month_plan_title "
                "FROM week_plans w LEFT JOIN month_plans m ON m.id = w.month_plan_id "
                "WHERE w.deadline >= %s AND w.deadline < %s ORDER BY w.deadline",
                (selected_start, selected_end),
            )
            week_plans = cursor.fetchall()
            cursor.execute(
                "SELECT s.id, s.title, s.date, s.start_time, s.end_time, s.week_plan_id, w.title AS week_plan_title "
                "FROM schedules s LEFT JOIN week_plans w ON w.id = s.week_plan_id "
                "WHERE s.date >= %s AND s.date < %s ORDER BY s.date, s.start_time",
                (selected_start, selected_end),
            )
            schedules = cursor.fetchall()
            cursor.execute(
                "SELECT id, deadline FROM month_plans WHERE deadline >= %s AND deadline < %s",
                (trend_start, selected_end),
            )
            trend_month_plans = cursor.fetchall()
            cursor.execute(
                "SELECT id, deadline FROM week_plans WHERE deadline >= %s AND deadline < %s",
                (trend_start, selected_end),
            )
            trend_week_plans = cursor.fetchall()
            cursor.execute(
                "SELECT date, start_time, end_time FROM schedules WHERE date >= %s AND date < %s",
                (trend_start, selected_end),
            )
            trend_schedules = cursor.fetchall()

    def hours_between(start, end):
        if not start or not end:
            return 0.0
        if isinstance(start, timedelta) and isinstance(end, timedelta):
            return max(0.0, (end - start).total_seconds() / 3600)
        seconds = (end.hour * 3600 + end.minute * 60 + end.second) - (
            start.hour * 3600 + start.minute * 60 + start.second
        )
        return max(0.0, seconds / 3600)

    def month_bounds(index):
        return date(index // 12, index % 12 + 1, 1)

    days_in_month = monthrange(year, month)[1]
    daily = {
        date(year, month, day).isoformat(): {"schedule_count": 0, "planned_hours": 0.0}
        for day in range(1, days_in_month + 1)
    }
    for schedule in schedules:
        key = schedule["date"].isoformat()
        daily[key]["schedule_count"] += 1
        daily[key]["planned_hours"] += hours_between(schedule["start_time"], schedule["end_time"])

    hours_by_day = [item["planned_hours"] for item in daily.values()]
    total_hours = sum(hours_by_day)
    daily_mean = total_hours / days_in_month
    daily_stddev = sqrt(sum((value - daily_mean) ** 2 for value in hours_by_day) / days_in_month)
    busiest = max(daily.items(), key=lambda item: (item[1]["planned_hours"], item[1]["schedule_count"])) if schedules else None
    linked_count = sum(1 for schedule in schedules if schedule["week_plan_id"] is not None)

    trend = []
    for offset in range(6):
        index = year * 12 + month - 1 - 5 + offset
        start = month_bounds(index)
        end = month_bounds(index + 1)
        trend.append({
            "month": f"{start.year}-{start.month:02d}",
            "month_plans": sum(1 for item in trend_month_plans if item["deadline"] and start <= item["deadline"] < end),
            "week_plans": sum(1 for item in trend_week_plans if item["deadline"] and start <= item["deadline"] < end),
            "schedules": sum(1 for item in trend_schedules if start <= item["date"] < end),
            "planned_hours": round(sum(hours_between(item["start_time"], item["end_time"]) for item in trend_schedules if start <= item["date"] < end), 2),
        })

    response = {
        "period": f"{year}-{month:02d}",
        "definitions": {
            "month_plan_count": "按截止日期落在当月统计",
            "week_plan_count": "按截止日期落在当月统计",
            "schedule_count": "按日程日期落在当月统计",
            "planned_hours": "仅累加有有效开始和结束时间的日程，不代表实际学习时长",
            "completion": "系统未记录完成状态，不推断完成率或实际学习成果",
        },
        "summary": {
            "month_plan_count": len(month_plans),
            "week_plan_count": len(week_plans),
            "schedule_count": len(schedules),
            "planned_hours": round(total_hours, 2),
            "linked_schedule_ratio_percent": round(linked_count / len(schedules) * 100, 1) if schedules else 0,
            "busiest_day": {
                "date": busiest[0],
                "schedule_count": busiest[1]["schedule_count"],
                "planned_hours": round(busiest[1]["planned_hours"], 2),
            } if busiest else None,
            "daily_mean_hours": round(daily_mean, 2),
            "daily_stddev_hours": round(daily_stddev, 2),
        },
        "month_plans": month_plans,
        "week_plans": week_plans,
        "daily_load": [{"date": day, **value, "planned_hours": round(value["planned_hours"], 2)} for day, value in daily.items()],
        "trend_six_months": trend,
    }
    return json.dumps(response, ensure_ascii=False, default=str)


@tool(description="新建日程。需要提供标题、日期(YYYY-MM-DD)、开始时间(HH:MM)和结束时间(HH:MM)。可选的周计划ID。")
def create_schedule(title: str, date: str, start_time: str, end_time: str, week_plan_id: int = None) -> str:
    # 格式化时间，补全秒数
    st = f"{start_time}:00" if len(start_time) == 5 else start_time
    et = f"{end_time}:00" if len(end_time) == 5 else end_time
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 获取当前时间

    with get_db() as conn:
        with conn.cursor() as cursor:
            sql = "INSERT INTO schedules (title, date, start_time, end_time, week_plan_id, color, repeat_type, created_at) VALUES (%s, %s, %s, %s, %s, 'blue', 'none', %s)"
            cursor.execute(sql, (title, date, st, et, week_plan_id, now_str))
            conn.commit()
    return "[UI_ACTION: /schedule] [调用工具: create_schedule] 成功创建日程。"


@tool(description="修改日程。需要提供日程ID，以及要修改的字段（标题、日期、时间等）。")
def update_schedule(schedule_id: int, title: str = None, date: str = None, start_time: str = None,
                    end_time: str = None) -> str:
    with get_db() as conn:
        with conn.cursor() as cursor:
            updates = []
            params = []
            if title is not None:
                updates.append("title = %s")
                params.append(title)
            if date is not None:
                updates.append("date = %s")
                params.append(date)
            if start_time is not None:
                updates.append("start_time = %s")
                params.append(f"{start_time}:00" if len(start_time) == 5 else start_time)
            if end_time is not None:
                updates.append("end_time = %s")
                params.append(f"{end_time}:00" if len(end_time) == 5 else end_time)

            if updates:
                sql = f"UPDATE schedules SET {', '.join(updates)} WHERE id = %s"
                params.append(schedule_id)
                cursor.execute(sql, tuple(params))
                conn.commit()
    return "[UI_ACTION: /schedule] [调用工具: update_schedule] 成功修改日程。"


@tool(description="删除日程。需要提供日程ID。")
def delete_schedule(schedule_id: int) -> str:
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM schedules WHERE id = %s", (schedule_id,))
            conn.commit()
    return "[UI_ACTION: /schedule] [调用工具: delete_schedule] 成功删除日程。"


# ═══════════════════════════════════════════════════
# 5. 日报工具
# ═══════════════════════════════════════════════════
@tool(description="查询所有日报。返回 JSON 字符串。")
def get_reports() -> str:
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, name, source, date, pain, solution, problem, tomorrow FROM reports ORDER BY date DESC")
            results = cursor.fetchall()
            for r in results:
                if r['date']: r['date'] = r['date'].isoformat()
            return json.dumps(results, ensure_ascii=False)


@tool(description="修改日报内容。需要提供日报ID和修改后的文本内容。")
def update_report(report_id: int, pain: str = None, solution: str = None, problem: str = None,
                  tomorrow: str = None) -> str:
    with get_db() as conn:
        with conn.cursor() as cursor:
            updates = []
            params = []
            if pain is not None:
                updates.append("pain = %s")
                params.append(pain)
            if solution is not None:
                updates.append("solution = %s")
                params.append(solution)
            if problem is not None:
                updates.append("problem = %s")
                params.append(problem)
            if tomorrow is not None:
                updates.append("tomorrow = %s")
                params.append(tomorrow)

            if updates:
                sql = f"UPDATE reports SET {', '.join(updates)} WHERE id = %s"
                params.append(report_id)
                cursor.execute(sql, tuple(params))
                conn.commit()
    return "[UI_ACTION: /report] [调用工具: update_report] 成功修改日报。"


@tool(description="删除日报。需要提供日报ID。")
def delete_report(report_id: int) -> str:
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM reports WHERE id = %s", (report_id,))
            conn.commit()
    return "[UI_ACTION: /report] [调用工具: delete_report] 成功删除日报。"

# ═══════════════════════════════════════════════════
# 6. 时间工具
# ═══════════════════════════════════════════════════
@tool(description="获取当前真实的日期、时间和星期几。当用户询问今天几号、明天几号、需要基于今天推算相对日期，或询问未注明年份的某月时，必须优先调用此工具获取基准时间。")
def get_current_date() -> str:
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    weekday_map = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    weekday = weekday_map[now.weekday()]
    return f"{now.strftime('%Y-%m-%d %H:%M')} {weekday}"
