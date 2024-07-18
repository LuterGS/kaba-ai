import os

from openai import AzureOpenAI

from feature.db import db


class AiChat:

    def __init__(self, client: AzureOpenAI, deployment_name, endpoint, search_endpoint, search_key, search_index):
        self._azure_client = client
        self._deployment_name = deployment_name
        self._endpoint = endpoint
        self._search_endpoint = search_endpoint
        self._search_key = search_key
        self._search_index = search_index
        self._embedding_model_name = "text-embedding-ada-002"


    def get_ai_character_chat_fast(self, book_id, character, user_query):
        book_name = db.get_book_name(book_id)
        system_msg = f"당신의 유일한 역할은 {book_name} 책의 {character} 역할이다. {character} 역할이라고 생각하고 질문에 답변해."
        response = self._azure_client.chat.completions.create(
            model=self._deployment_name,
            messages=[
                {
                    "role": "user",
                    "content": user_query
                }],
            max_tokens=300,  # 1200
            temperature=0,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None,
            stream=False,
            extra_body={
                "data_sources": [{
                    "type": "azure_search",
                    "parameters": {
                        "endpoint": f"{self._search_endpoint}",
                        "index_name": f"{self._search_index}",
                        "semantic_configuration": f"{self._search_index}-semantic-configuration",
                        "query_type": "vector_semantic_hybrid",
                        "fields_mapping": {
                        },
                        "in_scope": True,
                        "role_information": system_msg,  # system message
                        "filter": None,  # 필요시 최적화?
                        "strictness": 2,  # default : 3 / 값을 낮추면 더 빠른 응답을 얻을 수 있지만, 정보의 정확성이 떨어질 수 있음
                        "top_n_documents": 3,  # default : 5 / 검색 결과 개수 설정, '3'
                        "authentication": {
                            "type": "api_key",
                            "key": f"{self._search_key}"
                        },
                        "embedding_dependency": {
                            "type": "deployment_name",
                            "deployment_name": "text-embedding-ada-002"
                        }
                    }
                }]
            }
        )
        return {
            "response": response.choices[0].message.content
        }
