import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.convert import (
    VALID_TARGET_LEVELS,
    JclConvertError,
    _merge_status_detail,
    _normalize_status_display,
    convert_jcl,
)

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

    def test_tracks_wind_and_qigu_for_jigen(self):
        result = convert_jcl(TEST_JCL, target_level=134)
        jigen_key = next(
            key
            for key in result["data"]
            if key.split("#", 1)[1].split("-", 1)[0] == "29674"
        )
        statuses = result["data"][jigen_key]

        assert "" not in statuses
        assert sum(len(detail["timeline"]) for detail in statuses.values()) == 134
        assert sum(
            len(detail["timeline"])
            for status, detail in statuses.items()
            if "#29268-20-1" in status
        ) == 42
        assert sum(
            len(detail["timeline"])
            for status, detail in statuses.items()
            if "#29268-20-1" in status and "#20696-1-1" in status
        ) == 32
        assert sum(
            len(detail["timeline"])
            for status, detail in statuses.items()
            if "#20680-1-1" in status and "#20699-1-1" in status
        ) == 134
        assert sum(
            len(detail["timeline"])
            for status, detail in statuses.items()
            if all(buff_id in status for buff_id in (
                "#20680-1-1", "#20696-1-1", "#20699-1-1", "#29268-20-1"
            ))
        ) == 32

    def test_suppresses_filtered_fixture_diagnostics(self):
        result = convert_jcl(TEST_JCL, target_level=134)
        assert result["diagnostics"] == {
            "unknownSkillIds": [],
            "unknownBuffIds": [],
            "unknownTalentIds": [],
        }

    def test_strips_online_owned_hat_enchant_from_exported_statuses(self):
        result = convert_jcl(TEST_JCL, target_level=134)
        statuses = [
            status
            for skill_statuses in result["data"].values()
            for status in skill_statuses
        ]
        assert all("#15436-" not in status for status in statuses)
        assert sum(
            len(detail["timeline"])
            for skill_statuses in result["data"].values()
            for detail in skill_statuses.values()
        ) == 648


def test_normalized_status_collision_merges_details():
    assert _normalize_status_display("大附魔帽#15436-17-1,养荣#20699-1-1||") == "养荣#20699-1-1||"

    existing = {
        "timeline": [[1, False, 100]],
        "expected_count": 1,
        "hit_damage": 100.0,
        "critical_damage": 200.0,
        "critical_strike": 0.2,
        "expected_damage": 120.0,
        "gradients": {"overcome": 2.0},
    }
    incoming = {
        "timeline": [[2, True, 200], [3, False, 150]],
        "expected_count": 2,
        "hit_damage": 160.0,
        "critical_damage": 260.0,
        "critical_strike": 0.4,
        "expected_damage": 200.0,
        "gradients": {"overcome": 5.0},
    }

    _merge_status_detail(existing, incoming)

    assert existing["timeline"] == [[1, False, 100], [2, True, 200], [3, False, 150]]
    assert existing["expected_count"] == 3
    assert existing["hit_damage"] == 140.0
    assert existing["critical_damage"] == 240.0
    assert existing["critical_strike"] == pytest.approx(1 / 3)
    assert existing["expected_damage"] == pytest.approx(520 / 3)
    assert existing["gradients"] == {"overcome": 7.0}

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
