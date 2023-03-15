import pytest
from src.escp import InvalidEncodingError

from test import CommandsDefault


@pytest.fixture
def commands():
    return CommandsDefault()


@pytest.mark.parametrize('encoding,', ['cp437', 'utf-8'])
def test_encoding_independent(commands, encoding):
    assert commands.text("Hello world", encoding=encoding).buffer == b'Hello world'


def test_utf8_usa(commands):
    assert commands.text("{", encoding='utf-8').buffer == b'\x7b'


def test_utf8_french(commands):
    # should send \x7b with international character set 1 (France)
    with pytest.raises(InvalidEncodingError):
        commands.text("é", encoding='utf-8')


def test_utf8_emoji(commands):
    # Can never be encoded in cp437
    with pytest.raises(InvalidEncodingError):
        commands.text("😢", encoding='utf-8')


def test_cp437_emoji(commands):
    # Can never be encoded in cp437
    with pytest.raises(UnicodeError):
        commands.text("😢", encoding='cp437')
