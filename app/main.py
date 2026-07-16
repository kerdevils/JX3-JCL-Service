import asyncio
import os
import tempfile
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.convert import JclConvertError, VALID_TARGET_LEVELS
from app.models import ConvertResponse, ErrorDetail
from app.process_runner import ConversionTimedOut, run_conversion_in_subprocess

MAX_FILE_SIZE = 50 * 1024 * 1024
ALLOWED_EXTENSIONS = {".jcl", ".txt"}
_conversion_slots = asyncio.Semaphore(2)
CONVERSION_TIMEOUT_SECONDS = 90

STATIC_DIR = Path(__file__).parent / "static"


def _validate_before_read(filename: str) -> None:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File extension {suffix!r} not allowed. Allowed: {ALLOWED_EXTENSIONS}",
        )


app = FastAPI(
    title="无方 JCL 转换服务",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.environ.get(
            "JX3_JCL_ALLOWED_ORIGINS", "http://localhost:3000"
        ).split(",")
        if origin.strip()
    ],
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


async def _read_upload(upload: UploadFile, filename: str) -> bytes:
    chunks = []
    total = 0
    while True:
        chunk = await upload.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum size of {MAX_FILE_SIZE // (1024 * 1024)} MiB.",
            )
        chunks.append(chunk)
    _validate_content(filename, total)
    return b"".join(chunks)


@app.post(
    "/v1/jcl/convert",
    response_model=ConvertResponse,
    responses={
        413: {"model": ErrorDetail},
        429: {"model": ErrorDetail},
        504: {"model": ErrorDetail},
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

    content = await _read_upload(file, filename)

    if target_level not in VALID_TARGET_LEVELS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid target_level={target_level}. Supported: {sorted(VALID_TARGET_LEVELS)}",
        )

    if max_time is not None and max_time <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="max_time must be greater than zero.",
        )
    tmp_path = os.path.join(
        tempfile.gettempdir(), f"jx3-jcl-{uuid.uuid4().hex}.jcl"
    )
    result_path = os.path.join(
        tempfile.gettempdir(), f"jx3-jcl-{uuid.uuid4().hex}.json"
    )
    try:
        with open(tmp_path, "wb") as f:
            f.write(content)

        acquired = False
        try:
            try:
                await asyncio.wait_for(_conversion_slots.acquire(), timeout=1)
                acquired = True
            except asyncio.TimeoutError as exc:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many conversions are running. Please retry shortly.",
                ) from exc

            try:
                conversion_task = asyncio.create_task(
                    asyncio.to_thread(
                        run_conversion_in_subprocess,
                        tmp_path,
                        result_path,
                        player_id,
                        target_level,
                        max_time,
                        CONVERSION_TIMEOUT_SECONDS,
                    )
                )
                try:
                    result = await asyncio.shield(conversion_task)
                except asyncio.CancelledError:
                    await conversion_task
                    raise
            except ConversionTimedOut as exc:
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail="JCL conversion timed out.",
                ) from exc
            except JclConvertError as exc:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=str(exc),
                ) from exc
        finally:
            if acquired:
                _conversion_slots.release()
        return result
    finally:
        for path in (tmp_path, result_path):
            try:
                os.unlink(path)
            except OSError:
                pass


@app.get("/v1/health")
async def health():
    return {"status": "ok"}
