import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException

router = APIRouter()

# 文件保存目录
UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# 允许的扩展名
ALLOWED_EXTENSIONS = {'.txt', '.md', '.pdf', '.docx'}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传文档：支持 .txt / .md / .pdf / .docx"""
    try:
        # 校验扩展名
        suffix = Path(file.filename).suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件格式：{suffix}。仅支持 {', '.join(ALLOWED_EXTENSIONS)}"
            )

        # 读取内容并校验大小
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="文件超过 20MB 限制")

        # 保存
        unique_name = f"{uuid.uuid4().hex}{suffix}"
        save_path = UPLOAD_DIR / unique_name
        save_path.write_bytes(content)

        return {
            "success": True,
            "filename": file.filename,
            "saved_name": unique_name,
            "path": str(save_path),
            "size": len(content),
            "type": suffix[1:],       # 比如 "pdf"、"txt"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))