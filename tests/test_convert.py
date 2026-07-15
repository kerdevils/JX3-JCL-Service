import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.convert import VALID_TARGET_LEVELS, JclConvertError, convert_jcl

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
TEST_JCL = os.path.join(FIXTURES_DIR, "TEST.jcl")


class TestConvertJcl:
    def test_converts_test_fixture(self):
        result = convert_jcl(TEST_JCL, target_level=134)

        assert "player" in result
        assert result["player"]["kungfuId"] == 10627
        assert result["player"]["kungfuName"] == "无方"
        assert result["player"]["name"] != "无方"
        assert "battle" in result
        assert result["battle"]["startFrame"] >= 0
        assert result["battle"]["endFrame"] > result["battle"]["startFrame"]
        assert "data" in result
        assert len(result["data"]) > 0
        assert "diagnostics" in result
        assert "unknownSkillIds" in result["diagnostics"]
        assert "unknownBuffIds" in result["diagnostics"]
        assert "unknownTalentIds" in result["diagnostics"]

    def test_finds_wufang_player_automatically(self):
        result = convert_jcl(TEST_JCL, target_level=134)
        pid = result["player"]["id"]
        assert pid != ""
        assert result["player"]["kungfuId"] == 10627

    def test_rejects_invalid_target_level(self):
        with pytest.raises(JclConvertError, match="target_level"):
            convert_jcl(TEST_JCL, target_level=999)

    def test_accepts_all_valid_target_levels(self):
        for level in VALID_TARGET_LEVELS:
            result = convert_jcl(TEST_JCL, target_level=level)
            assert result["player"]["kungfuId"] == 10627

    def test_returns_timeline_data(self):
        result = convert_jcl(TEST_JCL, target_level=134)
        data = result["data"]
        for skill_key, statuses in data.items():
            for buff_key, detail in statuses.items():
                assert "timeline" in detail
                timeline = detail["timeline"]
                assert isinstance(timeline, list)
                for entry in timeline:
                    assert len(entry) == 3
                    assert isinstance(entry[0], int)
                    assert isinstance(entry[1], (bool, int))
                    assert isinstance(entry[2], (int, float))

    def test_no_unknown_talents_for_fixture(self):
        result = convert_jcl(TEST_JCL, target_level=134)
        unknown = result["diagnostics"].get("unknownTalentIds", [])
        assert unknown == []

    def test_throws_on_nonexistent_file(self):
        with pytest.raises(JclConvertError, match="JCL parse failed"):
            convert_jcl("/nonexistent/path.jcl", target_level=134)


class TestJclWithMaxTime:
    def test_truncates_timeline(self):
        result_full = convert_jcl(TEST_JCL, target_level=134)
        result_trunc = convert_jcl(TEST_JCL, target_level=134, max_time=4.0)

        def count_hits(r):
            return sum(
                len(detail.get("timeline", []))
                for statuses in r["data"].values()
                for detail in statuses.values()
            )

        assert count_hits(result_trunc) <= count_hits(result_full)
