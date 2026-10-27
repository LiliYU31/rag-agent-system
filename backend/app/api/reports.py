import re
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import date as dt_date
from app.core.database import get_db
from app.models import Report

router = APIRouter()

# ═══════════════════ 文件保存目录 ═══════════════════
DATA_DIR = Path(__file__).parent.parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)


# ═══════════════════ Pydantic 模型 ═══════════════════
class ReportCreate(BaseModel):
    name: str
    source: str | None = None
    date: dt_date | None = None
    pain: str | None = None
    solution: str | None = None
    problem: str | None = None
    tomorrow: str | None = None


class ReportUpdate(BaseModel):
    name: str | None = None
    source: str | None = None
    date: dt_date | None = None
    pain: str | None = None
    solution: str | None = None
    problem: str | None = None
    tomorrow: str | None = None


# ═══════════════════ 文件名与文件保存工具 ═══════════════════
def report_filename(report: Report) -> str:
    """生成日报文件名：{date}_{id}.txt"""
    date_str = report.date.isoformat() if report.date else "unknown"
    return f"{date_str}_{report.id}.txt"


def report_to_txt(report: Report) -> str:
    """Report 对象 → txt 文本"""
    lines = [
        f"项目名称：{report.name or ''}",
        f"项目来源：{report.source or ''}",
        f"项目日期：{report.date.isoformat() if report.date else ''}",
        f"项目痛点：{report.pain or ''}",
        f"解决方法：{report.solution or ''}",
        f"遇到的问题：{report.problem or ''}",
        f"明日计划：{report.tomorrow or ''}",
        "---",
    ]
    return "\n".join(lines)


def save_report_file(report: Report) -> str:
    """保存日报到 data/ 目录，返回路径"""
    filepath = DATA_DIR / report_filename(report)
    filepath.write_text(report_to_txt(report), encoding="utf-8")
    return str(filepath)


def delete_report_file(report: Report):
    """删除日报对应的 txt 文件"""
    filepath = DATA_DIR / report_filename(report)
    if filepath.exists():
        filepath.unlink()


def parse_date_from_filename(filename: str) -> dt_date | None:
    """从文件名解析日期：20260919.txt → 2026-09-19 或 2026-09-19.txt"""
    m = re.search(r"(\d{8})", filename)
    if m:
        try:
            s = m.group(1)
            return dt_date(int(s[:4]), int(s[4:6]), int(s[6:8]))
        except ValueError:
            pass
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", filename)
    if m:
        try:
            return dt_date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass
    return None


# ═══════════════════ txt 解析器 ═══════════════════
FIELD_ALIASES = {
    "项目名称": "name", "名称": "name",
    "项目来源": "source", "来源": "source",
    "项目日期": "date", "日期": "date",
    "项目痛点": "pain", "痛点": "pain",
    "解决方法": "solution", "解决办法": "solution",
    "遇到的问题": "problem", "遇到问题": "problem", "问题": "problem",
    "明日计划": "tomorrow", "计划": "tomorrow",
}

def parse_report_text(text: str) -> list[dict]:
    """解析日报文本，支持多行字段"""
    def parse_block(block: str) -> dict | None:
        report = {k: "" for k in ["name", "source", "pain", "solution", "problem", "tomorrow"]}
        current_field = None

        for line in block.split("\n"):
            stripped = line.strip()
            if not stripped:
                continue

            matched_field = None
            matched_value = ""
            for alias, field in FIELD_ALIASES.items():
                for sep in ["：", ":"]:
                    prefix = alias + sep
                    if stripped.startswith(prefix):
                        matched_field = field
                        matched_value = stripped[len(prefix):].strip()
                        break
                if matched_field:
                    break

            if matched_field:
                current_field = matched_field
                if report[matched_field]:
                    report[matched_field] += "\n" + matched_value
                else:
                    report[matched_field] = matched_value
            elif current_field:
                report[current_field] += "\n" + stripped

        return report if report.get("name") else None

    reports = []
    blocks = [b for b in text.split("---") if b.strip()]
    for block in blocks:
        parsed = parse_block(block)
        if parsed:
            reports.append(parsed)

    return reports


# ═══════════════════ 路由定义（顺序非常关键） ═══════════════════

@router.get("/reports")
async def list_reports(
    name: str | None = None,
    date: dt_date | None = None,
    date_start: dt_date | None = None,
    date_end: dt_date | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Report)
    if name:
        stmt = stmt.where(Report.name.like(f"%{name}%"))
    if date_start:
        stmt = stmt.where(Report.date >= date_start)
    if date_end:
        stmt = stmt.where(Report.date <= date_end)
    if date and not date_start and not date_end:
        stmt = stmt.where(Report.date == date)
    stmt = stmt.order_by(Report.date.desc(), Report.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/reports")
async def create_report(data: ReportCreate, db: AsyncSession = Depends(get_db)):
    report = Report(**data.model_dump())
    db.add(report)
    await db.flush()
    save_report_file(report)
    await db.commit()
    await db.refresh(report)
    return {"success": True, "data": report}


# ✅ 导入和导出是固定路径，必须放在 /{report_id} 的前面！
@router.post("/reports/import")
async def import_reports(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("gbk")

    parsed = parse_report_text(text)
    if not parsed:
        raise HTTPException(status_code=400, detail="没有解析到有效的日报内容，请检查格式")

    file_date = parse_date_from_filename(file.filename or "")
    count = 0
    for item in parsed:
        if not item.get("date") and file_date:
            item["date"] = file_date
        if not item.get("date"):
            item["date"] = dt_date.today()

        report = Report(**item)
        db.add(report)
        await db.flush()
        save_report_file(report)
        count += 1

    await db.commit()
    return {"success": True, "count": count}


@router.get("/reports/export")
async def export_reports(
    name: str | None = None,
    date: dt_date | None = None,
    date_start: dt_date | None = None,
    date_end: dt_date | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Report)
    if name:
        stmt = stmt.where(Report.name.like(f"%{name}%"))
    if date_start:
        stmt = stmt.where(Report.date >= date_start)
    if date_end:
        stmt = stmt.where(Report.date <= date_end)
    if date and not date_start and not date_end:
        stmt = stmt.where(Report.date == date)
    stmt = stmt.order_by(Report.date.desc())
    result = await db.execute(stmt)
    reports = result.scalars().all()

    lines = []
    for r in reports:
        lines.append(f"项目名称：{r.name or ''}")
        lines.append(f"项目来源：{r.source or ''}")
        lines.append(f"项目日期：{r.date.isoformat() if r.date else ''}")
        lines.append(f"项目痛点：{r.pain or ''}")
        lines.append(f"解决方法：{r.solution or ''}")
        lines.append(f"遇到的问题：{r.problem or ''}")
        lines.append(f"明日计划：{r.tomorrow or ''}")
        lines.append("---")

    content = "\n".join(lines)
    return PlainTextResponse(
        content=content,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=reports.txt"},
    )


# ✅ 下面这些是动态路径，必须放在固定路径的后面
@router.get("/reports/{report_id}")
async def get_report(report_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="日报不存在")
    return report


@router.put("/reports/{report_id}")
async def update_report(report_id: int, data: ReportUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="日报不存在")

    old_date = report.date
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(report, key, value)
    await db.flush()

    if old_date != report.date:
        old_report = Report(id=report.id, date=old_date)
        delete_report_file(old_report)

    save_report_file(report)
    await db.commit()
    await db.refresh(report)
    return {"success": True, "data": report}


@router.delete("/reports/{report_id}")
async def delete_report(report_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="日报不存在")

    delete_report_file(report)
    await db.delete(report)
    await db.commit()
    return {"success": True, "message": "已删除"}
