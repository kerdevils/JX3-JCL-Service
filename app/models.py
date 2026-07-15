from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class PlayerInfo(BaseModel):
    id: str
    name: str
    kungfuId: int
    kungfuName: str


class BattleInfo(BaseModel):
    startFrame: int
    endFrame: int


class Diagnostics(BaseModel):
    unknownSkillIds: List[int] = []
    unknownBuffIds: List[int] = []
    unknownTalentIds: List[int] = []


class ConvertResponse(BaseModel):
    player: PlayerInfo
    battle: BattleInfo
    data: Dict[str, Any]
    diagnostics: Diagnostics


class ErrorDetail(BaseModel):
    detail: str
