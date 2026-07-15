import logging
import os
import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.convert import JclConvertError, VALID_TARGET_LEVELS, convert_jcl
from app.models import ConvertResponse, ErrorDetail

MAX_FILE_SIZE = 50 * 1024 * 1024
ALLOWED_EXTENSIONS = {".jcl", ".txt"}
_executor = ThreadPoolExecutor(max_workers=2)
logger = logging.getLogger("jx3_jcl_service")

STATIC_DIR = Path(__file__).parent / "static"


def _validate_before_read(filename: str) -> None:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File extension {suffix!r} not allowed. Allowed: {ALLOWED_EXTENSIONS}",
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    _executor.shutdown(wait=True)


app = FastAPI(
    title="无方 JCL 转换服务",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def index():
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return HTMLResponse(index_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>JX3 JCL Service</h1><p>Frontend not found.</p>")


@app.get("/v1/jcl/export")
async def jcl_export(request: Request):
    return FileResponse(
        STATIC_DIR / "index.html",
        media_type="text/html",
    )


def _validate_content(filename: str, size: int) -> None:
    if size == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File is empty.",
        )
    if size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {MAX_FILE_SIZE // (1024 * 1024)} MiB.",
        )


def _run_convert(
    tmp_path: str,
    player_id: str,
    target_level: int,
    max_time: float,
) -> dict:
    try:
        return convert_jcl(
            file_path=tmp_path,
            player_id=player_id,
            target_id="",
            target_level=target_level,
            max_time=max_time,
        )
    except JclConvertError:
        raise
    except Exception as exc:
        logger.exception("Unexpected error during JCL conversion")
        raise JclConvertError("Internal conversion error. Check server logs.") from exc


@app.post(
    "/v1/jcl/convert",
    response_model=ConvertResponse,
    responses={
        413: {"model": ErrorDetail},
        415: {"model": ErrorDetail},
        422: {"model": ErrorDetail},
    },
)
async def jcl_convert(
    file: UploadFile = File(...),
    max_time: float = Form(None),
    player_id: str = Form(None),
    target_level: int = Form(134),
):
    filename = file.filename or "upload.jcl"
    _validate_before_read(filename)

    content = await file.read()
    _validate_content(filename, len(content))

    if target_level not in VALID_TARGET_LEVELS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid target_level={target_level}. Supported: {sorted(VALID_TARGET_LEVELS)}",
        )

    tmp_path = os.path.join(
        tempfile.gettempdir(), f"jx3-jcl-{uuid.uuid4().hex}.jcl"
    )
    try:
        with open(tmp_path, "wb") as f:
            f.write(content)

        loop = __import__("asyncio").get_event_loop()
        try:
            result = await loop.run_in_executor(
                _executor,
                _run_convert,
                tmp_path,
                player_id,
                target_level,
                max_time,
            )
        except JclConvertError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc
        return result
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


@app.get("/v1/health")
async def health():
    return {"status": "ok"}
