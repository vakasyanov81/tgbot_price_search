import pytest

from autosnab_bot.services.price_list import PriceInfo
from autosnab_bot.services.search_format import prepare_search_result, try_to_int
from tests.price_helpers import price_info


def test_escapes_html() -> None:
    found = {'<b>tire</b> & rim': [PriceInfo('10.0', '5', '3.0', 1)]}
    assert prepare_search_result(found) == '1. &lt;b&gt;tire&lt;/b&gt; &amp; rim - 10Руб. 3 шт.'


def test_numbers_rows_and_shows_supplier() -> None:
    kama = price_info('5000.0', supplier='Пошк')
    found = {'kama': [kama], 'nokian': [price_info('7000')]}
    assert prepare_search_result(found) == '1. kama - 5000Руб. 1 шт. (Пошк)\n2. nokian - 7000Руб. 1 шт.'


@pytest.mark.parametrize(
    ('raw_number', 'expected'),
    [
        ('inf', 'inf'),
        ('12.7', '12'),
        ('abc', 'abc'),
    ],
)
def test_try_to_int(raw_number: str, expected: str) -> None:
    assert try_to_int(raw_number) == expected
