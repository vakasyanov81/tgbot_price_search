"""Меню /script_manager → «Поставщики»: включение и выключение файлов поставщиков через CLI priceformation."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from autosnab_bot.services import priceformation_vendors
from autosnab_bot.services.priceformation_output import log_block
from autosnab_bot.services.response import send_response
from autosnab_bot.services.validate_user import validate_admin, validate_user

VENDORS_CALLBACK = 'script_vendors'
VENDOR_PREFIX = 'script_vendor:'
ENABLED_MARK = '[✅] '
DISABLED_MARK = '[ ] '


@validate_user
@validate_admin
async def show_vendors(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return
    await query.answer()
    try:
        vendors = await priceformation_vendors.get_vendors()
    except RuntimeError as exc:
        await send_response(update, context, response=f'Не удалось получить поставщиков:\n{log_block(str(exc))}')
        return
    await send_response(
        update,
        context,
        response='Поставщики (нажмите, чтобы включить или выключить):',
        keyboard=vendors_keyboard(vendors),
    )


@validate_user
@validate_admin
async def switch_vendor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None or query.data is None:
        return
    await query.answer()
    folder = query.data.removeprefix(VENDOR_PREFIX)
    try:
        vendors = await _toggle_and_list(folder)
    except RuntimeError as exc:
        await send_response(update, context, response=f'Не удалось переключить поставщика:\n{log_block(str(exc))}')
        return
    await query.edit_message_reply_markup(reply_markup=vendors_keyboard(vendors))


async def _toggle_and_list(folder: str) -> list[priceformation_vendors.Vendor]:
    await priceformation_vendors.toggle_vendor(folder)
    return await priceformation_vendors.get_vendors()


def vendors_keyboard(vendors: list[priceformation_vendors.Vendor]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(_label(vendor), callback_data=f'{VENDOR_PREFIX}{vendor.folder}')] for vendor in vendors]
    )


def _label(vendor: priceformation_vendors.Vendor) -> str:
    mark = ENABLED_MARK if vendor.enabled else DISABLED_MARK
    return f'{mark}{vendor.name}'
