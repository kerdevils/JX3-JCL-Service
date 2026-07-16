from base.gain import Gain
from general.gains.equipment import EQUIPMENT_GAINS

GAINS = {
    (801,): Gain(),
    (2760,): Gain(),
    (1952,): Gain(),
    **EQUIPMENT_GAINS,
}
