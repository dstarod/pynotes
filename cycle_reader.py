from datetime import date, timedelta
from itertools import cycle
from collections import namedtuple

Book = namedtuple('Book', ['id', 'name', 'chapters_count', 'chapters_per_day'])

lib = [
    Book('10', 'First', 21, 2),
    Book('02', 'Second', 12, 3),
    Book('03', 'Thurd', 14, 3),
    Book('11', 'Fours', 13, 1),
]

STARTED_AT = date(2017, 1, 1)

def reading_days(book):
    return sum([
        (book.chapters_count//book.chapters_per_day),
        int(bool(book.chapters_count%book.chapters_per_day))
    ])

def chapter_blocks(book):
    book_reading_days = reading_days(book)
    chapters = list(range(1, book.chapters_count+1))
    return [
        chapters[book.chapters_per_day*day:book.chapters_per_day*(day+1)]
        for day in range(book_reading_days)
    ]

def read_today(today, started=STARTED_AT, skipped=0):
    lib_days = sum(map(reading_days, lib))
    reading_day = (today-started).days + lib_days - skipped
    lib_position = reading_day - (reading_day//lib_days)*lib_days
    for book in cycle(lib):
        book_reading_days = reading_days(book)
        lib_position = lib_position-book_reading_days
        if lib_position >= 0:
            continue
        chapters_per_days = chapter_blocks(book)
        return (book.name, chapters_per_days[lib_position])

started = date.today()
for i in range(20):
    print(read_today(started+timedelta(days=i)))