from datetime import datetime, date, time
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Date, DateTime, Time, Text, ForeignKey, Enum
from app.core.database import Base
import enum


class RepeatType(str, enum.Enum):
    none = "none"
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"


class MonthPlan(Base):
    __tablename__ = "month_plans"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), comment="月计划标题")
    deadline: Mapped[date] = mapped_column(Date, nullable=True, comment="截止日期")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class WeekPlan(Base):
    __tablename__ = "week_plans"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    month_plan_id: Mapped[int] = mapped_column(
        ForeignKey("month_plans.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), comment="周计划标题")
    start_date: Mapped[date] = mapped_column(Date, nullable=True)
    deadline: Mapped[date] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class Schedule(Base):
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    week_plan_id: Mapped[int] = mapped_column(
        ForeignKey("week_plans.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), comment="日程标题")
    date: Mapped[date] = mapped_column(Date, comment="日程日期")
    start_time: Mapped[time] = mapped_column(Time, nullable=True)
    end_time: Mapped[time] = mapped_column(Time, nullable=True)
    color: Mapped[str] = mapped_column(String(20), default="blue")
    repeat_type: Mapped[RepeatType] = mapped_column(
        Enum(RepeatType), default=RepeatType.none
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), comment="项目名称")
    source: Mapped[str] = mapped_column(String(255), nullable=True, comment="项目来源")
    date: Mapped[date] = mapped_column(Date, nullable=True, comment="项目日期")
    pain: Mapped[str] = mapped_column(Text, nullable=True, comment="项目痛点")
    solution: Mapped[str] = mapped_column(Text, nullable=True, comment="解决方法")
    problem: Mapped[str] = mapped_column(Text, nullable=True, comment="遇到问题")
    tomorrow: Mapped[str] = mapped_column(Text, nullable=True, comment="明日计划")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)