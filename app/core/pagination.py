import os

PAGE_SIZE = int(os.getenv("DMARKI_PAGE_SIZE", "20"))

class Paginator:
    def __init__(self, total: int, page_size: int = PAGE_SIZE):
        self.total = total
        self.page_size = page_size
        self.pages = max(1, (total + page_size - 1) // page_size)
        self.page = 1

    def range(self):
        start = (self.page - 1) * self.page_size
        end = start + self.page_size
        return start, end

    def next(self):
        if self.page < self.pages: self.page += 1

    def prev(self):
        if self.page > 1: self.page -= 1

    def goto(self, p: int):
        if 1 <= p <= self.pages: self.page = p
