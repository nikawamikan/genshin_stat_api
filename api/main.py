from lib.gen_genshin_image import save_image
from model.enka_model import get_character_status, get_json, Character, get_user_data
from fastapi.responses import FileResponse
from fastapi import FastAPI
from ordered_set import OrderedSet
from lib import score_calc
import os
import glob

URL_CACHE = OrderedSet(glob.glob('build_images/*.jpeg'))
MAX_CACHE_SIZE = 1000
CALC_TYPE_MAP = {v: k for k, v in score_calc.BUILD_NAMES.items()}


def cache_append(file_path: str):
    URL_CACHE.add(file_path)
    if len(URL_CACHE) > MAX_CACHE_SIZE:
        image_path = URL_CACHE.pop(0)
        os.remove(image_path)


app = FastAPI()


@app.post("/{uid}_{create_date}_{char_name}_{build_type}_build.jpg")
async def get_build(
    uid: int,
    create_date: str,
    char_name: str,
    char_stat: Character,
    build_type: str = "atk"
):

    char_stat.set_build_type(score_calc.BUILD_NAMES[build_type])
    file_path = f"./build_images/{uid}_{create_date}_{char_name}_{build_type}.jpeg"
    if file_path not in URL_CACHE:
        save_image(file_path=file_path, character_status=char_stat)
        cache_append(file_path=file_path)
    return FileResponse(file_path)


@app.get("/build_types.json")
async def get_build_types():
    return CALC_TYPE_MAP


@app.get("/{uid}.json")
async def get_user_json(uid: int):
    json = await get_user_data(await get_json(uid))
    return json
