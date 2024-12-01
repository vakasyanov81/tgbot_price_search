class PriceListSearch:
    def __init__(self, data_loader):
        data_loader.load_price()
        self.price_list = data_loader.get_price_list()

    def search(self, search_string: str, search_limit=50):
        """Поиск по названию позиции в прайсе"""
        result = self.strict_search(
            search_string, search_limit
        ) or self.no_accurate_search(search_string, search_limit)
        return result

    def strict_search(self, search_string: str, search_limit=50):
        """Строгий поиск по точному вхождению"""
        result = dict()
        search_string = search_string.lower()
        search_count = 0

        for title, prices in self.price_list.items():
            if search_string in title:
                result[title] = prices
                search_count += 1
            if search_count >= search_limit:
                break
        return result

    def no_accurate_search(self, search_string: str, search_limit=50):
        """Не строгий поиск"""
        result = dict()
        search_string = search_string.lower()
        search_count = 0
        search_chunks = [s.strip() for s in search_string.split() if len(s.strip())]
        search_chunks_len = len(search_chunks)
        if search_chunks_len == 1:
            return result

        for title, prices in self.price_list.items():
            searched_chunk_count = 0
            for search_chunk in search_chunks:
                if search_chunk in title:
                    searched_chunk_count += 1
            if searched_chunk_count == search_chunks_len:
                result[title] = prices
                search_count += 1
            if search_count >= search_limit:
                break
        return result


def prepare_search_result(source):
    # добавить сортировку по цене, сначала дешевые.
    row = 1
    result = ""
    for title, prices in source.items():
        result = (
            result
            + f"{row}. {title} - {try_to_int(prices[0].price)}Руб. {try_to_int(prices[0].rest)} шт. \n"
        )
        row += 1
    return result


def try_to_int(val: str) -> str:
    try:
        return str(int(float(val)))
    except ValueError:
        return val
