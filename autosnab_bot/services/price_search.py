import html

from autosnab_bot.services.price_list import price_data


class PriceListSearch:
    def __init__(self, data_loader) -> None:
        self.is_loaded = bool(data_loader.load_price())
        self.price_list: price_data = data_loader.get_price_list()

    def search(self, search_string: str, search_limit: int = 50) -> price_data:
        """Поиск по названию позиции в прайсе"""
        return self.strict_search(search_string, search_limit) or self.no_accurate_search(search_string, search_limit)

    def strict_search(self, search_string: str, search_limit: int = 50) -> price_data:
        """Строгий поиск по точному вхождению"""
        search_string = search_string.lower()
        result: price_data = {}
        for title, prices in self.price_list.items():
            if search_string in title:
                result[title] = prices
                if len(result) >= search_limit:
                    break
        return result

    def no_accurate_search(self, search_string: str, search_limit: int = 50) -> price_data:
        """Не строгий поиск"""
        search_chunks = search_string.lower().split()
        result: price_data = {}
        if len(search_chunks) <= 1:
            return result

        for title, prices in self.price_list.items():
            if all(chunk in title for chunk in search_chunks):
                result[title] = prices
                if len(result) >= search_limit:
                    break
        return result


def prepare_search_result(source: price_data) -> str:
    # добавить сортировку по цене, сначала дешевые.
    lines = []
    for row, (title, prices) in enumerate(source.items(), start=1):
        price = html.escape(try_to_int(prices[0].price))
        rest = html.escape(try_to_int(prices[0].rest))
        lines.append(f"{row}. {html.escape(title)} - {price}Руб. {rest} шт.")
    return "\n".join(lines)


def try_to_int(val: str) -> str:
    try:
        return str(int(float(val)))
    except ValueError, OverflowError:
        return val
