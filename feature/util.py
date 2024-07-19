import re


class UtilFunctions:

    @staticmethod
    def remove_doc_tags(text):
        # 정규 표현식 패턴 정의: [doc숫자] 형식
        pattern1 = r'\[doc\d+\]'
        # 정규 표현식 패턴 정의: 연속된 하나 이상의 스페이스
        pattern2 = r'\s+'
        # 패턴에 매칭되는 부분을 빈 문자열로 대체
        cleaned_text = re.sub(pattern1, '', text)
        # 스페이스 여러 개 들어간 것 하나로 변경
        cleaned_text = re.sub(pattern2, ' ', cleaned_text)
        return cleaned_text
