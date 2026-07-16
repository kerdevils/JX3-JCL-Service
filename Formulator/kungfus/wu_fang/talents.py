from typing import Dict, List

from base.gain import Gain

TALENTS: List[Dict[int, Gain]] = [
    {
        28458: Gain("炮阳", buff_ids=[20718]),
        28443: Gain("甘遂"),
        28415: Gain("荆障", buff_ids=[21856], skill_ids=[36068]),
        28461: Gain("连茹", skill_ids=[42444]),
    },
    {
        40194: Gain("六微", skill_ids=[40208]),
        28406: Gain("苍棘", skill_ids=[28409]),
        29503: Gain("茎蹊", buff_ids=[21610]),
        28405: Gain("岚霏"),
    },
    {
        28419: Gain("凄骨", buff_ids=[20696]),
        28375: Gain("沐息"),
        28485: Gain("南秸"),
        28370: Gain("渐苞"),
    },
    {
        38965: Gain("紫伏", skill_ids=[28434]),
        38633: Gain("汲刺", skill_ids=[38638]),
        28432: Gain("疾根"),
        42500: Gain("旋覆", skill_ids=[28737]),
    },
    {
        36067: Gain("香繁饮露"),
        44384: Gain("熟地药斗", dot_ids=[33061], skill_ids=[44392]),
        28436: Gain("滞眠", buff_ids=[20707]),
        30734: Gain("折枝", skill_ids=[30735, 32922]),
    },
    {
        28426: Gain("养荣", buff_ids=[20699]),
        28583: Gain("月煎"),
        38642: Gain("荆障连击", skill_ids=[38641]),
        28533: Gain("远跖", skill_ids=[29441]),
    },
    {
        29498: Gain("苍棘增伤"),
        28413: Gain("相使", buff_ids=[20680]),
        28420: Gain("熟地"),
        28439: Gain("鹰扬", skill_ids=[29720]),
        28365: Gain("宣通"),
        34796: Gain("落蕊"),
        28731: Gain("遇阳"),
        39661: Gain("逆势"),
        30016: Gain("景慕"),
        28402: Gain("青阳", skill_ids=[44992]),
        28376: Gain("应射"),
        30507: Gain("渌波"),
    },
]
