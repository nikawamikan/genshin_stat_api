from decimal import Decimal
import aiohttp
from lib import score_calc
from model.yaml_models import get_jp_character_models, get_jp_names
from pydantic import BaseModel
from decimal import Decimal
import re


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


async def get_json(uid: int) -> dict:
    url = f"https://enka.network/api/uid/{uid}"
    async with aiohttp.ClientSession(raise_for_status=True) as session:
        async with session.get(url) as response:
            resp = await response.json()
    return resp


def pop_character_data(json: list, id: int) -> dict:
    try:
        # アバターインフォリストを回す。nにキャラ情報がすべて入る。
        # もしキャラクター情報が公開されていない、表示できない場合はFileNotFoundErrorでraiseする。
        for n in json['avatarInfoList']:
            if n["avatarId"] == int(id):
                chara = n
                break
            else:
                continue
    except:
        raise KeyError()
    return chara


def get_suffix(name: str):
    if PERCENT_PATTERN.search(name):
        return "%"
    return ""


def get_score(value: Decimal, name: str, type: str):
    pass


class ArtifactStatus(BaseModel):
    value: Decimal
    score: Decimal
    name: str
    suffix: str

    def get_status(self):
        return f"{self.value}{self.suffix}"


class Artifact(BaseModel):
    name: str
    icon: str
    main_name: str
    main_value: str
    level: int
    status: list[ArtifactStatus]
    score: Decimal
    artifact_set_name: str
    star: int


class Weapon(BaseModel):
    name: str
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
    build_type: str

    def get_dir(self):
        if self.name == "旅人":
            return f"{self.name}/{self.element}"
        return self.name


async def get_charcter_status(uid: str):
    json = await get_json(uid)


def get_artifact(json: dict, build_type: str):
    flat = json["flat"]
    name = flat["icon"]
    icon = f'https://enka.network/ui/{flat["icon"]}.png'
    main_name = NAME_HASH[flat["reliquaryMainstat"]["mainPropId"]]
    main_value = str(flat["reliquaryMainstat"]["statValue"])
    level = json["reliquary"]["level"] - 1
    artifact_set_name = NAME_HASH[flat["setNameTextMapHash"]]
    star = flat["rankLevel"]
    status = [
        ArtifactStatus(
            value=round(Decimal(v["statValue"]), 1),
            name=NAME_HASH[v["appendPropId"]],
            score=score_calc.calc(
                NAME_HASH[v["appendPropId"]],
                v["statValue"],
                build_type
            ),
            suffix=get_suffix(NAME_HASH[v["appendPropId"]]),
        ) for v in flat["reliquarySubstats"]
    ]
    print(flat["reliquarySubstats"])
    return Artifact(
        name=name,
        icon=icon,
        main_name=main_name,
        star=star,
        main_value=main_value,
        level=level,
        artifact_set_name=artifact_set_name,
        status=status,
        score=round(sum([v.score for v in status]), 1)
    )


def get_artifacts(json: list[dict], build_type: str) -> dict[str, Artifact]:
    return {
        v["flat"]["equipType"]: get_artifact(v, build_type)
        for v in json
    }


def get_weapon(json: dict):
    flat = json["flat"]
    name = NAME_HASH[flat["nameTextMapHash"]]
    icon = f'https://enka.network/ui/{flat["icon"]}.png'
    main_name = NAME_HASH[flat["weaponStats"][0]["appendPropId"]]
    main_value = flat["weaponStats"][0]["statValue"]
    sub_name = NAME_HASH[flat["weaponStats"][1]["appendPropId"]]
    sub_value = flat["weaponStats"][0]["statValue"]
    level = json["weapon"]["level"] - 1
    rank = flat["rankLevel"]
    print(main_name, main_value, sub_name, sub_value, level, rank)
    return Weapon(
        name=name,
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


def get_elemental_name_value(json: dict):

    elemental_list = []
    fuga = None
    elemental_name = None
    elemental_value = None
    # とりあえず1以上の値がダメージバフ
    for n, fuga in ELEMENT_DAMAGE_TYPES.items():
        if round(json["fightPropMap"][n]*100) > 0:
            elemental_list.append(round(json["fightPropMap"][n]*100))
            elemental_name = fuga
            elemental_value = f'{str(round(json["fightPropMap"][n]*100 , 1))}%'

    # もし0以外が2以上あったら（1以上のダメージバフが複数あったら）
    if len([x for x in elemental_list if x != 0]) >= 2:
        elemental_list = [x for x in elemental_list if x != 0]
        reverse_dict = {v: k for k, v in ELEMENT_DAMAGE_TYPES.items()}
        # 数値が同じ場合はそのキャラの元素のダメージバフを表示
        if len(set(elemental_list)) != len(elemental_list):
            elemental_name = CHARACTER[json["avatarId"]].element
            elemental_value = f'{str(round(json["fightPropMap"][reverse_dict.get(elemental_name)]*100 , 1))}%'
        # 数値が同じじゃなかったら最も高いダメージバフを表示
        else:
            max_value = max(elemental_list)
            max_value_index = elemental_list.index(max_value)
            ELEMENT_list = [{k: v} for k, v in reverse_dict.items()]
            n = str(
                "".join([v for k, v in ELEMENT_list[max_value_index].items()]))
            elemental_name = ELEMENT_DAMAGE_TYPES[n]
            elemental_value = f'{str(round(json["fightPropMap"][n]*100 , 1))}%'

    return (elemental_name, elemental_value)


async def get_character_status(json: dict, build_type: str):
    id = str(json["avatarId"])
    name = CHARACTER[id].name
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

    elemental_name, elemental_value = get_elemental_name_value(json)
    skills = get_skills(
        id,
        json["skillLevelMap"],
        json["proudSkillExtraLevelMap"] if "proudSkillExtraLevelMap" in json else {}
    )
    artifacts = get_artifacts(json["equipList"][:-1], build_type)
    weapon = get_weapon(json["equipList"][-1])
    return Character(
        id=id,
        name=name,
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
        build_type=build_type
    )
