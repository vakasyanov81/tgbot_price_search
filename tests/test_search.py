from autosnab_bot.services.price_list import PriceInfo, get_instance_price_list


def search(title, search_string):
    data = {title: PriceInfo("10", "10", "1", 1)}
    _price_list = get_instance_price_list("PriceListSimple", "PriceListSearch", data)
    return _price_list.search(search_string)


def test_search():
    assert {} == search("185/60r15 bfgoodrich g-force winter 2 88t", "185 65 r15")
    assert "185/65r15 bfgoodrich g-force winter 2 88t" in search(
        "185/65r15 bfgoodrich g-force winter 2 88t", "185 65 r15"
    )
