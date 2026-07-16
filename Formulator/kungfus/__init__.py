from typing import Type, Callable, Dict, List, Tuple

from base.attribute import Attribute
from base.buff import Buff
from base.dot import Dot
from base.gain import Gain
from base.recipe import Recipe
from base.skill import Skill
from general.buffs import GENERAL_BUFFS
from general.recipes import GENERAL_RECIPES
from general.skills import GENERAL_SKILLS
from kungfus import ao_xue_zhan_yi, jing_yu_jue, xiao_chen_jue, bei_ao_jue, gu_feng_jue
from kungfus import tai_xu_jian_yi, wen_shui_jue, fen_shan_jing, ling_hai_jue, yin_long_jue, shan_hai_xin_jue
from kungfus import tie_lao_lv, ming_zun_liu_li_ti, tie_gu_yi
from kungfus import yi_jin_jing, hua_jian_you, tian_luo_gui_dao, fen_ying_sheng_jue, tai_xuan_jing, zhou_tian_gong
from kungfus import zi_xia_gong, bing_xin_jue, du_jing, mo_wen, wu_fang


class Kungfu:
    attribute: Type[Attribute]
    prepare: Callable
    buffs: Dict[int, Buff]
    dots: Dict[int, Dot]
    skills: Dict[int, Skill]
    recipes: Dict[Tuple[int, int], Recipe]
    talents: Dict[int, Gain]
    gains: Dict[tuple, Gain]

    talent_choices: List[List[int]]
    talent_encoder: Dict[str, tuple]
    talent_decoder: Dict[int, str]
    recipe_choices: Dict[str, Dict[str, tuple]]

    def __init__(self, kungfu_id, name, school, major, kind, formation, kungfu):
        self.kungfu_id = kungfu_id
        self.name = name
        self.school = school
        self.major = major
        self.kind = kind
        self.formation = formation

        self.attribute = kungfu.Attribute
        self.prepare = kungfu.prepare

        self.build_buffs(kungfu)
        self.build_dots(kungfu)
        self.build_skills(kungfu)
        self.build_gains(kungfu)
        self.build_talents(kungfu)
        self.build_recipes(kungfu)

    def build_buffs(self, kungfu):
        self.buffs = {**GENERAL_BUFFS}
        for buff_class, items in kungfu.BUFFS.items():
            for buff_id, attrs in items.items():
                self.buffs[buff_id] = buff = buff_class(buff_id)
                buff.set_asset(attrs)

    def build_dots(self, kungfu):
        self.dots = {}
        for dot_class, items in kungfu.DOTS.items():
            for dot_id, attrs in items.items():
                self.dots[dot_id] = dot = dot_class(dot_id)
                dot.set_asset(attrs)

    def build_skills(self, kungfu):
        self.skills = {**GENERAL_SKILLS}
        for skill_class, items in kungfu.SKILLS.items():
            for skill_id, attrs in items.items():
                self.skills[skill_id] = skill = skill_class(skill_id)
                skill.set_asset(attrs)

    def build_recipes(self, kungfu):
        self.recipes = {**GENERAL_RECIPES}
        for recipe_class, items in kungfu.RECIPES.items():
            for recipe_key, attrs in items.items():
                if not isinstance(recipe_key, tuple):
                    recipe_key = (recipe_key, 1)
                self.recipes[recipe_key] = recipe = recipe_class(*recipe_key)
                recipe.set_asset(attrs)
        self.recipe_choices = {}
        for skill, recipes in kungfu.RECIPE_CHOICES.items():
            self.recipe_choices[skill] = {}
            for name, recipe_key in recipes.items():
                if not isinstance(recipe_key, tuple):
                    recipe_key = (recipe_key, 1)
                self.recipe_choices[skill][name] = recipe_key

    def build_talents(self, kungfu):
        self.talent_choices, self.talents = [], {}
        self.talent_encoder, self.talent_decoder = {}, {}
        for talent_choices in kungfu.TALENTS:
            talent_choice = []
            self.talent_choices.append(talent_choice)
            for gain_id, gain in talent_choices.items():
                self.gains[(gain_id, 1)] = self.talents[gain_id] = gain
                self.talent_encoder[gain.gain_name] = (gain_id, 1)
                self.talent_decoder[gain_id] = gain.gain_name
                talent_choice.append(gain.gain_name)

    def build_gains(self, kungfu):
        self.gains = {**kungfu.GAINS}


SUPPORT_KUNGFU = {
    10627: Kungfu(
        10627, "无方", "药宗", "根骨", "内功", "乱暮浊茵阵", wu_fang
    ),
}
