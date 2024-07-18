import json
from openai import AzureOpenAI

from feature.pdf_reader import PdfReader
from feature.prompt import Prompter


class CharacterMap:
    def __init__(self, client: AzureOpenAI, deployment_name):
        self._azure_client = client
        self._deployment_name = deployment_name
        self._pdf_reader = PdfReader()

    def get_relation_map(self, start_page, end_page, book_id):
        # 소설 시작부터 현재까지 읽은 페이지 데이터 얻기
        context_book_str = self._pdf_reader.get_pdf_text(start_page, end_page, book_id)

        # system에 들어갈 system 메시지 작성
        system_msg = "너는 10년동안 책 안에 있는 인물들로 인물 관계도를 만드는 전문가야. 지시사항에 맞게 인물 관계도를 만들어."

        # prompt 선언
        prompt = Prompter.character_map(context_book_str)

        # 결과
        response = self._azure_client.chat.completions.create(
            model=self._deployment_name,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt}
            ]
        )

        result = response.choices[0].message.content
        print(result)

        # preprocessing result
        start_idx = result.find('{')  # 맨 처음
        end_idx = result.rfind('}')  # 맨 마지막

        relation_map_dict = json.loads(result[start_idx:end_idx + 1])
        relation_map_keys = list(relation_map_dict.keys())

        main_character = relation_map_dict[relation_map_keys[0]]  # 주인공
        characters = relation_map_dict[relation_map_keys[1]]  # 등장인물
        relation_map = relation_map_dict[relation_map_keys[2]]  # 인물관계
        event = relation_map_dict[relation_map_keys[3]]  # 인물관계

        return {
            "mainCharacter": main_character,
            "characters": characters,
            "relationMap": relation_map,
            "event": event
        }

