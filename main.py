import os
from typing import Literal, List

from fastapi import FastAPI
from dotenv import load_dotenv
from openai.lib.azure import AzureOpenAI
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware

from feature.ai_chat import AiChat
from feature.ai_chat_multiturn import AICharacterChat
from feature.character_map import CharacterMap
from feature.kaba_wiki import KabaWiki
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
kaba_wiki = KabaWiki(client, deployment_name, search_endpoint, search_key, search_index)

book_1_little_prince = AICharacterChat(client, deployment_name, search_endpoint, search_key, search_index)
book_1_little_prince.start_conversation(1, "어린 왕자")

book_1_fox = AICharacterChat(client, deployment_name, search_endpoint, search_key, search_index)
book_1_fox.start_conversation(1, "여우")

book_1_snake = AICharacterChat(client, deployment_name, search_endpoint, search_key, search_index)
book_1_snake.start_conversation(1, "보아뱀")

book_1_star = AICharacterChat(client, deployment_name, search_endpoint, search_key, search_index)
book_1_star.start_conversation(1, "천문학자")

book_1_ceo = AICharacterChat(client, deployment_name, search_endpoint, search_key, search_index)
book_1_ceo.start_conversation(1, "사업가")

book_2_romeo = AICharacterChat(client, deployment_name, search_endpoint, search_key, search_index)
book_2_romeo.start_conversation(2, "로미오")

book_2_juliet = AICharacterChat(client, deployment_name, search_endpoint, search_key, search_index)
book_2_juliet.start_conversation(2, "줄리엣")

chatbots = {
    "어린 왕자": book_1_little_prince,
    "여우": book_1_fox,
    "보아뱀": book_1_snake,
    "천문학자": book_1_star,
    "사업가": book_1_ceo,
    "로미오": book_2_romeo,
    "줄리엣": book_2_juliet
}

app = FastAPI()

origins = [
    "https://kaba.team",
    "http://localhost:3000",
    "http://localhost"
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
    return character_map.get_relation_map(end_page, book_id)


@app.get("/diary-img-url/{book_id}")
async def get_diary_img_url(book_id: int, sentence: str | None = None, img_style: str | None = None):
    if img_style is None:
        img_style = "anime"
    if sentence is None:
        return "not found!"
    else:
        return picture_diary.gen_diary_img_url(book_id=book_id, fav_sent=sentence, img_style=img_style, flag_use_book_nm=True)


# 메시지 모델 정의
class Message(BaseModel):
    role: Literal['user', 'assistant']
    content: str


# 요청 본문 모델 정의
class Chat(BaseModel):
    character: str
    messages: List[Message]


@app.post("/ai-chat")
async def get_ai_chat(chat: Chat):
    chatbot = chatbots.get(chat.character)
    if len(chat.messages) > 10:
        chat.messages = chat.messages[-10:]
    if chatbot is None:
        return {"response": "없는 인물에 대한 채팅을 요청했습니다."}
    else:
        return {"response": chatbot.get_ai_character_chat_fast(chat.messages)}


# @app.post("/ai-chat/clear")
# async def clear_ai_chat(character: str | None = None):
#     chatbot = chatbots.get(character)
#     if chatbot is None:
#         return {"response": "not found"}
#     else:
#         chatbot.clear_history()
#         return {"response": "ok"}


@app.get("/recap-generator/{book_id}")
async def get_recap_generator(book_id: int, end_page: int | None = None, img_style: str | None = None):
    if end_page is None:
        end_page = 3
    return await recap_generator.get_summary_plot_img(book_id, end_page, img_style)


@app.get("/kaba-wiki/{book_id}")
async def get_kaba_wiki(book_id: int, sentence: str | None = None):
    return kaba_wiki.get_wiki_context_answer(book_id, 1, 1, sentence)
