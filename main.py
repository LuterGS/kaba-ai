import os

from fastapi import FastAPI
from dotenv import load_dotenv
from openai.lib.azure import AzureOpenAI
from fastapi.middleware.cors import CORSMiddleware

from feature.ai_chat import AiChat
from feature.character_map import CharacterMap
from feature.picture_diary import PictureDiary
from feature.recap_geneator import RecapGenerator

load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "").strip(),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("OPENAI_API_VERSION")
)

endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "").strip()
search_endpoint = os.getenv('AZURE_AI_SEARCH_ENDPOINT')
search_key = os.getenv("AZURE_AI_SEARCH_API_KEY")
search_index = os.getenv("AZURE_AI_SEARCH_INDEX")

deployment_name = os.getenv('DEPLOYMENT_NAME')  # gpt-4o

character_map = CharacterMap(client, deployment_name)
picture_diary = PictureDiary(client, deployment_name)
ai_chat = AiChat(client, deployment_name, endpoint, search_endpoint, search_key, search_index)
recap_generator = RecapGenerator(client, deployment_name)

app = FastAPI()

origins = [
    "https://kaba.team",
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/")
async def test():
    return "hello world!"


@app.get("/character-map/{book_id}")
async def get_character_map(book_id: int, end_page: int | None = None):
    start_page = 1
    if end_page is None:
        end_page = start_page + 1
    print(start_page, end_page)
    return character_map.get_relation_map(start_page, end_page, book_id)


@app.get("/diary-img-url/{book_id}")
async def get_diary_img_url(book_id: int, sentence: str | None = None):
    if sentence is None:
        return "not found!"
    else:
        return picture_diary.gen_diary_img_url(book_id=book_id, fav_sent=sentence, flag_use_book_nm=False)


@app.get("/ai-chat/{book_id}")
async def get_ai_chat(book_id: int, character: str | None = None, question: str | None = None):
    if character is None:
        character = "주인공"
    if question is None:
        question = "나에 대해 알려줘"
    return ai_chat.get_ai_character_chat_fast(book_id, character, question)


@app.get("/recap-generator/{book_id}")
async def get_recap_generator(book_id: int, end_page: int | None = None, img_style: str | None = None):
    if end_page is None:
        end_page = 3
    return recap_generator.get_summary_plot_img(book_id, 1, end_page, img_style)

