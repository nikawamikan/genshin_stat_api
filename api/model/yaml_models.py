from pydantic import BaseModel
from lib.yaml_util import yaml

NAME_SUBSTR = len("UI_AvatarIcon_Side_")


class CharacterModel(BaseModel):
    Element: str
    IconName: str
    NameId: str
    sideIconName: str


class CharacterConfigModel(BaseModel):
    Element: str = None
    Consts: list[str] = None
    SkillOrder: list[str] = None
    Skills: dict[str, str] = None
    ProudMap: dict[str, str] = None
    NameTextMapHash: str = None
    QualityType: str = None


class SkillModel(BaseModel):
    icon: str
    name: str
    id: str
    proud_id: str


class JpCharacterModel(BaseModel):
    element: str
    consts: list[str]
    skills: list[SkillModel]
    name: str
    proud_map: dict[str, str]
    quality: int
    icon_url: str
    side_icon_url: str
    gacha_icon_url: str


def get_models_base(path: str, model):
    data: dict = yaml(path=path).load_yaml()
    return {
        k: model(**v) for k, v in data.items() if len(v) > 0
    }


def get_character_models() -> dict[str, CharacterModel]:
    return get_models_base("characters.yaml", CharacterModel)


def get_character_config_models() -> dict[str, CharacterConfigModel]:
    return get_models_base("characters_config.yaml", CharacterConfigModel)


def get_jp_names() -> dict[str, str]:
    data: dict = yaml(path="jp_names.yaml").load_yaml()
    return data


def get_jp_character_models():
    chara_model = get_character_models()
    config_model = get_character_config_models()
    jp_name = get_jp_names()
    return {
        k: JpCharacterModel(
            element=v.Element,
            consts=v.Consts,
            skills=[
                SkillModel(
                    icon=f"https://enka.network/ui/{v.Skills[v2]}.png",
                    name=v.Skills[v2],
                    id=v2,
                    proud_id=v.ProudMap[v2]
                )for v2 in v.SkillOrder
            ],
            name=jp_name[v.NameTextMapHash],
            icon_url=f"https://enka.network/ui/{chara_model[k].IconName}.png",
            proud_map=v.ProudMap,
            quality=5 if v.QualityType == "QUALITY_ORANGE" else 4,
            side_icon_url=f"https://enka.network/ui/{chara_model[k].sideIconName}.png",
            gacha_icon_url=f"https://enka.network/ui/UI_Gacha_AvatarImg_{chara_model[k].sideIconName[NAME_SUBSTR:]}.png"
        ) for k, v in config_model.items()
    }
