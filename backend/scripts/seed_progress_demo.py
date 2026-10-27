"""Seed repeatable progress-dashboard demo data for June–October 2026.

Run from backend with: python scripts/seed_progress_demo.py
Only rows with the DEMO-2026 title prefix are replaced on reruns.
"""

import asyncio
import random
import sys
from datetime import date, time, timedelta
from pathlib import Path

from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import async_session, engine
from app.models import MonthPlan, RepeatType, Schedule, WeekPlan


PREFIX = "[演示数据 2026]"
MONTHS = (6, 7, 8, 9, 10)
MONTH_PLAN_COUNTS = (3, 4, 5, 3, 5)
WEEK_PLAN_COUNTS = (4, 5, 7, 6, 8)
SCHEDULE_COUNTS = (12, 17, 21, 23, 27)
RNG = random.Random(20261027)


def clustered_date(year: int, month: int, anchors: list[int]) -> date:
    days_in_month = (date(year + (month == 12), month % 12 + 1, 1) - timedelta(days=1)).day
    if anchors and RNG.random() < 0.68:
        day = min(days_in_month, max(1, RNG.choice(anchors) + RNG.randint(-2, 2)))
    else:
        day = RNG.randint(1, days_in_month)
    return date(year, month, day)


async def main() -> None:
    async with async_session() as session:
        demo_schedules = (await session.execute(
            select(Schedule).where(Schedule.title.like(f"{PREFIX}%"))
        )).scalars().all()
        demo_weeks = (await session.execute(
            select(WeekPlan).where(WeekPlan.title.like(f"{PREFIX}%"))
        )).scalars().all()
        demo_months = (await session.execute(
            select(MonthPlan).where(MonthPlan.title.like(f"{PREFIX}%"))
        )).scalars().all()

        for row in demo_schedules:
            await session.delete(row)
        for row in demo_weeks:
            await session.delete(row)
        for row in demo_months:
            await session.delete(row)
        await session.flush()

        month_plans_by_month: dict[int, list[MonthPlan]] = {}
        for month, count in zip(MONTHS, MONTH_PLAN_COUNTS):
            month_plans_by_month[month] = []
            for index in range(count):
                plan = MonthPlan(
                    title=f"{PREFIX} {month}月重点计划 {index + 1:02d}",
                    deadline=clustered_date(2026, month, [8, 18, 25]),
                )
                session.add(plan)
                month_plans_by_month[month].append(plan)
        await session.flush()

        week_plans_by_month: dict[int, list[WeekPlan]] = {}
        for month, count in zip(MONTHS, WEEK_PLAN_COUNTS):
            week_plans_by_month[month] = []
            month_start = date(2026, month, 1)
            month_end = date(2026, month + 1, 1) if month < 12 else date(2027, 1, 1)
            for index in range(count):
                deadline = clustered_date(2026, month, [7, 15, 23, 28])
                start_date = max(month_start, deadline - timedelta(days=RNG.randint(3, 7)))
                month_options = month_plans_by_month[month]
                parent_id = RNG.choice(month_options).id if RNG.random() < 0.76 else None
                plan = WeekPlan(
                    title=f"{PREFIX} {month}月周计划 {index + 1:02d}",
                    month_plan_id=parent_id,
                    start_date=min(start_date, month_end - timedelta(days=1)),
                    deadline=deadline,
                )
                session.add(plan)
                week_plans_by_month[month].append(plan)
        await session.flush()

        total_schedules = 0
        for month, count in zip(MONTHS, SCHEDULE_COUNTS):
            anchors = [RNG.randint(4, 27) for _ in range(3)]
            month_weeks = week_plans_by_month[month]
            for index in range(count):
                scheduled_date = clustered_date(2026, month, anchors)
                start_hour = RNG.randint(12, 19)
                start_minute = RNG.choice((0, 15, 30, 45))
                duration_minutes = RNG.choice((30, 45, 60, 75, 90, 120, 150))
                start_minutes = start_hour * 60 + start_minute
                end_minutes = min(start_minutes + duration_minutes, 23 * 60)
                week_id = RNG.choice(month_weeks).id if RNG.random() < 0.78 else None
                session.add(Schedule(
                    title=f"{PREFIX} {month}月安排 {index + 1:03d}",
                    week_plan_id=week_id,
                    date=scheduled_date,
                    start_time=time(start_minutes // 60, start_minutes % 60),
                    end_time=time(end_minutes // 60, end_minutes % 60),
                    color=RNG.choice(("blue", "green", "orange", "purple")),
                    repeat_type=RepeatType.none,
                ))
                total_schedules += 1

        await session.commit()
        inserted_months = sum(MONTH_PLAN_COUNTS)
        inserted_weeks = sum(WEEK_PLAN_COUNTS)
        print(
            f"演示数据已生成：{inserted_months} 个月计划、{inserted_weeks} 周计划、"
            f"{total_schedules} 个日程（2026 年 6–10 月）。"
        )
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
