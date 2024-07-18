

class DB:

    def __init__(self):
        self._book = {
            1: "어린 왕자",
            2: "로미오와 줄리엣"
        }

        self._pdf = {
            1: './data/little_prince.pdf',
            2: './data/romeo and juliet.pdf'
        }

    def get_book_name(self, book_id):
        return self._book[book_id]

    def get_pdf_location(self, book_id):
        return self._pdf[book_id]

db = DB()