from platform import system
from abc import ABC, abstractmethod
from typing import override
from dataclasses import dataclass
import pymupdf

SYSTEM_SLASH = '\\' if system().lower() == 'windows' else '/'

@dataclass
class Section:
    file_name: str
    total_pages: int | None
    page: int | None
    section: int | None
    text: str

class FileExtractor(ABC):
    @abstractmethod
    def get_section(self):
        ...

class PdfExtractor(FileExtractor):
    _file = None
    _path = ''

    def __init__(self, path: str):
        self._path = path

        try:
            self._file = pymupdf.open(path)
        except Exception as err:
            raise err

    def get_info(self) -> dict:
        ...

    def get_pages(self) -> dict:
        result = []

        for page in self._file:
            result.append({
                'page': page.number + 1,
                'text': page.get_text()
            })

        return result

    @override
    def get_section(self):
        for page in self._file:
            yield Section(
                file_name=self._path.split(SYSTEM_SLASH)[-1],
                total_pages=len(self._file),
                page=page.number,
                section=None,
                text=page.get_text()
            )

class PlainTxtExtractor(FileExtractor):
    def __init__(self, path):
        self._path = path
        self._file = open(path, 'r', encoding="utf-8")

    def __del__(self):
        self._file.close()

    @override
    def get_section(self):
        section = 0
        while True:
            buffer = self._file.read(4096)
            section += 1

            if not buffer:
                break

        yield Section(
            file_name=self._path.split(SYSTEM_SLASH)[-1],
            total_pages=None,
            page=None,
            section=section,
            text=buffer
        )

class Extractor:
    @staticmethod
    def get(path: str) -> FileExtractor:
        ext = path.split('.')[-1].lower()

        match ext:
            case 'pdf':
                return PdfExtractor(path)
            case _:
                return PlainTxtExtractor(path)
