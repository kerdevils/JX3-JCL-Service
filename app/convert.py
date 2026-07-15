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

_WUFANG_LEVEL_NORMALIZE: Dict[int, Dict[int, int]] = {
    32841: {3: 2},
}

# These are activation/control records, not damage skills. The parser cannot
# turn them into output data, and their related buffs are tracked separately.
_INTERNAL_SKILL_IDS = frozenset({
    22169, 38578, 38934, 38944, 38945, 38950, 38984, 38985,
    39088, 40790, 40793, 40803,
})
_ONLINE_OWNED_BUFF_IDS = frozenset({15436})


def _get_normalized_level(skill_id: int, formulator_level: int) -> int:
    mapping = _WUFANG_LEVEL_NORMALIZE.get(skill_id, {})
    if mapping:
        return mapping.get(formulator_level, formulator_level)
    return 1


def _normalize_damage_display(display: str) -> str:
    paren_idx = display.rfind("(")
    if paren_idx != -1 and "#" in display[:paren_idx]:
        dot_part = display[:paren_idx]
        rest = display[paren_idx + 1:].rstrip(")")
        dot_name, dot_info = dot_part.split("#", 1)
        dot_id_str, dot_level_str, dot_rest = dot_info.split("-", 2)
        dot_id = int(dot_id_str)
        dot_level = int(dot_level_str)
        new_dot_level = _get_normalized_level(dot_id, dot_level)
        dot_key = f"{dot_name}#{dot_id}-{new_dot_level}-{dot_rest}"

        if "|" in rest:
            src_part, consume_part = rest.split("|", 1)
        else:
            src_part = rest
            consume_part = None

        src_name, src_info = src_part.split("#", 1)
        src_id_str, src_level_str, src_rest = src_info.split("-", 2)
        src_id = int(src_id_str)
        src_level = int(src_level_str)
        new_src_level = _get_normalized_level(src_id, src_level)
        src_key = f"{src_name}#{src_id}-{new_src_level}-{src_rest}"

        if consume_part:
            cons_name, cons_info = consume_part.split("#", 1)
            cons_id_str, cons_level_str, cons_rest = cons_info.split("-", 2)
            cons_id = int(cons_id_str)
            cons_level = int(cons_level_str)
            new_cons_level = _get_normalized_level(cons_id, cons_level)
            cons_key = f"{cons_name}#{cons_id}-{new_cons_level}-{cons_rest}"
            return f"{dot_key}({src_key}|{cons_key})"
        return f"{dot_key}({src_key})"

    name, info = display.split("#", 1)
    parts = info.split("-")
    skill_id = int(parts[0])
    level = int(parts[1]) if len(parts) > 1 else 1
    new_level = _get_normalized_level(skill_id, level)
    if new_level == 1:
        return f"{name}#{skill_id}"
    return f"{name}#{skill_id}-{new_level}"


def _normalize_status_display(display: str) -> str:
    """Remove buffs that JX3ONLINE already models as equipment attributes."""
    sections = []
    for section in display.split("|"):
        tokens = []
        for token in section.split(",") if section else []:
            try:
                buff_id = int(token.rsplit("#", 1)[1].split("-", 1)[0])
            except (IndexError, ValueError):
                tokens.append(token)
                continue
            if buff_id not in _ONLINE_OWNED_BUFF_IDS:
                tokens.append(token)
        sections.append(",".join(tokens))
    return "|".join(sections)


def _merge_status_detail(existing: dict, incoming: dict) -> None:
    old_count = existing["expected_count"]
    incoming_count = incoming["expected_count"]
    total_count = old_count + incoming_count
    existing["timeline"] += incoming["timeline"]
    if total_count:
        for field in (
            "hit_damage",
            "critical_damage",
            "critical_strike",
            "expected_damage",
        ):
            existing[field] = (
                existing[field] * old_count + incoming[field] * incoming_count
            ) / total_count
    existing["expected_count"] = total_count
    for key, value in incoming["gradients"].items():
        existing["gradients"][key] += value


def _copy_detail(detail) -> dict:
    detail_vars = vars(detail)
    copied = dict(detail_vars)
    copied["timeline"] = list(detail_vars["timeline"])
    copied["gradients"] = dict(detail_vars["gradients"])
    return copied


def _apply_paoyang(file_path: str, parser, player_id: str, target_id: str):
    paoyang_frames: Set[int] = set()
    try:
        lines = open(file_path, encoding="gbk").readlines()
    except UnicodeDecodeError:
        lines = open(file_path, encoding="utf-8").readlines()
    from utils.lua import parse_lua
    for line in lines:
        row = line.split("\t")
        if row[4] == "13":
            detail = parse_lua(row[-1])
            if detail[4] == 20718 and detail[5] == 0:
                paoyang_frames.add(int(row[1]) - parser.start_frame)

    if not paoyang_frames:
        return

    record = parser.records[player_id][target_id]
    for damage_tuple in list(record.keys()):
        if damage_tuple[0][0] != 28081:
            continue
        statuses = record[damage_tuple]
        new_statuses = {}
        for status_tuple, timeline in list(statuses.items()):
            pao_timeline = []
            rest_timeline = []
            for entry in timeline:
                nearby = any(pf - 2 <= entry[0] <= pf for pf in paoyang_frames)
                if nearby:
                    pao_timeline.append(entry)
                else:
                    rest_timeline.append(entry)
            if pao_timeline:
                current, snapshot, target_env = status_tuple
                pao_current = current
                if not any(buff_id == 20718 for buff_id, *_ in current):
                    pao_current = tuple(sorted(
                        list(current) + [(20718, 1, 1)],
                        key=lambda x: abs(x[0])
                    ))
                pao_status = (pao_current, snapshot, target_env)
                new_statuses[pao_status] = new_statuses.get(pao_status, []) + pao_timeline
            if rest_timeline:
                new_statuses.setdefault(status_tuple, []).extend(rest_timeline)
        if new_statuses:
            record[damage_tuple] = new_statuses


class JclConvertError(Exception):
    pass


class _DiagnosticsCollector:
    def __init__(self):
        self.unknown_skill_ids: Set[int] = set()
        self.unknown_buff_ids: Set[int] = set()
        self.unknown_talent_ids: Set[int] = set()


def _patch_parser_for_diagnostics(parser, collector: _DiagnosticsCollector):
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
        target_id, react = detail[1], detail[2]
        if target_id not in parser.id2name or react:
            return original_parse_damage(row)
        damage_id = detail[4]
        player = parser.players[player_id]
        actual_damage = detail[8].get(12, 0)
        if (
            actual_damage
            and damage_id not in player.skills
            and damage_id not in player.dots
            and damage_id not in _INTERNAL_SKILL_IDS
        ):
            collector.unknown_skill_ids.add(int(damage_id))
        return original_parse_damage(row)

    original_parse_buff = parser.parse_buff

    def patched_parse_buff(row):
        return original_parse_buff(row)

    parser.parse_damage = patched_parse_damage
    parser.parse_buff = patched_parse_buff


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

    diagnostics = _DiagnosticsCollector()

    parser = Parser()
    _patch_parser_for_diagnostics(parser, diagnostics)

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

    used_buff_ids: Set[int] = set()
    for damage_tuple, statuses in parser.records.get(player_id, {}).get(target_id, {}).items():
        for status_tuple in statuses:
            for section in status_tuple:
                for buff_id, *_ in section:
                    used_buff_ids.add(buff_id)
    for buff_id in used_buff_ids:
        if buff_id in selected_player.buffs:
            selected_player.buffs[buff_id].activate = True

    talent_ids = parser.select_talents.get(player_id, [])

    if 28458 in talent_ids and 20718 in selected_player.buffs:
        selected_player.buffs[20718].activate = True
        _apply_paoyang(file_path, parser, player_id, target_id)

    if target_id not in parser.records.get(player_id, {}):
        available_targets = list(parser.records.get(player_id, {}).keys())
        raise JclConvertError(
            f"Target {target_id!r} not found for player {player_id!r}. "
            f"Available targets: {available_targets}"
        )

    end_time = max_time if max_time is not None else parser.duration
    record = parser.records[player_id][target_id]

    analyzer = Analyzer(
        kungfu=selected_player,
        target_level=target_level,
        start_time=min_time,
        end_time=end_time,
        record=record,
    )

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
        result: Dict[str, dict] = {}
        for damage_display, statuses in analyzer.details.items():
            norm_key = _normalize_damage_display(damage_display)
            # Analyzer's empty key is an aggregate. Keep it only when it is
            # the sole status; otherwise it would duplicate every timeline.
            status_items = [
                (status_display, detail)
                for status_display, detail in statuses.items()
                if status_display or not any(statuses)
            ]
            output_statuses = result.setdefault(norm_key, {})
            for status_display, detail in status_items:
                norm_status = _normalize_status_display(status_display)
                detail_vars = _copy_detail(detail)
                if norm_status in output_statuses:
                    _merge_status_detail(output_statuses[norm_status], detail_vars)
                else:
                    output_statuses[norm_status] = detail_vars
    finally:
        analyzer.sub_gains()
        analyzer.sub_recipes()

    unknown_skill_ids = sorted(
        diagnostics.unknown_skill_ids
        | {
            int(sid)
            for sid in not_support_gains
            if sid.lstrip("-").isdigit()
        }
    )
    unknown_buff_ids = sorted(diagnostics.unknown_buff_ids)

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
