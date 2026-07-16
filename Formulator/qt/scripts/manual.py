from typing import Dict

from qt.components.manual import ManualAttrWidget


def manual_script(manual_widget: ManualAttrWidget):
    """返回手动属性数据获取函数"""

    def get_manual_data():
        if manual_widget.enabled:
            return manual_widget.get_attrs()
        return {}

    return get_manual_data
