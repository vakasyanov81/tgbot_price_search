import asyncio

import pytest

from autosnab_bot.services import validate_user
from tests.fakes import make_context, make_update

STRANGER = 7


@pytest.mark.parametrize(
    ('allowed', 'user_id', 'expected'),
    [
        (frozenset(), 1, False),
        (frozenset((1, 2)), 1, True),
        (frozenset((1, 2)), 3, False),
    ],
)
def test_check_rights(monkeypatch: pytest.MonkeyPatch, allowed: frozenset[int], user_id: int, expected: bool) -> None:
    monkeypatch.setattr(validate_user, 'ALLOWED_USER_IDS', allowed)
    assert validate_user.check_rights(user_id) is expected


def test_parse_allow_list_ignores_blank_items() -> None:
    assert validate_user._parse_allow_list('1, 2,,') == frozenset((1, 2))
    assert validate_user._parse_allow_list('') == frozenset()


def test_stranger_gets_access_denied_without_menu() -> None:
    calls: list[int] = []

    @validate_user.validate_user
    async def callback(_update: object, _context: object) -> None:
        calls.append(1)

    context = make_context()
    asyncio.run(callback(make_update('r15', user_id=STRANGER), context))

    assert calls == []
    assert f'Ваш ID - {STRANGER}' in context.bot.texts[0]
    assert context.bot.sent[0]['reply_markup'] is None
