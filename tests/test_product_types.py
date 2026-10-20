import asyncio

import pytest

from autosnab_bot.services import priceformation_reference, product_types


def test_cache_keeps_last_list_on_error(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    async def ok() -> list[str]:
        calls.append('ok')
        return ['Диск']

    async def fail() -> list[str]:
        raise RuntimeError('cli down')

    monkeypatch.setattr(product_types, '_cache', product_types._TypesCache())
    monkeypatch.setattr(priceformation_reference, 'get_product_types', ok)
    assert asyncio.run(product_types.get_product_types()) == ['Диск']
    assert asyncio.run(product_types.get_product_types()) == ['Диск']
    assert calls == ['ok']

    product_types._cache.loaded_at = 0
    monkeypatch.setattr(product_types, 'CACHE_TTL', 0)
    monkeypatch.setattr(priceformation_reference, 'get_product_types', fail)
    assert asyncio.run(product_types.get_product_types()) == ['Диск']
