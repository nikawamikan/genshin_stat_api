from decimal import Decimal
import aiohttp
from lib import score_calc
from model.yaml_models import get_jp_character_models, get_jp_names
from pydantic import BaseModel
from decimal import Decimal
import re
import datetime


def none_to_empty_char(data: dict[str, str], keys: list[str]) -> str:
    if keys[0] in data:
        if len(keys) == 1:
            return data[keys[0]]
        else:
            return none_to_empty_char(data[keys[0]], keys[1:])
    else:
        return ""


CHARACTER = get_jp_character_models()
NAME_HASH = get_jp_names()
ELEMENT = {
    "Wind": "風",
    "Rock": "岩",
    "Electric": "雷",
    "Grass": "草",
    "Water": "水",
    "Fire": "炎",
    "Ice": "氷"
}
PERCENT_PATTERN = re.compile(r"%|会心|チャ|元素ダメ")
ELEMENT_DAMAGE_TYPES = {
    "30": "物理ダメージ",
    "40": "炎元素ダメージ",
    "41": "雷元素ダメージ",
    "42": "水元素ダメージ",
    "43": "草元素ダメージ",
    "44": "風元素ダメージ",
    "45": "岩元素ダメージ",
    "46": "氷元素ダメージ"
}
ELEMENT_MAP = {
    "Fire": "40",
    "Electric": "41",
    "Water": "42",
    "Grass": "43",
    "Wind": "44",
    "Rock": "45",
    "Ice": "46",
}


def check_traveler(id: int):
    return id in ["10000007", "10000005"]


async def get_json(uid: int) -> dict:
    url = f"https://enka.network/api/uid/{uid}"
    async with aiohttp.ClientSession(raise_for_status=True) as session:
        async with session.get(url) as response:
            resp = await response.json()
    return resp


def get_suffix(name: str):
    if PERCENT_PATTERN.search(name):
        return "%"
    return ""


def get_score(value: Decimal, name: str, type: str):
    pass


class ArtifactStatus(BaseModel):
    value: Decimal
    name: str
    suffix: str

    def get_status(self):
        if self.suffix == "":
            value = int(self.value)
        else:
            value = self.value
        return f"{value}{self.suffix}"

    def get_score(self, build_type: str):
        return score_calc.calc(self.name, self.value, build_type)


class Artifact(BaseModel):
    icon_name: str
    icon: str
    main_name: str
    main_value: str
    suffix: str
    level: int
    status: list[ArtifactStatus]
    artifact_set_name: str
    star: int
    score: Decimal = 0.0

    def calc_score(self, build_type: str) -> Decimal:
        self.score = sum([status.get_score(build_type)
                         for status in self.status])

    def get_status(self):
        return f"{self.main_value}{self.suffix}"


class Weapon(BaseModel):
    name: str
    icon_name: str
    main_name: str
    main_value: str
    sub_name: str
    sub_value: str
    icon: str
    level: int
    rank: int


class Skill(BaseModel):
    name: str
    icon: str
    level: int
    add_level: int


class Character(BaseModel):
    id: str
    name: str
    english_name: str
    image: str
    element: str
    star: int
    constellations: str
    level: str
    love: int
    base_hp: str
    added_hp: str
    base_attack: str
    added_attack: str
    base_defense: str
    added_defense: str
    critical_rate: str
    critical_damage: str
    charge_efficiency: str
    elemental_mastery: str
    elemental_name: str = None
    elemental_value: str = None
    skills: list[Skill]
    artifacts: dict[str, Artifact]
    weapon: Weapon
    uid: int
    create_date: str
    build_type: str = None

    def get_dir(self):
        if self.english_name == "Player":
            return f"{self.english_name}/{self.element}"
        return self.english_name

    def set_build_type(self, build_type: str):
        self.build_type = build_type.replace(" ver2", "")
        for artifact in self.artifacts.values():
            artifact.calc_score(build_type)


class UserData(BaseModel):
    uid: int
    level: int
    signature: str
    world_level: int
    name_card_id: int
    finish_achievement_num: int
    tower_floor_index: int
    tower_level_index: int
    nickname: str
    create_date: str
    char_name_map: dict[str, int]
    characters: list[Character]


def get_characters(uid: int, create_date: str, json: dict) -> list[Character]:
    if 'avatarInfoList' in json:
        characters = [
            get_character_status(uid, create_date, v) for v in json['avatarInfoList']
        ]
    else:
        characters = []

    return characters


def get_user_data(json: dict) -> UserData:
    uid = json['uid']
    create_date = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    char_list = get_characters(uid, create_date, json)
    char_name_map = {c.name: i for i, c in enumerate(char_list)}
    return UserData(
        uid=json['uid'],
        level=json['playerInfo']['level'],
        signature=none_to_empty_char(json, ['playerInfo', 'signature']),
        world_level=json['playerInfo']['worldLevel'],
        name_card_id=json['playerInfo']['nameCardId'],
        finish_achievement_num=json['playerInfo']['finishAchievementNum'],
        tower_floor_index=json['playerInfo']['towerFloorIndex'],
        tower_level_index=json['playerInfo']['towerLevelIndex'],
        nickname=json['playerInfo']['nickname'],
        create_date=create_date,
        char_name_map=char_name_map,
        characters=char_list,
    )


def get_artifact(json: dict):
    flat = json["flat"]
    icon_name = flat["icon"]
    icon = f'https://enka.network/ui/{flat["icon"]}.png'
    main_name = NAME_HASH[flat["reliquaryMainstat"]["mainPropId"]]
    main_value = str(flat["reliquaryMainstat"]["statValue"])
    suffix = get_suffix(main_name)
    level = json["reliquary"]["level"] - 1
    artifact_set_name = NAME_HASH[flat["setNameTextMapHash"]]
    star = flat["rankLevel"]
    status = [
        ArtifactStatus(
            value=round(Decimal(v["statValue"]), 1),
            name=NAME_HASH[v["appendPropId"]],
            suffix=get_suffix(NAME_HASH[v["appendPropId"]]),
        ) for v in flat["reliquarySubstats"]
    ]
    return Artifact(
        icon_name=icon_name,
        icon=icon,
        main_name=main_name,
        star=star,
        main_value=main_value,
        suffix=suffix,
        level=level,
        artifact_set_name=artifact_set_name,
        status=status,
    )


def get_artifacts(json: list[dict]) -> dict[str, Artifact]:
    return {
        v["flat"]["equipType"]: get_artifact(v)
        for v in json
    }


def get_weapon(json: dict):
    flat = json["flat"]
    name = NAME_HASH[flat["nameTextMapHash"]]
    icon_name = flat["icon"]
    icon = f'https://enka.network/ui/{icon_name}.png'
    main_name = NAME_HASH[flat["weaponStats"][0]["appendPropId"]]
    main_value = flat["weaponStats"][0]["statValue"]
    sub_name = ""
    sub_value = ""
    if len(flat["weaponStats"]) == 2:
        sub_name = NAME_HASH[flat["weaponStats"][1]["appendPropId"]]
        sub_value = flat["weaponStats"][0]["statValue"]
    level = json["weapon"]["level"] - 1
    rank = flat["rankLevel"]
    return Weapon(
        name=name,
        icon_name=icon_name,
        icon=icon,
        main_name=main_name,
        main_value=main_value,
        sub_name=sub_name,
        sub_value=sub_value,
        level=level,
        rank=rank
    )


def get_skills(id: str, skill_levels: dict[str, int], extra_skill_levels: dict[str, int]):
    return [
        Skill(
            name=v.name,
            icon=v.icon,
            level=skill_levels[v.id],
            add_level=extra_skill_levels[v.proud_id] if v.proud_id in extra_skill_levels else 0,
        )for v in CHARACTER[id].skills
    ]


def get_constellations(chara: dict):
    try:
        constellations = str(len(chara["talentIdList"]))
        if constellations == "6":
            constellations = "完"
        elif constellations == "0":
            constellations = "無"
    except:
        constellations = "無"
    return constellations


def get_elemental_name_value(id: str, json: dict):

    elemental_name = None
    elemental_value = None

    max_value = 0
    max_key = None
    for k in ELEMENT_DAMAGE_TYPES.keys():
        if max_value < json["fightPropMap"][k]:
            max_value = json["fightPropMap"][k]
            max_key = k
    if max_key is not None:
        if max_value == json["fightPropMap"][ELEMENT_MAP[CHARACTER[id].element]]:
            elemental_name = ELEMENT_DAMAGE_TYPES[ELEMENT_MAP[CHARACTER[id].element]]
        else:
            elemental_name = ELEMENT_DAMAGE_TYPES[max_key]
        elemental_value = f"{round(max_value*100, 1)}%"

    return (elemental_name, elemental_value)


def get_character_status(uid: int, create_date: str, json: dict):
    id = str(json["avatarId"])
    if check_traveler(id):
        id = f"{id}-{json['skillDepotId']}"
    name = CHARACTER[id].name
    english_name = CHARACTER[id].english_name
    image = CHARACTER[id].gacha_icon_url
    element = CHARACTER[id].element
    star = CHARACTER[id].quality
    constellations = get_constellations(json)

    level = str(json["propMap"]["4001"]["val"])
    base_hp = str(round(json["fightPropMap"]["1"]))
    added_hp = str(
        round(json["fightPropMap"]["2000"]) - round(json["fightPropMap"]["1"]))
    base_attack = str(round(json["fightPropMap"]["4"]))
    added_attack = str(
        round(json["fightPropMap"]["2001"]) - round(json["fightPropMap"]["4"]))
    base_defense = str(round(json["fightPropMap"]["7"]))
    added_defense = str(
        round(json["fightPropMap"]["2002"]) - round(json["fightPropMap"]["7"]))
    critical_rate = str(round(json["fightPropMap"]["20"] * 100, 1))
    critical_damage = str(round(json["fightPropMap"]["22"] * 100, 1))
    charge_efficiency = str(round(json["fightPropMap"]["23"] * 100, 1))
    elemental_mastery = str(round(json["fightPropMap"]["28"]))
    love = int(round(json["fetterInfo"]["expLevel"]))

    elemental_name, elemental_value = get_elemental_name_value(id, json)
    skills = get_skills(
        id,
        json["skillLevelMap"],
        json["proudSkillExtraLevelMap"] if "proudSkillExtraLevelMap" in json else {}
    )
    artifacts = get_artifacts(json["equipList"][:-1])
    weapon = get_weapon(json["equipList"][-1])
    return Character(
        id=id,
        name=name,
        english_name=english_name,
        image=image,
        element=element,
        star=star,
        constellations=constellations,
        level=level,
        love=love,
        base_hp=base_hp,
        added_hp=added_hp,
        base_attack=base_attack,
        added_attack=added_attack,
        base_defense=base_defense,
        added_defense=added_defense,
        critical_rate=critical_rate,
        critical_damage=critical_damage,
        charge_efficiency=charge_efficiency,
        elemental_mastery=elemental_mastery,
        elemental_name=elemental_name,
        elemental_value=elemental_value,
        skills=skills,
        artifacts=artifacts,
        weapon=weapon,
        uid=uid,
        create_date=create_date
    )
