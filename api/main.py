from lib.gen_genshin_image import get_character_image_bytes
from model.enka_model import get_character_status, pop_character_data, get_json
from fastapi.responses import Response
from fastapi import FastAPI


app = FastAPI()


@app.get("/build_image.jpg")
async def get_build(uid: int,  character_id: int, build_type: str = "攻撃力%"):
    json = await get_json(uid)
    chara_stat = await get_character_status(pop_character_data(json, character_id), build_type)
    byte_data = get_character_image_bytes(chara_stat)
    return Response(content=byte_data, media_type="image/jpg")
