import json
import re

from feature.db import db
from feature.pdf_reader import PdfReader
from feature.prompt import Prompter


from openai import AzureOpenAI


class RecapGenerator:
    def __init__(self, client: AzureOpenAI, deployment_name):
        self._azure_client = client
        self._deployment_name = deployment_name
        self._pdf_reader = PdfReader()

    def _summary_plot(self, book_id, start_page, end_page):
        # 소설 시작부터 현재까지 읽은 페이지 데이터 얻기
        context_book_str = self._pdf_reader.get_pdf_text(start_page, end_page, book_id)

        # keyword_system_message
        kw_sys_msg = "너의 유일한 역할은 주어진 소설 내용을 중심 사건으로 요약하는 것이다."

        # keyword prompt
        keyword_prompt = Prompter.summary_keyword_plot(context_book_str)

        # 결과
        response = self._azure_client.chat.completions.create(
            model=self._deployment_name,
            messages=[
                {"role": "system", "content": kw_sys_msg},  # system_msg
                {"role": "user", "content": keyword_prompt}  # prompt
            ],
            # response_format={"type" : "json_object"}, # 답변 형식을 json으로 저장
        )

        result = response.choices[0].message.content
        print(f'[INFO] Finish summary plot...')

        return result

    # preprocessing summary plot result
    # json.load(result) -> list 형태 일 때 전처리
    def _prep_gen_result_list_format(self, book_name, list_format):
        sent_list = []
        keyword_list = []

        # 겉은 list, 안에는 dict
        for dict_item in list_format:
            try:
                col_list = list(dict_item.keys())

                # 문장 번호가 없는 경우
                if len(col_list) == 2:
                    sent_col_idx = 0
                    keyword_col_idx = 1
                else:
                    sent_col_idx = 1
                    keyword_col_idx = 2

                # 요약 문장 추가
                sent = dict_item[col_list[sent_col_idx]]
                sent_list.append(sent)

                # keyword가 string이면 list로 변환
                keyword_obj = dict_item[col_list[keyword_col_idx]]

                if isinstance(keyword_obj, str):
                    keyword_obj = keyword_obj.split(',')
                else:
                    pass

                # bookname + '배경' + keyword
                keyword = [book_name + ' 배경'] + keyword_obj
                keyword_list.append(keyword)

            except Exception as e:
                print('list_format error: ', e)

        return sent_list, keyword_list

    # json.load(result) -> dict 형태 일 때 전처리
    def _prep_gen_result_dict_format(self, book_name, dict_format):
        sent_list = []
        keyword_list = []

        # 문장 key 정보
        sent_key_list = list(dict_format.keys())

        for sent_key in sent_key_list:
            try:
                sent_info = dict_format[sent_key]
                col_list = list(sent_info.keys())

                # 문장 번호가 없는 경우
                if len(col_list) == 2:
                    sent_col_idx = 0
                    keyword_col_idx = 1
                else:
                    sent_col_idx = 1
                    keyword_col_idx = 2

                # 요약 문장 추가
                sent = sent_info[col_list[sent_col_idx]]
                sent_list.append(sent)

                # keyword가 string이면 list로 변환
                keyword_obj = sent_info[col_list[keyword_col_idx]]

                if isinstance(keyword_obj, str):
                    keyword_obj = keyword_obj.split(',')
                else:
                    pass

                # bookname + '배경' + keyword
                keyword = [book_name + ' 배경'] + keyword_obj
                keyword_list.append(keyword)

            except Exception as e:
                print('dict format error: ', e)

        return sent_list, keyword_list

    # json.load(result) -> str 형태 일 때 전처리
    def _prep_gen_result_str_format(self, book_name, str_format):
        try:
            # 정규표현식으로 json 형태 데이터 추출
            json_objects = re.findall(r'\{\n.*?\n\}', str_format, re.DOTALL)

            # JSON 문자열을 json.loads를 통해 dict로 변환
            dict_list = [json.loads(obj) for obj in json_objects]  # dict_list 안에 있는 값들은 dict 형태를 가지게 됨

        except Exception as e:
            print('str_format json error: ', e)

        sent_list = []
        keyword_list = []

        for dict_item in dict_list:
            try:
                col_list = list(dict_item.keys())

                # 문장 번호가 없는 경우
                if len(col_list) == 2:
                    sent_col_idx = 0
                    keyword_col_idx = 1
                else:
                    sent_col_idx = 1
                    keyword_col_idx = 2

                # 요약 문장 추가
                sent = dict_item[col_list[sent_col_idx]]
                sent_list.append(sent)

                # keyword가 string이면 list로 변환
                keyword_obj = dict_item[col_list[keyword_col_idx]]

                if isinstance(keyword_obj, str):
                    keyword_obj = keyword_obj.split(',')
                else:
                    pass

                # bookname + '배경' + keyword
                keyword = [book_name + ' 배경'] + keyword_obj
                keyword_list.append(keyword)

            except Exception as e:
                print('str_format error: ', e)

        return sent_list, keyword_list

    # 비용 효율성을 올리기위해 최대한 json 형태를 정제하려 노력했다.
    def _prep_summary_result(self, result, book_name):
        # 재시도 한번만 시도
        attempt = 0
        while (attempt <= 1):
            try:
                print(f'[INFO] Start num {attempt} prep_summary_result...')
                # """json 제거
                start_idx = result.find('\n')
                end_idx = result.rfind('\n')
                prep_result = result[start_idx + 1:end_idx]  # string

                sent_list = []
                keyword_list = []
                # string 데이터가 json으로 변환
                try:
                    json_result = json.loads(prep_result)  # 겉은 list, 안에는 dict
                    # 겉은 list, 안에는 dict
                    if isinstance(json_result, list):
                        print('[INFO] _prep_gen_result_list_format...')
                        sent_list, keyword_list = self._prep_gen_result_list_format(book_name, json_result)
                        break
                    # 겉은 dict, 안에는 dict
                    elif isinstance(json_result, dict):
                        print('[INFO] _prep_gen_result_dict_format...')
                        sent_list, keyword_list = self._prep_gen_result_dict_format(book_name, json_result)
                        break
                    else:
                        # 함수 다시 호출...
                        print('#' * 30)
                        print('Unknown error...')
                        print(json_result)
                        attempt += 1

                except Exception as e2:
                    # 형태 오류, 정규표현식으로 가져오기
                    try:
                        print('[INFO] _prep_gen_result_str_format...')
                        ent_list, keyword_list = self._prep_gen_result_str_format(book_name, prep_result)
                        break
                    # 함수 다시 호출하기
                    except Exception as e3:
                        print('#' * 30)
                        print('e3 error 함수 재실행: ', e3)
                        attempt += 1

            except Exception as e1:
                print('#' * 30)
                print('e1 error 함수 재실행: ', e1)
                attempt += 1

        return sent_list, keyword_list

    def _generate_image(self, prompt, n=1, size="1024x1024"):
        try:
            response = self._azure_client.images.generate(
                model="dall-e-3",
                # 원하는 화풍???? 찾기,
                prompt=prompt,
                n=n,
                size=size,
            )
            urls = [img.url for img in response.data]
            # print(f"Generated URLs: {urls}")  # Debug print

            return urls

        except Exception as e:
            print(f"An error occurred in generate_image: {e}")

            return []

    # 지난 줄거리를 keyword로 요약한 다음 keyword 기반으로 그림 생성
    def gen_summary_img(self, sent_keyword_list, img_style):
        summary_img_url_list = []
        filter_list = ["유아", "아동", "애기", "아기", "어린이", "유소년", "유치원생", "영아", "미취학아동", "갓난아기"]

        # key값들이 변할 수 있으므로 index로 접근해야 함
        for img_idx, sent_keyword in enumerate(sent_keyword_list):

            filtered_keyword = [item for item in sent_keyword if item not in filter_list]

            # init image prompt / img_style : anime, dreamscape
            summary_img_prompt = Prompter.summary_img(img_style, ', '.join(filtered_keyword))

            # 이미지 생성
            summary_img_urls = self._generate_image(summary_img_prompt)
            summary_img_url_list.append(summary_img_urls)

            # 이미지 저장
            # save_img_by_url(summary_img_urls, img_file_path)

            print(f'[INFO] Finish generate image {img_idx}...')

        return summary_img_url_list

    # 줄거리 요약 및 이미지 얻기
    def get_summary_plot_img(self, book_id, end_page, img_style):
        start_page = db.get_page_start(book_id)
        book_name = db.get_book_name(book_id)

        try:
            # 줄거리 요약
            summary_plot_result: str = self._summary_plot(book_id, start_page, end_page)
            print("summary_plot_result: ", summary_plot_result)

            # 줄거리 요약 전처리
            sent_list, keyword_list = self._prep_summary_result(summary_plot_result, book_name)


            # 키워드 기반의 이미지 생성 (파일 저장)
            summary_img_url_list = self.gen_summary_img(keyword_list, img_style)
            print("sent_list", sent_list)
            print("keyword_list", keyword_list)
            print("summary_img_url_list", summary_img_url_list)

            result = []
            for i in range(len(sent_list)):
                result.append({
                    "id": i,
                    "sent": sent_list[i],
                    "keyword": keyword_list[i],
                    "img_url": summary_img_url_list[i]
                })
            return {"response": result}

        except Exception as e:
            print('get_summary_plot_img error: ', e)
            print(summary_plot_result)

# %%
# 줄거리 요약 및 줄거리 keyword 기반 그림 생성 (책이름, anime 기반)

# book_name = '어린 왕자'
# start_page = 4
# end_page = 22
# img_style = 'anime'  # dreamscape
#
# # 줄거리 요약 및 이미지 생성
# summary_sent_list, summary_keyword_list, summary_img_url_list = get_summary_plot_img(book_name, start_page,
#                                                                                          end_page, lp_text_list,
#                                                                                          img_style, prompt_dict)