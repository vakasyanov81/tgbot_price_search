import operator

import pytest

from autosnab_bot.services.price_list import PriceInfo
from autosnab_bot.services.price_search import PriceListSearch
from tests.price_helpers import StubLoader, numbered_prices, price_info

BFGOODRICH = '185/65r15 bfgoodrich g-force winter 2 88t'
DISK = 'Диск'
KAMA = 'kama'
MANY = 100
LIMIT = 3


def make_search(titles_prices: dict[str, list[PriceInfo]], loaded: bool = True) -> PriceListSearch:
    return PriceListSearch(StubLoader(titles_prices, loaded))


def test_search_by_chunks() -> None:
    assert make_search({'185/60r15 bfgoodrich': [price_info('10')]}).search('185 65 r15') == {}
    assert BFGOODRICH in make_search({BFGOODRICH: [price_info('10')]}).search('185 65 r15')


def test_single_word_needs_exact_entry() -> None:
    assert make_search({BFGOODRICH: [price_info('10')]}).search('winter2') == {}


def test_search_limit_is_respected() -> None:
    titles_prices = {f'tire {index}': [price_info('1', index)] for index in range(MANY)}
    assert len(make_search(titles_prices).search('tire', search_limit=LIMIT)) == LIMIT


def test_is_loaded_reflects_loader_result() -> None:
    assert make_search({}).is_loaded is True
    assert make_search({}, loaded=False).is_loaded is False


def test_search_sorts_by_price_across_all_matches() -> None:
    titles_prices = numbered_prices(KAMA, MANY, operator.neg)
    titles_prices[f'{KAMA} no price'] = [price_info('')]
    search = make_search(titles_prices)

    cheapest = search.search(KAMA, search_limit=LIMIT)
    assert list(cheapest) == [f'{KAMA} 99', f'{KAMA} 98', f'{KAMA} 97']
    everything = search.search(KAMA, search_limit=None)
    assert len(everything) == MANY + 1
    assert list(everything)[-1] == f'{KAMA} no price'


def test_cheapest_row_of_title_goes_first() -> None:
    expensive = price_info('5000', 1, 'Пошк')
    cheap = price_info('4500', 2, 'Пионер')
    search = make_search({KAMA: [expensive, cheap], 'nokian': [price_info('4700')]})
    found = search.search('a')
    assert list(found) == [KAMA, 'nokian']
    assert found[KAMA][0].supplier == 'Пионер'


@pytest.mark.parametrize(
    ('product_type', 'expected'),
    [
        (None, [f'{KAMA} 185/65r15', f'{KAMA} 185/65r15 диск']),
        (DISK, [f'{KAMA} 185/65r15 диск']),
        ('Грузовая шина', []),
    ],
)
def test_search_filters_by_product_type(product_type: str | None, expected: list[str]) -> None:
    search = make_search(
        {
            f'{KAMA} 185/65r15': [price_info('1', product_type='Легковая шина')],
            f'{KAMA} 185/65r15 диск': [price_info('2', 2, product_type=DISK)],
        }
    )
    assert list(search.search(KAMA, product_type=product_type)) == expected
