import pytest

from autosnab_bot.services import validate_user


@pytest.mark.parametrize(
    ("allowed", "user_id", "expected"),
    [
        (frozenset(), 1, False),
        (frozenset({1, 2}), 1, True),
        (frozenset({1, 2}), 3, False),
    ],
)
def test_check_rights(monkeypatch, allowed, user_id, expected):
    monkeypatch.setattr(validate_user, "ALLOWED_USER_IDS", allowed)
    assert validate_user.check_rights(user_id) is expected


def test_parse_allow_list_ignores_blank_items():
    assert validate_user._parse_allow_list("1, 2,,") == frozenset({1, 2})
    assert validate_user._parse_allow_list("") == frozenset()
