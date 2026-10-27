from calendar import monthrange
from datetime import date
from math import sqrt

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import MonthPlan, Schedule, WeekPlan

router = APIRouter()


def shift_month(year: int, month: int, offset: int) -> tuple[int, int]:
    month_index = year * 12 + month - 1 + offset
    return month_index // 12, month_index % 12 + 1


def month_start(year: int, month: int) -> date:
    return date(year, month, 1)


def duration_hours(schedule: Schedule) -> float:
    if not schedule.start_time or not schedule.end_time:
        return 0
    seconds = (schedule.end_time.hour * 3600 + schedule.end_time.minute * 60 + schedule.end_time.second) - (
        schedule.start_time.hour * 3600 + schedule.start_time.minute * 60 + schedule.start_time.second
    )
    return max(0, seconds / 3600)


@router.get("/progress/monthly")
async def monthly_progress(year: int, month: int, db: AsyncSession = Depends(get_db)):
    """Return a monthly workload overview and a six-month trend ending at the selected month."""
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="月份必须在 1 到 12 之间")

    selected_start = month_start(year, month)
    selected_next_year, selected_next_month = shift_month(year, month, 1)
    selected_end = month_start(selected_next_year, selected_next_month)
    trend_year, trend_month = shift_month(year, month, -5)
    trend_start = month_start(trend_year, trend_month)

    month_result = await db.execute(
        select(MonthPlan).where(MonthPlan.deadline >= selected_start, MonthPlan.deadline < selected_end)
    )
    month_plans = month_result.scalars().all()

    week_result = await db.execute(
        select(WeekPlan).where(WeekPlan.deadline >= selected_start, WeekPlan.deadline < selected_end)
    )
    week_plans = week_result.scalars().all()

    schedule_result = await db.execute(
        select(Schedule).where(Schedule.date >= trend_start, Schedule.date < selected_end)
    )
    schedules = schedule_result.scalars().all()

    selected_schedules = [s for s in schedules if selected_start <= s.date < selected_end]
    day_count = monthrange(year, month)[1]
    daily = {
        date(year, month, day).isoformat(): {"schedule_count": 0, "planned_hours": 0.0}
        for day in range(1, day_count + 1)
    }
    for schedule in selected_schedules:
        key = schedule.date.isoformat()
        if key in daily:
            daily[key]["schedule_count"] += 1
            daily[key]["planned_hours"] += duration_hours(schedule)

    trend = []
    for offset in range(6):
        trend_year_i, trend_month_i = shift_month(trend_year, trend_month, offset)
        start_i = month_start(trend_year_i, trend_month_i)
        next_year_i, next_month_i = shift_month(trend_year_i, trend_month_i, 1)
        end_i = month_start(next_year_i, next_month_i)
        trend.append({
            "month": f"{trend_year_i}-{trend_month_i:02d}",
            "month_plans": sum(1 for p in month_plans if p.deadline and start_i <= p.deadline < end_i)
                if start_i >= selected_start else None,
            "week_plans": sum(1 for p in week_plans if p.deadline and start_i <= p.deadline < end_i)
                if start_i >= selected_start else None,
            "schedules": sum(1 for s in schedules if start_i <= s.date < end_i),
            "planned_hours": round(sum(duration_hours(s) for s in schedules if start_i <= s.date < end_i), 2),
        })

    # Load plan data for the full trend window so earlier months have real counts too.
    trend_month_result = await db.execute(
        select(MonthPlan).where(MonthPlan.deadline >= trend_start, MonthPlan.deadline < selected_end)
    )
    trend_month_plans = trend_month_result.scalars().all()
    trend_week_result = await db.execute(
        select(WeekPlan).where(WeekPlan.deadline >= trend_start, WeekPlan.deadline < selected_end)
    )
    trend_week_plans = trend_week_result.scalars().all()
    for point in trend:
        point_year, point_month = map(int, point["month"].split("-"))
        start_i = month_start(point_year, point_month)
        next_year_i, next_month_i = shift_month(point_year, point_month, 1)
        end_i = month_start(next_year_i, next_month_i)
        point["month_plans"] = sum(1 for p in trend_month_plans if p.deadline and start_i <= p.deadline < end_i)
        point["week_plans"] = sum(1 for p in trend_week_plans if p.deadline and start_i <= p.deadline < end_i)

    hours_per_day = [entry["planned_hours"] for entry in daily.values()]
    total_hours = sum(hours_per_day)
    mean_hours = total_hours / day_count if day_count else 0
    stddev_hours = sqrt(sum((hours - mean_hours) ** 2 for hours in hours_per_day) / day_count) if day_count else 0
    busiest_day = max(daily.items(), key=lambda item: (item[1]["planned_hours"], item[1]["schedule_count"])) if selected_schedules else None
    linked_count = sum(1 for schedule in selected_schedules if schedule.week_plan_id is not None)

    return {
        "year": year,
        "month": month,
        "month_plans": {
            "total": len(month_plans),
            "items": [{"id": p.id, "title": p.title, "deadline": p.deadline} for p in month_plans],
        },
        "week_plans": {
            "total": len(week_plans),
            "items": [{"id": p.id, "title": p.title, "deadline": p.deadline} for p in week_plans],
        },
        "schedules": {
            "total": len(selected_schedules),
            "items": [{
                "id": s.id,
                "title": s.title,
                "date": s.date,
                "week_plan_id": s.week_plan_id,
                "start_time": s.start_time,
                "end_time": s.end_time,
            } for s in selected_schedules],
        },
        "planned_hours": round(total_hours, 2),
        "linked_schedule_ratio": round(linked_count / len(selected_schedules) * 100, 1) if selected_schedules else 0,
        "busiest_day": {
            "date": busiest_day[0],
            "schedule_count": busiest_day[1]["schedule_count"],
            "planned_hours": round(busiest_day[1]["planned_hours"], 2),
        } if busiest_day else None,
        "daily_mean_hours": round(mean_hours, 2),
        "daily_stddev_hours": round(stddev_hours, 2),
        "daily_load": [{"date": day, **values, "planned_hours": round(values["planned_hours"], 2)} for day, values in daily.items()],
        "trend": trend,
    }
