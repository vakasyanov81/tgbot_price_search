import asyncio
from pathlib import Path
from typing import Any

import pytest
from telegram.error import BadRequest

from autosnab_bot.handlers import pf_menu, pf_upload
from autosnab_bot.handlers.pf_callbacks import CANCEL_UPLOAD, CHOOSE_SUPPLIER, CONFIRM_UPLOAD, SUPPLIER_PREFIX
from autosnab_bot.services import priceformation, priceformation_reference
from autosnab_bot.services.priceformation_cli import CommandResult
from autosnab_bot.services.supplier_upload import PendingUpload
from tests.fakes import FakeBot, keyboard_labels, make_context, make_document, make_update

MIM = 'Мим'

type Uploaded = tuple[str, list[bytes]]
SECOND_STATUS = 102
SUPPLIERS = {'4': MIM, '1': 'Пошк'}
PLACED = CommandResult(0, '{"ok": true, "files": ["/p/mim/price.xlsx", "/p/mim/territories.json"]}')


def press(context: Any, callback_data: str) -> None:
    asyncio.run(pf_menu.priceformation_action(make_update(callback_data=callback_data), context))


def send_file(context: Any, file_name: str, file_id: str = 'file-1') -> None:
    asyncio.run(
        pf_upload.supplier_price_upload(make_update(document=make_document(file_name, file_id=file_id)), context)
    )


@pytest.fixture
def suppliers(monkeypatch: pytest.MonkeyPatch) -> None:
    async def get_suppliers() -> dict[str, str]:
        return SUPPLIERS

    monkeypatch.setattr(priceformation_reference, 'get_suppliers', get_suppliers)


def test_choose_supplier_lists_sorted(suppliers: None) -> None:
    context = make_context()
    press(context, CHOOSE_SUPPLIER)
    assert keyboard_labels(context.bot.sent[0]) == [MIM, 'Пошк', 'Отмена']


def test_choose_supplier_cli_error(monkeypatch: pytest.MonkeyPatch) -> None:
    async def get_suppliers() -> dict[str, str]:
        raise RuntimeError('нет uv')

    monkeypatch.setattr(priceformation_reference, 'get_suppliers', get_suppliers)
    context = make_context()
    press(context, CHOOSE_SUPPLIER)
    assert context.bot.texts == ['Не удалось получить список поставщиков:\n<pre>нет uv</pre>']


def test_collect_files_and_upload(suppliers: None, monkeypatch: pytest.MonkeyPatch) -> None:
    uploaded: list[Uploaded] = []

    async def load_supplier_prices(supplier_id: str, sources: list[Path]) -> CommandResult:
        uploaded.append((supplier_id, [path.read_bytes() for path in sources]))
        return PLACED

    monkeypatch.setattr(priceformation, 'load_supplier_prices', load_supplier_prices)
    bot = FakeBot()
    bot.files = {'a': b'price', 'b': b'[]'}
    context = make_context(bot=bot)
    press(context, CHOOSE_SUPPLIER)
    press(context, f'{SUPPLIER_PREFIX}4')
    send_file(context, 'Прайс МИМ.xlsx', 'a')
    send_file(context, 'list.csv')
    send_file(context, 'territories.json', 'b')
    press(context, CONFIRM_UPLOAD)

    assert uploaded == [('4', [b'price', b'[]'])]
    assert bot.edited[-1]['text'] == f'Поставщик «{MIM}», файлов: 2\n• Прайс МИМ.xlsx\n• territories.json'
    assert bot.texts[-1] == f'Файлы поставщика «{MIM}» загружены:\n• price.xlsx\n• territories.json'
    assert pf_upload.PENDING_UPLOAD not in context.user_data


def test_status_message_resent_when_not_editable() -> None:
    pending = {pf_upload.PENDING_UPLOAD: PendingUpload('4', MIM)}
    context = make_context(pending, FakeBot(edit_error=BadRequest('gone')))
    send_file(context, 'a.xlsx')
    send_file(context, 'b.xlsx')
    assert len(context.bot.sent) == 2
    assert context.user_data[pf_upload.PENDING_UPLOAD].status_message_id == SECOND_STATUS


def test_document_without_pending_supplier_gets_hint() -> None:
    context = make_context()
    send_file(context, 'price.xlsx')
    assert context.bot.texts == ['Чтобы загрузить прайс поставщика, выберите его: /pf']


def test_stale_supplier_list_and_cancel(suppliers: None) -> None:
    context = make_context()
    press(context, f'{SUPPLIER_PREFIX}4')
    press(context, CHOOSE_SUPPLIER)
    press(context, f'{SUPPLIER_PREFIX}4')
    press(context, CANCEL_UPLOAD)
    assert context.bot.texts[0] == 'Список поставщиков устарел, откройте его заново через /pf'
    assert context.bot.texts[-1] == 'Загрузка прайса отменена'
    assert context.user_data == {}


def test_upload_without_files() -> None:
    context = make_context({pf_upload.PENDING_UPLOAD: PendingUpload('4', MIM)})
    press(context, CONFIRM_UPLOAD)
    assert context.bot.texts == ['Нет файлов для загрузки, выберите поставщика заново через /pf']
