import pdfplumber

from feature.db import db


class PdfReader:
    def __init__(self):
        # web client 필요
        self.id = 1

    def _get_pdf_text(self, pdf_path, is_subpage):
        pdf_text_list = []

        with pdfplumber.open(pdf_path) as pdf:
            # PDF 페이지 수
            num_pages = len(pdf.pages)

            # 각 페이지의 텍스트 추출
            for page_num in range(num_pages):
                page = pdf.pages[page_num]
                # sub page 존재
                if is_subpage == True:
                    # subpage 판단
                    left = page.crop((0, 0, 0.5 * page.width, 0.9 * page.height))
                    right = page.crop((0.5 * page.width, 0, page.width, page.height))

                    l_text = left.extract_text()
                    r_text = right.extract_text()

                    # subpage 내용 합치기
                    text = l_text + " " + r_text
                # sub page 없음
                else:
                    text = page.extract_text()

                pdf_text_list.append(text)

        print("test2!!!!!!!!!!!!!!!")
        print(pdf_text_list)
        return pdf_text_list, num_pages

    def _slice_pdf_page(self, start, end, pdf_text_list):
        # 첫 idx 보정
        if start == 0:
            start = 1

        slice_pdf_str = ''

        try:
            for idx in range(start - 1, end):
                slice_pdf_str = slice_pdf_str + '\n\n' + pdf_text_list[idx]
        except Exception as e:
            print('e:', e)
            pass

        # slice string 보정
        mod_slice_pdf_str = [x for x in slice_pdf_str.split('\n') if len(x) > 0]
        mod_slice_pdf_str = ' '.join(mod_slice_pdf_str)

        return mod_slice_pdf_str

    def get_pdf_text(self, start, end, book_id) -> str:
        # TODO : Azure container 에서 다운로드한 후 넘길 수 있도록 변경
        pdf_path = db.get_pdf_location(book_id)
        all_text_list, num_pages = self._get_pdf_text(pdf_path, True)
        return self._slice_pdf_page(start, end, all_text_list)

