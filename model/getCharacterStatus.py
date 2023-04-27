from decimal import Decimal
import aiohttp
import urllib
from model.yaml_models import get_jp_character_models
from pydantic import BaseModel


ELEMENT = {
    "Wind": "風",
    "Rock": "岩",
    "Electric": "雷",
    "Grass": "草",
    "Water": "水",
    "Fire": "炎",
    "Ice": "氷"
}


async def get_json(uid: int) -> dict:
    url = f"https://enka.network/api/uid/{uid}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                return None
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


class Artifact(BaseModel):
    main_name: str
    main_value: str
    ster: int
    image: str
    level: int
    status: list[tuple[str, str]]
    score: Decimal
    artifact_set_name: str

class Weapon(BaseModel):
    name: str
    main_name: str
    main_value: str
    sub_name: str
    sub_value: str
    image: str
    level: int
    rank: int


class Character(BaseModel):
    id: str
    name: str
    image: str
    element: str
    ster: int
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
    elemental_name: str
    elemental_value: str
    skill_list_image: list
    skill_list_level: list
    artifacts: list[Artifact]
    weapon: Weapon
    build_type: str


    def get_dir(self):
        if self.name == "旅人":
            return f"{self.name}/{self.element}"
        return self.name



def get_artifact():
    

class CharacterStatus():





    def getCharacterStatus(json: dict, id: str, build_type: str):
        """
        uidからキャラクター情報を読み取ります。
        《self.character》
        ・name キャラクター名
        """
        chara = CharacterStatus.pop_character_data(json, id)

        if id == "10000007" or id == "10000005":
            id += f"-{chara['skillDepotId']}"

        name = genshinTextHash[characters[id]["NameId"]]
        image = getCharacterPicture(name)
        element = config[str(id)]['Element']
        ster = int(words[name]["ster"])

        # 凸情報。もし6凸、または0凸だった場合は、それに対応する日本語に変換する。
        try:
            constellations = str(len(chara["talentIdList"]))
            if constellations == "6":
                constellations = "完"
            elif constellations == "0":
                constellations = "無"
        except:
            constellations = "無"

        level = str(chara["propMap"]["4001"]["val"])
        base_hp = str(round(chara["fightPropMap"]["1"]))
        added_hp = str(
            round(chara["fightPropMap"]["2000"]) - round(chara["fightPropMap"]["1"]))
        base_attack = str(round(chara["fightPropMap"]["4"]))
        added_attack = str(
            round(chara["fightPropMap"]["2001"]) - round(chara["fightPropMap"]["4"]))
        base_defense = str(round(chara["fightPropMap"]["7"]))
        added_defense = str(
            round(chara["fightPropMap"]["2002"]) - round(chara["fightPropMap"]["7"]))

        critical_rate = str(round(chara["fightPropMap"]["20"] * 100, 1))
        critical_damage = str(round(chara["fightPropMap"]["22"] * 100, 1))
        charge_efficiency = str(round(chara["fightPropMap"]["23"] * 100, 1))
        elemental_mastery = str(round(chara["fightPropMap"]["28"]))
        love = int(round(chara["fetterInfo"]["expLevel"]))

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

        elemental_list = []
        fuga = None
        elemental_name = None
        elemental_value = None
        # とりあえず1以上の値がダメージバフ
        for n, fuga in ELEMENT_DAMAGE_TYPES.items():
            if round(chara["fightPropMap"][n]*100) > 0:
                elemental_list.append(round(chara["fightPropMap"][n]*100))
                elemental_name = fuga
                elemental_value = f'{str(round(chara["fightPropMap"][n]*100 , 1))}%'

        # もし0以外が2以上あったら（1以上のダメージバフが複数あったら）
        if len([x for x in elemental_list if x != 0]) >= 2:
            elemental_list = [x for x in elemental_list if x != 0]
            reverse_dict = {v: k for k, v in ELEMENT_DAMAGE_TYPES.items()}
            # 数値が同じ場合はそのキャラの元素のダメージバフを表示
            if len(set(elemental_list)) != len(elemental_list):
                elemental_name = f"{ELEMENT[element]}元素ダメージ"
                elemental_value = f'{str(round(chara["fightPropMap"][reverse_dict.get(elemental_name)]*100 , 1))}%'
            # 数値が同じじゃなかったら最も高いダメージバフを表示
            else:
                max_value = max(elemental_list)
                max_value_index = elemental_list.index(max_value)
                ELEMENT_list = [{k: v} for k, v in reverse_dict.items()]
                n = str(
                    "".join([v for k, v in ELEMENT_list[max_value_index].items()]))
                elemental_name = ELEMENT_DAMAGE_TYPES[n]
                elemental_value = f'{str(round(chara["fightPropMap"][n]*100 , 1))}%'

        skill_list_image = []
        skill_list_level = []
        for skill in config[id]['SkillOrder']:
            skill_list_image.append(
                f"https://enka.network/ui/{config[id]['Skills'][str(skill)]}.png")
            add_level = 0
            key = str(config[id]["ProudMap"][str(skill)])
            if "proudSkillExtraLevelMap" in chara and key in chara["proudSkillExtraLevelMap"]:
                add_level = chara["proudSkillExtraLevelMap"][key]
            skill_list_level.append(
                str(chara["skillLevelMap"][str(skill)] + add_level))

        character_resalt = character(
            id,
            name,
            image,
            element,
            ster,
            constellations,
            level,
            love,
            base_hp,
            added_hp,
            base_attack,
            added_attack,
            base_defense,
            added_defense,
            critical_rate,
            critical_damage,
            charge_efficiency,
            elemental_mastery,
            elemental_name,
            elemental_value,
            skill_list_image,
            skill_list_level)

        artifact_resalt: list[artifact] = []
        weapon_image = None
        weapon_sub_name = None
        weapon_sub_value = None
        for n in chara["equipList"]:
            artifact_status = []
            if 'weapon' in n:
                # 武器アイコン追加
                weapon_image = f'https://enka.network/ui/{n["flat"]["icon"]}.png'

                hoge = 0
                for weaponData in n["flat"]["weaponStats"]:
                    hoge += 1
                    if hoge == 1:
                        weapon_main_name = genshinTextHash[weaponData["appendPropId"]]
                        weapon_main_value = str(weaponData["statValue"])
                    else:
                        weapon_sub_name = genshinTextHash[weaponData["appendPropId"]]
                        weapon_sub_value = str(weaponData["statValue"])

                weapon_name = genshinTextHash[n["flat"]["nameTextMapHash"]]

                weapon_rank = None
                try:
                    for z in n["weapon"]["affixMap"].values():
                        f = z
                    weapon_level = n["weapon"]["level"]
                    weapon_rank = str(f+1)
                except:
                    weapon_level = n["weapon"]["level"]

                weapon_resalt = weapon(
                    weapon_name,
                    weapon_main_name,
                    weapon_main_value,
                    weapon_sub_name,
                    weapon_sub_value,
                    weapon_image,
                    weapon_level,
                    weapon_rank)

            else:

                artifact_ster = n["flat"]["rankLevel"]
                artifact_image = f'https://enka.network/ui/{n["flat"]["icon"]}.png'
                artifact_main_name = genshinTextHash[n["flat"]
                                                     ["reliquaryMainstat"]["mainPropId"]]
                artifact_set_name = genshinTextHash[n["flat"]
                                                    ["setNameTextMapHash"]]
                artifact_main_value = str(
                    n["flat"]["reliquaryMainstat"]["statValue"])
                if "reliquarySubstats" in n["flat"]:
                    for b in n["flat"]["reliquarySubstats"]:
                        artifact_status.append(
                            (genshinTextHash[b["appendPropId"]], b["statValue"]))
                artifact_status_score = genshinscore.score(
                    artifact_status,
                    build_type
                )
                aritifact_level = n["reliquary"]["level"]-1

                artifact_resalt.append(
                    artifact(
                        artifact_main_name,
                        artifact_main_value,
                        artifact_ster,
                        artifact_image,
                        aritifact_level,
                        artifact_status,
                        artifact_status_score,
                        artifact_set_name,
                    ))

        return CharacterStatus(character_resalt, weapon_resalt, artifact_resalt, build_type)
