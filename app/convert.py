import logging
import os
import sys
from typing import Dict, List, Optional, Set

_FORMULATOR_PATH = os.environ.get(
    "FORMULATOR_PATH",
    os.path.join(os.path.dirname(__file__), "..", "..", "Formulator"),
)
_FORMULATOR_PATH = os.path.abspath(_FORMULATOR_PATH)

if _FORMULATOR_PATH not in sys.path:
    sys.path.insert(0, _FORMULATOR_PATH)

logger = logging.getLogger(__name__)

VALID_TARGET_LEVELS = frozenset({131, 132, 133, 134})


class JclConvertError(Exception):
    pass


class _DiagnosticsCollector:
    def __init__(self):
        self.unknown_skill_ids: Set[int] = set()
        self.unknown_buff_ids: Set[int] = set()
        self.unknown_talent_ids: Set[int] = set()


def _patch_parser_for_diagnostics(parser):
    original_parse_damage = parser.parse_damage

    def patched_parse_damage(row):
        from utils.lua import parse_lua
        detail = parse_lua(row)
        caster_id = detail[0]
        player_id = (
            parser.pet2employer.get(caster_id, caster_id)
            if caster_id in parser.pet2employer
            else caster_id
        )
        if player_id not in parser.players:
            return
        damage_id = detail[4]
        player = parser.players[player_id]
        if damage_id not in player.skills and damage_id not in player.dots:
            _diag_collector.unknown_skill_ids.add(int(damage_id))
        return original_parse_damage(row)

    original_parse_buff = parser.parse_buff

    def patched_parse_buff(row):
        from utils.lua import parse_lua
        detail = parse_lua(row)
        caster_id = detail[0]
        player_id = (
            parser.pet2employer.get(caster_id, caster_id)
            if caster_id in parser.pet2employer
            else caster_id
        )
        if player_id not in parser.players:
            return
        buff_id = detail[4]
        if buff_id not in parser.players[player_id].buffs:
            _diag_collector.unknown_buff_ids.add(int(buff_id))
        return original_parse_buff(row)

    parser.parse_damage = patched_parse_damage
    parser.parse_buff = patched_parse_buff


_diag_collector: Optional[_DiagnosticsCollector] = None


def convert_jcl(
    file_path: str,
    player_id: Optional[str] = None,
    target_id: str = "",
    target_level: int = 134,
    max_time: Optional[float] = None,
    min_time: float = 0,
) -> dict:
    from utils.parser import Parser
    from utils.analyzer import Analyzer

    if target_level not in VALID_TARGET_LEVELS:
        raise JclConvertError(
            f"Invalid target_level={target_level}. Supported: {sorted(VALID_TARGET_LEVELS)}"
        )

    global _diag_collector
    _diag_collector = _DiagnosticsCollector()

    parser = Parser()
    _patch_parser_for_diagnostics(parser)

    try:
        parser(file_path)
    except Exception as exc:
        raise JclConvertError(f"JCL parse failed: {exc}") from exc

    if not parser.players:
        raise JclConvertError(
            "No supported player found. Only Wufang (kungfu 10627) is currently supported."
        )

    wufang_players = {
        pid: p for pid, p in parser.players.items() if p.kungfu_id == 10627
    }

    if not wufang_players and player_id is None:
        raise JclConvertError("No Wufang (10627) player found in this log.")

    if player_id is None:
        player_id = next(iter(wufang_players))
    elif player_id not in parser.players:
        available = list(wufang_players.keys())
        raise JclConvertError(
            f"Player {player_id!r} not found. Available Wufang players: {available}"
        )

    selected_player = parser.players[player_id]
    if selected_player.kungfu_id != 10627:
        player_name = parser.id2name.get(player_id, str(player_id))
        raise JclConvertError(
            f"Selected player {player_name!r} is not Wufang (kungfu={selected_player.kungfu_id}). "
            "Only Wufang is supported."
        )

    if player_id not in parser.id2name:
        raise JclConvertError(f"Player {player_id!r} has no recorded name in log.")

    parser.current_player = player_id
    parser.current_target = target_id

    if target_id not in parser.records.get(player_id, {}):
        available_targets = list(parser.records.get(player_id, {}).keys())
        raise JclConvertError(
            f"Target {target_id!r} not found for player {player_id!r}. "
            f"Available targets: {available_targets}"
        )

    end_time = max_time if max_time is not None else parser.current_stop_time
    record = parser.records[player_id][target_id]

    analyzer = Analyzer(
        kungfu=selected_player,
        target_level=target_level,
        start_time=min_time,
        end_time=end_time,
        record=record,
    )

    talent_ids = parser.select_talents.get(player_id, [])
    talent_keys = [(tid, 1) for tid in talent_ids]

    unknown_talent_ids = [
        int(tid)
        for tid in sorted(talent_ids)
        if (tid, 1) not in selected_player.gains
    ]

    valid_talent_keys = [
        key for key in talent_keys if key in selected_player.gains
    ]

    not_support_gains: List[str] = []
    try:
        not_support_gains = analyzer.add_gains(valid_talent_keys)
        analyzer.analyze_details()
        result = {
            damage_display: {
                status_display: vars(detail)
                for status_display, detail in statuses.items()
            }
            for damage_display, statuses in analyzer.details.items()
        }
    finally:
        analyzer.sub_gains()
        analyzer.sub_recipes()

    unknown_skill_ids = sorted(
        _diag_collector.unknown_skill_ids
        | {
            int(sid)
            for sid in not_support_gains
            if sid.lstrip("-").isdigit()
        }
    )
    unknown_buff_ids = sorted(_diag_collector.unknown_buff_ids)

    return {
        "player": {
            "id": str(player_id),
            "name": parser.id2name[player_id],
            "kungfuId": selected_player.kungfu_id,
            "kungfuName": selected_player.name,
        },
        "battle": {
            "startFrame": parser.start_frame,
            "endFrame": parser.end_frame,
        },
        "data": result,
        "diagnostics": {
            "unknownSkillIds": unknown_skill_ids,
            "unknownBuffIds": unknown_buff_ids,
            "unknownTalentIds": unknown_talent_ids,
        },
    }
