from pydantic import BaseModel


class ShowAvatarInfo(BaseModel):
    avatarId: str
    level: int
    costumeId: str = None


class Playerinfo(BaseModel):
    nickname: str
    level: int
    signature: str
    worldLevel: int
    nameCardId: str
    finishAchievementNum: int
    towerFloorIndex: int
    towerLevelIndex: int
    showAvatarInfoList: list[ShowAvatarInfo]
    showNameCardIdList: list[str]
    profilePicture: dict[str, str]


class AvatarInfo(BaseModel):
    avatarId: str
    propMap: dict[str, dict[str, str]]
    fightPropMap: dict[str, str]
    skillDepotId: str
    inherentProudSkillList: list[str]
    skillLevelMap: dict[str, str]
