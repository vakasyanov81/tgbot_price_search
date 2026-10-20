import asyncio
from pathlib import Path

from autosnab_bot.services.response import send_document
from tests.fakes import make_context, make_update


def test_send_document(tmp_path: Path) -> None:
    path = tmp_path / 'README.md'
    path.write_text('# readme')
    context = make_context()
    asyncio.run(send_document(make_update('/pf'), context, path))
    assert context.bot.documents == ['README.md']
