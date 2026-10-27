"""Create demo daily reports tied to the seeded June–October 2026 schedules.

Run from backend with: python scripts/seed_report_demo.py
Only reports with the [演示日报 2026] name prefix are replaced on reruns.
"""

import asyncio
import sys
from collections import defaultdict
from pathlib import Path

from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api.reports import delete_report_file, save_report_file
from app.core.database import async_session, engine
from app.models import Report, Schedule, WeekPlan


SCHEDULE_PREFIX = "[演示数据 2026]%"
REPORT_PREFIX = "[演示日报 2026]"


async def main() -> None:
    async with async_session() as session:
        old_reports = (await session.execute(
            select(Report).where(Report.name.like(f"{REPORT_PREFIX}%"))
        )).scalars().all()
        for report in old_reports:
            delete_report_file(report)
            await session.delete(report)
        await session.flush()

        schedules = (await session.execute(
            select(Schedule)
            .where(Schedule.title.like(SCHEDULE_PREFIX))
            .order_by(Schedule.date, Schedule.id)
        )).scalars().all()
        week_plans = (await session.execute(
            select(WeekPlan).where(WeekPlan.title.like(SCHEDULE_PREFIX))
        )).scalars().all()
        week_title_by_id = {plan.id: plan.title for plan in week_plans}

        schedules_by_month: dict[int, dict[str, list[Schedule]]] = defaultdict(lambda: defaultdict(list))
        for schedule in schedules:
            schedules_by_month[schedule.date.month][schedule.date.isoformat()].append(schedule)

        report_count = 0
        for month in range(6, 11):
            days = sorted(schedules_by_month[month].items())
            if not days:
                continue
            # Five reports per month, sampled across the month and based on actual demo schedule titles.
            sample_indices = sorted({round(index * (len(days) - 1) / 4) for index in range(5)})
            for ordinal, sample_index in enumerate(sample_indices, start=1):
                report_date_str, daily_schedules = days[sample_index]
                chosen = daily_schedules[0]
                schedule_title = chosen.title.removeprefix("[演示数据 2026] ")
                week_title = week_title_by_id.get(chosen.week_plan_id)
                project_source = week_title.removeprefix("[演示数据 2026] ") if week_title else "临时安排"
                next_schedule = next(
                    (item for _, items in days[sample_index + 1:] for item in items), None
                )
                next_plan = next_schedule.title.removeprefix("[演示数据 2026] ") if next_schedule else "整理本周安排并确认后续节点"

                report = Report(
                    name=f"{REPORT_PREFIX} {month}月记录 {ordinal:02d} · {schedule_title}",
                    source=project_source,
                    date=chosen.date,
                    pain=f"推进“{schedule_title}”时，部分资料和执行步骤需要进一步梳理。",
                    solution=f"按任务目标拆分步骤，完成了“{schedule_title}”相关安排，并记录需要继续跟进的事项。",
                    problem="当前为演示日报内容；实际工作中可在此补充真实问题、影响范围和处理结果。",
                    tomorrow=f"继续跟进：{next_plan}。优先确认依赖项和可交付结果。",
                )
                session.add(report)
                await session.flush()
                save_report_file(report)
                report_count += 1

        await session.commit()
        print(f"已生成 {report_count} 篇演示日报，日期和项目来源关联 2026 年 6–10 月演示日程。")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
