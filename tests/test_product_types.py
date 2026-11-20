import asyncio

import pytest

from autosnab_bot.services import priceformation_reference, product_types


def test_cache_keeps_last_list_on_error(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    async def ok(group: str) -> list[str]:
        calls.append(group)
        return ['Диск'] if group == 'tire' else ['Аккумулятор']

    async def fail(_group: str) -> list[str]:
        raise RuntimeError('cli down')

    monkeypatch.setattr(product_types, '_cache', {})
    monkeypatch.setattr(priceformation_reference, 'get_product_types', ok)
    assert asyncio.run(product_types.get_product_types('tire')) == ['Диск']
    assert asyncio.run(product_types.get_product_types('tire')) == ['Диск']
    assert asyncio.run(product_types.get_product_types('akb')) == ['Аккумулятор']
    assert calls == ['tire', 'akb']
    monkeypatch.setattr(product_types, 'CACHE_TTL', 0)
    monkeypatch.setattr(priceformation_reference, 'get_product_types', fail)
    assert asyncio.run(product_types.get_product_types('tire')) == ['Диск']
