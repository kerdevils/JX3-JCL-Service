import json
import multiprocessing
import os
from typing import Optional

from app.convert import JclConvertError, convert_jcl


class ConversionTimedOut(Exception):
    pass


def _write_conversion_result(
    input_path: str,
    result_path: str,
    player_id: Optional[str],
    target_level: int,
    max_time: Optional[float],
) -> None:
    try:
        result = convert_jcl(
            file_path=input_path,
            player_id=player_id,
            target_id="",
            target_level=target_level,
            max_time=max_time,
        )
        payload = {"ok": True, "result": result}
    except JclConvertError as exc:
        payload = {"ok": False, "message": str(exc)}
    except Exception:
        payload = {
            "ok": False,
            "message": "Internal conversion error. Check server logs.",
        }

    with open(result_path, "w", encoding="utf-8") as output:
        json.dump(payload, output, ensure_ascii=False)


def _stop_process(process: multiprocessing.Process) -> None:
    process.terminate()
    process.join(5)
    if process.is_alive():
        process.kill()
        process.join()


def _wait_for_process(
    process: multiprocessing.Process, timeout_seconds: float
) -> None:
    process.join(timeout_seconds)
    if process.is_alive():
        _stop_process(process)
        raise ConversionTimedOut(
            f"JCL conversion exceeded {timeout_seconds} seconds."
        )


def run_conversion_in_subprocess(
    input_path: str,
    result_path: str,
    player_id: Optional[str],
    target_level: int,
    max_time: Optional[float],
    timeout_seconds: float,
) -> dict:
    context = multiprocessing.get_context("spawn")
    process = context.Process(
        target=_write_conversion_result,
        args=(input_path, result_path, player_id, target_level, max_time),
        daemon=False,
    )
    process.start()
    _wait_for_process(process, timeout_seconds)

    if process.exitcode != 0 or not os.path.exists(result_path):
        raise JclConvertError("Internal conversion error. Check server logs.")

    try:
        with open(result_path, encoding="utf-8") as result_file:
            payload = json.load(result_file)
    except (OSError, ValueError) as exc:
        raise JclConvertError(
            "Internal conversion error. Check server logs."
        ) from exc

    if payload.get("ok"):
        return payload["result"]
    raise JclConvertError(payload.get("message") or "JCL conversion failed.")
