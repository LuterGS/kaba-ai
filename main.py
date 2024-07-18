import os

from fastapi import FastAPI
from dotenv import load_dotenv
from openai.lib.azure import AzureOpenAI

from feature.character_map import CharacterMap
from feature.picture_diary import PictureDiary

load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "").strip(),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("OPENAI_API_VERSION")
)

deployment_name = os.getenv('DEPLOYMENT_NAME')  # gpt-4o

character_map = CharacterMap(client, deployment_name)
picture_diary = PictureDiary(client, deployment_name)

app = FastAPI()


@app.get("/")
async def test():
    return "hello world!"


@app.get("/character-map/{book_name}")
async def get_character_map(book_name: str, start_page: int | None = None, end_page: int | None = None):
    if start_page is None:
        start_page = 1
    if end_page is None:
        end_page = start_page + 1
    print(start_page, end_page)
    return character_map.get_relation_map(start_page, end_page, book_name)


@app.get("/diary_img/{book_name}")
async def get_diary_img(book_name: str, sentence: str | None = None):
    if sentence is None:
        return "not found!"
    else:
        return picture_diary.gen_diary_img(book_name=book_name, fav_sent=sentence, flag_use_book_nm=False)
