from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QCheckBox, QGroupBox

from qt.components import ComboWithLabel, DoubleSpinWithLabel, TableWithLabel


class ManualAttrWidget(QWidget):
    """手动输入属性面板，取代装备录入"""

    # 无方/毒性内功需要的核心基础属性
    POISON_ATTRS = [
        ("vitality_base", "体质"),
        ("spirit_base", "根骨"),
        ("spunk_base", "元气"),
    ]

    DAMAGE_ATTRS = [
        ("poison_attack_power_base", "毒性攻击"),
        ("all_critical_strike_base", "全会心等级"),
        ("all_critical_power_base", "全会心效果等级"),
        ("magical_overcome_base", "内功破防等级"),
    ]

    MISC_ATTRS = [
        ("strain_base", "无双等级"),
        ("haste_base", "加速等级"),
        ("surplus_base", "破招值"),
    ]

    WEAPON_ATTRS = [
        ("weapon_damage_base", "基础武器伤害"),
        ("weapon_damage_rand", "浮动武器伤害"),
    ]

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        # 开关
        self.enable_checkbox = QCheckBox("启用手动输入属性（将覆盖装备属性）")
        layout.addWidget(self.enable_checkbox)

        # 所有 SpinBox
        self.spin_boxes = {}

        # 主属性组
        self._build_group(layout, "主属性", self.POISON_ATTRS)

        # 攻击属性组
        self._build_group(layout, "攻击与会心", self.DAMAGE_ATTRS)

        # 其他属性组
        self._build_group(layout, "其他战斗属性", self.MISC_ATTRS)

        # 武器伤害组
        self._build_group(layout, "武器伤害", self.WEAPON_ATTRS)

        layout.addStretch()

    def _build_group(self, parent_layout, title, attrs):
        group = QGroupBox(title)
        grid = QGridLayout()
        group.setLayout(grid)

        for i, (attr_key, attr_label) in enumerate(attrs):
            row, col = divmod(i, 2)
            spin = DoubleSpinWithLabel(attr_label, maximum=999999, value=0)
            self.spin_boxes[attr_key] = spin
            grid.addWidget(spin, row, col)

        parent_layout.addWidget(group)

    @property
    def enabled(self):
        return self.enable_checkbox.isChecked()

    def get_attrs(self):
        """返回手动输入的属性字典（只包含非零值）"""
        if not self.enabled:
            return {}
        return {
            key: int(spin.spin_box.value())
            for key, spin in self.spin_boxes.items()
            if spin.spin_box.value() != 0
        }
