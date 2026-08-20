from dataclasses import dataclass
from .file_extractor import Section

@dataclass
class Chunk:
    file_name: str
    index: int
    page: int | None
    section: int | None
    size: int
    text: str

# Change chunker character-based to token-based
def chunker(provider: Section, chunk_size=512, overlap=32):
    for bucket in provider:
        index = 0
        offset = 0

        while offset < len(bucket.text):
            start = offset - (overlap if offset > overlap else 0)
            end = offset + chunk_size

            chunk = bucket.text[start : end]

            yield Chunk(
                file_name=bucket.file_name,
                index=index,
                page=bucket.page,
                section=bucket.section,
                size=len(chunk),
                text=chunk
            )

            index += 1
            offset += chunk_size
