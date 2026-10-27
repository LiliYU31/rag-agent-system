from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import date as dt_date, time as dt_time
from app.core.database import get_db
from app.models import MonthPlan, WeekPlan, Schedule, RepeatType

router = APIRouter()


# ═══════════════ Pydantic 请求模型 ═══════════════

class MonthPlanCreate(BaseModel):
    title: str
    deadline: dt_date | None = None


class MonthPlanUpdate(BaseModel):
    title: str | None = None
    deadline: dt_date | None = None


class WeekPlanCreate(BaseModel):
    title: str
    month_plan_id: int | None = None
    start_date: dt_date | None = None
    deadline: dt_date | None = None


class WeekPlanUpdate(BaseModel):
    title: str | None = None
    month_plan_id: int | None = None
    start_date: dt_date | None = None
    deadline: dt_date | None = None


class ScheduleCreate(BaseModel):
    title: str
    week_plan_id: int | None = None
    date: dt_date
    start_time: dt_time | None = None
    end_time: dt_time | None = None
    color: str = "blue"
    repeat_type: RepeatType = RepeatType.none


class ScheduleUpdate(BaseModel):
    title: str | None = None
    week_plan_id: int | None = None
    date: dt_date | None = None
    start_time: dt_time | None = None
    end_time: dt_time | None = None
    color: str | None = None
    repeat_type: RepeatType | None = None


# ═══════════════ 月计划 CRUD ═══════════════

@router.get("/month-plans")
async def list_month_plans(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MonthPlan).order_by(MonthPlan.deadline))
    return result.scalars().all()


@router.post("/month-plans")
async def create_month_plan(data: MonthPlanCreate, db: AsyncSession = Depends(get_db)):
    plan = MonthPlan(**data.model_dump())
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return {"success": True, "data": plan}


@router.put("/month-plans/{plan_id}")
async def update_month_plan(plan_id: int, data: MonthPlanUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MonthPlan).where(MonthPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="月计划不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(plan, key, value)
    await db.commit()
    await db.refresh(plan)
    return {"success": True, "data": plan}


@router.delete("/month-plans/{plan_id}")
async def delete_month_plan(plan_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MonthPlan).where(MonthPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="月计划不存在")
    await db.delete(plan)
    await db.commit()
    return {"success": True, "message": "已删除"}


# ═══════════════ 周计划 CRUD ═══════════════

@router.get("/week-plans")
async def list_week_plans(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WeekPlan).order_by(WeekPlan.deadline))
    return result.scalars().all()


@router.post("/week-plans")
async def create_week_plan(data: WeekPlanCreate, db: AsyncSession = Depends(get_db)):
    plan = WeekPlan(**data.model_dump())
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return {"success": True, "data": plan}


@router.put("/week-plans/{plan_id}")
async def update_week_plan(plan_id: int, data: WeekPlanUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WeekPlan).where(WeekPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="周计划不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(plan, key, value)
    await db.commit()
    await db.refresh(plan)
    return {"success": True, "data": plan}


@router.delete("/week-plans/{plan_id}")
async def delete_week_plan(plan_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WeekPlan).where(WeekPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="周计划不存在")
    await db.delete(plan)
    await db.commit()
    return {"success": True, "message": "已删除"}


# ═══════════════ 日程 CRUD ═══════════════

@router.get("/schedules")
async def list_schedules(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Schedule).order_by(Schedule.date, Schedule.start_time))
    return result.scalars().all()


@router.post("/schedules")
async def create_schedule(data: ScheduleCreate, db: AsyncSession = Depends(get_db)):
    schedule = Schedule(**data.model_dump())
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return {"success": True, "data": schedule}


@router.put("/schedules/{schedule_id}")
async def update_schedule(schedule_id: int, data: ScheduleUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=404, detail="日程不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(schedule, key, value)
    await db.commit()
    await db.refresh(schedule)
    return {"success": True, "data": schedule}


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=404, detail="日程不存在")
    await db.delete(schedule)
    await db.commit()
    return {"success": True, "message": "已删除"}