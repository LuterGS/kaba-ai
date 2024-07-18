import requests
from PIL import Image
from openai import AzureOpenAI

from feature.db import db
from feature.pdf_reader import PdfReader

import io

from feature.prompt import Prompter


class PictureDiary:

    def __init__(self, client: AzureOpenAI, deployment_name):
        self._azure_client = client
        self._deployment_name = deployment_name

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

    # print -> logging으로 변환?
    def _save_image(self, url, filename):
        """
        Save an image from a URL to a file

        :param url: URL of the image
        :param filename: Name of the file to save the image
        """
        try:
            # print(f"Attempting to save image from URL: {url}")  # Debug print
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception for bad status codes
            img = Image.open(io.BytesIO(response.content))
            img.save(filename)
            # print(f"Image saved successfully as {filename}")

        except requests.exceptions.RequestException as e:
            print(f"Error fetching the image: {e}")

        except Exception as e:
            print(f"Error saving the image: {e}")

    # print -> logging으로 변환?
    def _save_img_by_url(self, gen_urls, img_file_path):
        if gen_urls:
            for i, url in enumerate(gen_urls):
                if url:  # Check if URL is not empty
                    self._save_image(url, img_file_path)
                else:
                    print(f"Empty URL for image {i + 1}")
        else:
            print("No images were generated.")

    # 좋아하는 문구 기반의 이미지 파일 저장 (책 이름 사용 플래그 추가)
    def gen_diary_img_url(self, book_id, fav_sent: str, img_style: str, flag_use_book_nm):
        book_name = db.get_book_name(book_id)

        # 그림 일기 프롬프트 정의
        if flag_use_book_nm is False:
            # 책 이름 없이 그림 생성
            diary_prompt = Prompter.diary_img(fav_sent, img_style)
        else:
            # 책 이름 넣고 그림 생성
            diary_prompt = Prompter.diary_img_with_book(book_name, fav_sent, img_style)

        filter_list = ["유아", "아동", "애기", "아기", "어린이", "유소년", "유치원생", "영아", "미취학아동", "갓난아기"]
        for word in filter_list:
            diary_prompt = diary_prompt.replace(word, "")

        # 이미지 생성
        diary_img_urls = self._generate_image(diary_prompt)

        return {"urls": diary_img_urls}

        # 이미지 저장
        # self._save_img_by_url(diary_img_urls, diary_file_path)