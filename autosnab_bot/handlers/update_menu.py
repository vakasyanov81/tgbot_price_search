import html

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from autosnab_bot.handlers.vendor_menu import VENDORS_CALLBACK
from autosnab_bot.services.log_export import build_logs_archive
from autosnab_bot.services.response import send_document, send_response
from autosnab_bot.services.system_update import StepResult, restart_service, update_code
from autosnab_bot.services.validate_user import validate_admin, validate_user

UPDATE_CALLBACK = 'script_update'
LOGS_CALLBACK = 'script_logs'
MENU = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton('Обновить систему', callback_data=UPDATE_CALLBACK)],
        [InlineKeyboardButton('Выгрузить логи', callback_data=LOGS_CALLBACK)],
        [InlineKeyboardButton('Поставщики', callback_data=VENDORS_CALLBACK)],
    ]
)
# Telegram режет сообщение на 4096 символах; хвост вывода важнее начала — там ошибка.
MAX_OUTPUT = 3000


@validate_user
@validate_admin
async def script_manager(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_response(update, context, response='Управление ботом:', keyboard=MENU)


@validate_user
@validate_admin
async def update_system(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return
    await query.answer()
    await send_response(update, context, response='Обновляю код и субмодули…')
    outcomes = await update_code()
    await send_response(update, context, response=_report(outcomes))
    if all(outcome.ok for outcome in outcomes):
        await _restart(update, context)


@validate_user
@validate_admin
async def export_logs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return
    await query.answer()
    await send_response(update, context, response='Собираю логи…')
    archive = await build_logs_archive()
    try:
        await send_document(update, context, archive)
    finally:
        archive.unlink(missing_ok=True)


async def _restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_response(update, context, response='Перезапускаю сервис…')
    outcome = await restart_service()
    await send_response(update, context, response=_report([outcome]))


def _report(outcomes: list[StepResult]) -> str:
    blocks: list[str] = []
    for outcome in outcomes:
        status = 'OK' if outcome.ok else 'ОШИБКА'
        blocks.append(f'<b>{status}</b> <code>{html.escape(outcome.command)}</code>')
        output = html.escape(outcome.output[-MAX_OUTPUT:])
        if output:
            blocks.append(f'<pre>{output}</pre>')
    return '\n'.join(blocks)
