from autosnab_bot.services.price_list import PriceInfo, PriceListDataLoader, price_data
from autosnab_bot.services.price_search import PriceListSearch, prepare_search_result, try_to_int


class PriceListSimpleDataLoader:
    def __init__(self, items, loaded=True):
        self.price_list: price_data = items
        self.loaded = loaded

    def get_price_list(self) -> price_data:
        return self.price_list

    def load_price(self):
        return self.loaded


def get_instance(data) -> PriceListSearch:
    return PriceListSearch(PriceListSimpleDataLoader(data))


def search(title, search_string):
    _price_list = get_instance({title: [PriceInfo("10", "10", "1", 1)]})
    return _price_list.search(search_string)


def test_search():
    assert {} == search("185/60r15 bfgoodrich g-force winter 2 88t", "185 65 r15")
    assert "185/65r15 bfgoodrich g-force winter 2 88t" in search(
        "185/65r15 bfgoodrich g-force winter 2 88t", "185 65 r15"
    )


def test_prepare_search_result_escapes_html():
    result = prepare_search_result({"<b>tire</b> & rim": [PriceInfo("10.0", "5", "3.0", 1)]})
    assert result == "1. &lt;b&gt;tire&lt;/b&gt; &amp; rim - 10Руб. 3 шт."


def test_prepare_search_result_numbers_rows():
    source = {
        "first": [PriceInfo("1", "1", "1", 1)],
        "second": [PriceInfo("2", "2", "2", 2)],
    }
    assert prepare_search_result(source) == "1. first - 1Руб. 1 шт.\n2. second - 2Руб. 2 шт."


def test_try_to_int_handles_infinity():
    assert try_to_int("inf") == "inf"
    assert try_to_int("12.7") == "12"
    assert try_to_int("abc") == "abc"


def test_search_limit_is_respected():
    items = {f"tire {i}": [PriceInfo("1", "1", "1", i)] for i in range(10)}
    assert len(get_instance(items).search("tire", search_limit=3)) == 3


def test_is_loaded_reflects_loader_result():
    assert get_instance({}).is_loaded is True
    assert PriceListSearch(PriceListSimpleDataLoader({}, loaded=False)).is_loaded is False


def test_missing_price_file_is_not_loaded(tmp_path, monkeypatch):
    monkeypatch.setattr("autosnab_bot.config.UPLOAD_DIR", tmp_path)
    assert PriceListDataLoader("missing.xlsx").load_price() is False
