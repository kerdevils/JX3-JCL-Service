import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.process_runner import (
    ConversionTimedOut,
    _wait_for_process,
    run_conversion_in_subprocess,
)

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
TEST_JCL = os.path.abspath(os.path.join(FIXTURES_DIR, "TEST.jcl"))


class StuckProcess:
    def __init__(self):
        self.terminate_calls = 0
        self.kill_calls = 0
        self.join_calls = []
        self.alive_checks = 0

    def join(self, timeout=None):
        self.join_calls.append(timeout)

    def is_alive(self):
        self.alive_checks += 1
        return self.alive_checks <= 2

    def terminate(self):
        self.terminate_calls += 1

    def kill(self):
        self.kill_calls += 1


def _result_path():
    handle, path = tempfile.mkstemp(prefix="jx3-jcl-test-", suffix=".json")
    os.close(handle)
    os.unlink(path)
    return path


def test_wait_timeout_terminates_and_joins_process():
    process = StuckProcess()

    try:
        _wait_for_process(process, 0.01)
    except ConversionTimedOut as exc:
        assert "0.01 seconds" in str(exc)
    else:
        raise AssertionError("Expected ConversionTimedOut")

    assert process.terminate_calls == 1
    assert process.kill_calls == 1
    assert process.join_calls == [0.01, 5, None]


def test_real_conversion_in_subprocess():
    result_path = _result_path()
    try:
        result = run_conversion_in_subprocess(
            TEST_JCL,
            result_path,
            None,
            134,
            4.0,
            90,
        )
        assert result["battle"]["analysisSeconds"] == 4.0
        assert result["player"]["kungfuId"] == 10627
    finally:
        try:
            os.unlink(result_path)
        except OSError:
            pass


if __name__ == "__main__":
    test_wait_timeout_terminates_and_joins_process()
    test_real_conversion_in_subprocess()
    print("subprocess conversion smoke test passed")
