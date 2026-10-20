"""Справочники priceformation: каталог поставщиков и типы товара."""

from autosnab_bot.services.priceformation_cli import ERROR_TAIL, run_command, tail

GET_SUPPLIERS = 'get_supliers'
GET_PRODUCT_TYPES = 'get_product_types'


async def get_suppliers() -> dict[str, str]:
    """Каталог поставщиков: ИД → название."""
    command_result = await run_command(GET_SUPPLIERS)
    catalog = command_result.json() if command_result.ok else None
    if not isinstance(catalog, dict):
        raise RuntimeError(tail(command_result.output, ERROR_TAIL) or 'не удалось получить список поставщиков')
    return {supplier_id: entry['sup_title'] for supplier_id, entry in catalog.items()}


async def get_product_types() -> list[str]:
    """Типы товара, которые priceformation ставит в колонку «Тип товара» прайсов."""
    command_result = await run_command(GET_PRODUCT_TYPES)
    payload = command_result.json() if command_result.ok else None
    types = payload.get('types') if isinstance(payload, dict) else None
    if not isinstance(types, list):
        raise RuntimeError(tail(command_result.output, ERROR_TAIL) or 'не удалось получить типы товара')
    return [str(product_type) for product_type in types]
