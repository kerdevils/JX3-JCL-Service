from typing import Dict

from base.buff import Buff

BUFFS: Dict[type, Dict[int, dict]] = {
    Buff: {
        # 通用
        21168: dict(buff_name="植物温性", continuous=True),
        # 奇穴
        20680: dict(begin_frame_shift=-2),
        20696: dict(buff_name="凄骨", interval=960),
        20718: dict(buff_name="炮阳", begin_frame_shift=-2, attributes={"all_damage_addition": 205}),
        30352: dict(buff_name="凄骨"),
        20699: dict(buff_name="养荣"),
        # 当前版本新增
        21856: dict(buff_name="荆障"),
        21610: dict(buff_name="茎蹊"),
        20707: dict(buff_name="滞眠"),
        # 通用增益映射 (从装备/附魔/特效)
        24659: dict(buff_name="应理以药"),
        21758: dict(buff_name="断肠"),
    }
}
