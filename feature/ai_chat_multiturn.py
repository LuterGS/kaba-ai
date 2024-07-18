import re

from openai.lib.azure import AzureOpenAI

from feature.db import db


class AICharacterChat:

    def __init__(self, client: AzureOpenAI, deployment_name, search_endpoint, search_key, search_index):
        self._azure_client = client
        self._deployment_name = deployment_name
        self._search_endpoint = search_endpoint
        self._search_key = search_key
        self._search_index = search_index
        self._messages = []
        self._base = None

    def start_conversation(self, book_id, character):
        book_name = db.get_book_name(book_id)

        # 시스템 메시지에서 특정 구문이 날라올 경우, gpt가 알고 있는 내용으로 답변해줘.
        system_msg = f"당신의 유일한 역할은 {book_name} 책의 {character} 역할이다. {character} 역할이라고 생각하고 질문에 답변해."
        self._base = {"role": "system", "content": system_msg}

    def remove_doc_tags(self, text):
        # 정규 표현식 패턴 정의: [doc숫자] 형식
        pattern1 = r'\[doc\d+\]'
        # 정규 표현식 패턴 정의: 연속된 하나 이상의 스페이스
        pattern2 = r'\s+'
        # 패턴에 매칭되는 부분을 빈 문자열로 대체
        cleaned_text = re.sub(pattern1, '', text)
        # 스페이스 여러 개 들어간 것 하나로 변경
        cleaned_text = re.sub(pattern2, ' ', cleaned_text)
        return cleaned_text

    def clear_history(self):
        self._messages = []

    def get_ai_character_chat_fast(self, user_query, temperature=0):
        self._messages.append({"role": "user", "content": user_query})

        response = self._azure_client.chat.completions.create(
            model=self._deployment_name,
            messages=self._messages,
            max_tokens=300,
            temperature=temperature,
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
                        "in_scope": True,
                        "role_information": self._base["content"],
                        "strictness": 1, # default : 3 / 값을 낮추면 더 빠른 응답을 얻을 수 있지만, 정보의 정확성이 떨어질 수 있음
                        "top_n_documents": 1, # default : 5 / 검색 결과 개수 설정, '3'
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

        response_content = response.choices[0].message.content
        response_content = self.remove_doc_tags(response_content)

        check_resp_list = ['다른 질문', '다른 대화', '이 질문은 내가 답변할 수 있는 범위를', '요청하신 정보는 제공된',
                           '제공된 문서에서', '대화에서 벗어난', '답할 수 없어']

        if any(check_resp in response_content for check_resp in check_resp_list):
            print('[INFO] Not use vector_semantic_hybrid...')
            print('Error response_content: ', response_content)
            print('')
            # 검색 결과가 없을 경우 유연한 답변 생성
            # mod_user_query = '{character}의 입장에서 {user_query}를 대답해줘.'
            response_content = self._generate_fallback_response()

        self._messages.append({"role": "assistant", "content": response_content})

        return response_content

    def _generate_fallback_response(self):

        # 기존 대화와 맥락을 바탕으로 유연한 답변을 생성
        fallback_response = self._azure_client.chat.completions.create(
            model=self._deployment_name,
            messages=[self._base] + self._messages,
            max_tokens=300,
            temperature=0.7,  # 창의적 답변을 위해 온도 조절
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None,
            stream=False
        )
        result = fallback_response.choices[0].message.content
        result = self.remove_doc_tags(result)
        return result


