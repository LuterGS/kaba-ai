from openai.lib.azure import AzureOpenAI

from feature.db import db
from feature.pdf_reader import PdfReader
from feature.prompt import Prompter
from feature.util import UtilFunctions


class KabaWiki:

    def __init__(self, client: AzureOpenAI, deployment_name, search_endpoint, search_key, search_index):
        self._azure_client = client
        self._deployment_name = deployment_name
        self._pdf_reader = PdfReader()
        self._search_endpoint = search_endpoint
        self._search_key = search_key
        self._search_index = search_index

    # system_msg로 책의 OO 역할을 부여한 다음, 유저 질문에 답변
    def get_wiki_context_answer(self, book_id, start_page, end_page, user_query):
        book_name = db.get_book_name(book_id)
        print(book_name)

        # # init system message
        system_msg = f"당신의 유일한 역할은 {book_name} 책을 읽은 선생님이다. 책 내용을 기반으로 질문에 답변해."
        #
        # # 소설 시작부터 현재까지 읽은 페이지 데이터
        # context_boot_str = self._pdf_reader.get_pdf_text(start_page, end_page, book_id)
        #
        # # init prompt
        # prompt = Prompter.kaba_wiki(user_query, context_boot_str)

        response = self._azure_client.chat.completions.create(
            model=self._deployment_name,
            messages=[
                {
                    "role": "user",
                    "content": user_query  # prompt
                }],
            max_tokens=1200,
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
                            # "content_fields_separator": "\n",
                            # "content_fields": None,
                            # "filepath_field": None,
                            # "title_field": "title",
                            # "url_field": None,
                            # "vector_fields": [
                            #   "text_vector"
                            # ]
                        },
                        "in_scope": True,
                        "role_information": system_msg,  # system message
                        "filter": None,
                        "strictness": 3,
                        "top_n_documents": 5,
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

        result = response.choices[0].message.content
        result = UtilFunctions.remove_doc_tags(result)
        return {"response": result}

