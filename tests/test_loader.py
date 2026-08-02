"""
Unit tests for the ingestion module's chunking logic.

chunk_text() is pure logic (no file I/O, no network), so it's ideal for
fast, deterministic unit tests.
"""

import pytest

from src.ingestion.loader import chunk_text


def test_short_text_produces_one_chunk():
    text = "This is a short sentence."
    chunks = chunk_text(text, chunk_size=1000, overlap=150)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_long_text_produces_multiple_chunks():
    text = "a" * 2500
    chunks = chunk_text(text, chunk_size=1000, overlap=150)
    assert len(chunks) > 1


def test_chunks_have_overlap():
    text = "abcdefghij" * 200  # 2000 characters
    chunks = chunk_text(text, chunk_size=1000, overlap=150)

    # The end of the first chunk should reappear at the start of the second
    end_of_first = chunks[0][-150:]
    start_of_second = chunks[1][:150]
    assert end_of_first == start_of_second


def test_invalid_chunk_size_raises_error():
    with pytest.raises(ValueError):
        chunk_text("some text", chunk_size=100, overlap=150)  # overlap >= chunk_size


def test_empty_text_produces_no_chunks():
    chunks = chunk_text("", chunk_size=1000, overlap=150)
    assert chunks == []