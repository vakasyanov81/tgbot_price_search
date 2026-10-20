import dataclasses
import html
import json
import tempfile
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import ApplicationHandlerStop, ContextTypes

from autosnab_bot.services import priceformation
from autosnab_bot.services.response import send_document, send_response
from autosnab_bot.services.validate_user import validate_user

CALLBACK_PREFIX = "pf:"
MAKE_PRICE = CALLBACK_PREFIX + "make_price"
UPDATE_ALL = CALLBACK_PREFIX + "update_all"
SHOW_HELP = CALLBACK_PREFIX + "help"
CHOOSE_SUPPLIER = CALLBACK_PREFIX + "suppliers"
SUPPLIER_PREFIX = CALLBACK_PREFIX + "supplier:"
CANCEL_UPLOAD = CALLBACK_PREFIX + "cancel"
CONFIRM_UPLOAD = CALLBACK_PREFIX + "upload"

# Загрузка прайса поставщика, для которой собираем файлы.
PENDING_UPLOAD = "pf_pending_upload"

# Bot API отдаёт ботам файлы не больше 20 МБ.
MAX_FILE_SIZE = 20 * 1024 * 1024

# Пункты интерактивного меню CLI priceformation (без «выхода»).
MENU = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("Сформировать общий прайс по прайсам поставщиков", callback_data=MAKE_PRICE)],
        [InlineKeyboardButton("Обновить прайсы всех поставщиков (API и почта)", callback_data=UPDATE_ALL)],
        [InlineKeyboardButton("Загрузить прайс поставщика", callback_data=CHOOSE_SUPPLIER)],
        [InlineKeyboardButton("Справка (README)", callback_data=SHOW_HELP)],
    ]
)

_SUPPLIERS_CACHE = "pf_suppliers"

CANCEL_KEYBOARD = InlineKeyboardMarkup([[InlineKeyboardButton("Отмена", callback_data=CANCEL_UPLOAD)]])
UPLOAD_KEYBOARD = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton("Загрузить", callback_data=CONFIRM_UPLOAD),
            InlineKeyboardButton("Отмена", callback_data=CANCEL_UPLOAD),
        ]
    ]
)


@dataclasses.dataclass
class PendingUpload:
    supplier_id: str
    title: str
    # (file_id, имя файла) в порядке получения.
    files: list[tuple[str, str]] = dataclasses.field(default_factory=list)
    status_message_id: int | None = None


# Запас под заголовок и теги: лимит сообщения Telegram 4096 символов.
LOG_LIMIT = 3500


@validate_user
async def priceformation_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not priceformation.is_available():
        await send_response(
            update,
            context,
            response="Сабмодуль priceformation не найден. Выполните <code>git submodule update --init</code>",
        )
        return
    await send_response(update, context, response="Формирование прайсов:", keyboard=MENU)


@validate_user
async def priceformation_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return
    await query.answer()

    if query.data == SHOW_HELP:
        await send_document(update, context, priceformation.README_FILE)
        return
    if query.data == CHOOSE_SUPPLIER:
        await _choose_supplier(update, context)
        return
    if query.data == CANCEL_UPLOAD:
        _user_data(context).pop(PENDING_UPLOAD, None)
        await send_response(update, context, response="Загрузка прайса отменена")
        return
    if query.data and query.data.startswith(SUPPLIER_PREFIX):
        await _wait_supplier_price(update, context, query.data.removeprefix(SUPPLIER_PREFIX))
        return

    if priceformation.is_busy():
        await send_response(update, context, response="Уже выполняется другая команда, дождитесь её завершения")
        return

    if query.data == MAKE_PRICE:
        await _make_price(update, context)
    elif query.data == UPDATE_ALL:
        await _update_all(update, context)
    elif query.data == CONFIRM_UPLOAD:
        await _upload_supplier_files(update, context)


async def _make_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_response(update, context, response="Формирую общий прайс, это может занять несколько минут…")
    result, files = await priceformation.make_price()

    status = "Общий прайс сформирован" if result.ok else "Ошибка при формировании прайса"
    await send_response(update, context, response=f"<b>{status}</b>\n{_log(result.output)}")
    for path in files:
        await send_document(update, context, path)


async def _update_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_response(update, context, response="Обновляю прайсы поставщиков, это может занять несколько минут…")
    results = await priceformation.update_all_prices()

    lines = ["<b>Обновление прайсов поставщиков</b>"]
    for label, result in results.items():
        if result.ok:
            lines.append(f"✅ {html.escape(label)}")
        else:
            lines.append(f"❌ {html.escape(label)}: {html.escape(_error_text(result.output))}")
    await send_response(update, context, response="\n".join(lines))


async def _choose_supplier(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        suppliers = await priceformation.get_suppliers()
    except RuntimeError as exc:
        await send_response(update, context, response=f"Не удалось получить список поставщиков:\n{_log(str(exc))}")
        return
    context.bot_data[_SUPPLIERS_CACHE] = suppliers

    buttons = [
        [InlineKeyboardButton(title, callback_data=SUPPLIER_PREFIX + supplier_id)]
        for supplier_id, title in sorted(suppliers.items(), key=lambda item: item[1].lower())
    ]
    buttons.append([InlineKeyboardButton("Отмена", callback_data=CANCEL_UPLOAD)])
    await send_response(
        update,
        context,
        response="Выберите поставщика, для которого загрузить прайс:",
        keyboard=InlineKeyboardMarkup(buttons),
    )


async def _wait_supplier_price(update: Update, context: ContextTypes.DEFAULT_TYPE, supplier_id: str) -> None:
    title = context.bot_data.get(_SUPPLIERS_CACHE, {}).get(supplier_id)
    if title is None:
        await send_response(update, context, response="Список поставщиков устарел, откройте его заново через /pf")
        return
    _user_data(context)[PENDING_UPLOAD] = PendingUpload(supplier_id, title)
    await send_response(
        update,
        context,
        response=f"Пришлите файлы поставщика «{html.escape(title)}»: xls, xlsx, json или zip-архив, "
        "можно несколько. Затем нажмите «Загрузить».",
        keyboard=CANCEL_KEYBOARD,
    )


async def supplier_price_upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Файлы после выбора поставщика копятся для priceformation, а не уходят в загрузку прайса бота."""
    if PENDING_UPLOAD not in _user_data(context):
        return
    await _collect_supplier_file(update, context)
    raise ApplicationHandlerStop


@validate_user
async def _collect_supplier_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if message is None or message.document is None:
        return
    doc = message.document
    if not priceformation.is_supplier_file(doc.file_name):
        await send_response(
            update, context, response="Неверный формат файла. Подходят xls, xlsx, json или zip-архив с ними"
        )
        return
    if doc.file_size and doc.file_size > MAX_FILE_SIZE:
        await send_response(
            update, context, response=f"Файл {html.escape(doc.file_name or '')} больше 20 МБ, бот не может его скачать"
        )
        return

    pending: PendingUpload = _user_data(context)[PENDING_UPLOAD]
    pending.files.append((doc.file_id, Path(doc.file_name or "").name))
    await _show_collected(update, context, pending)


async def _show_collected(update: Update, context: ContextTypes.DEFAULT_TYPE, pending: PendingUpload) -> None:
    """Одно сообщение со списком файлов: альбом из нескольких файлов не плодит ответов."""
    names = "\n".join(f"• {html.escape(name)}" for _, name in pending.files)
    text = f"Поставщик «{html.escape(pending.title)}», файлов: {len(pending.files)}\n{names}"
    if pending.status_message_id is not None:
        try:
            await context.bot.edit_message_text(
                text,
                chat_id=_chat_id(update),
                message_id=pending.status_message_id,
                parse_mode=ParseMode.HTML,
                reply_markup=UPLOAD_KEYBOARD,
            )
            return
        except BadRequest:
            pass  # сообщение удалено или слишком старое — пришлём новое
    status = await send_response(update, context, response=text, keyboard=UPLOAD_KEYBOARD)
    pending.status_message_id = status.message_id


async def _upload_supplier_files(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pending: PendingUpload | None = _user_data(context).pop(PENDING_UPLOAD, None)
    if pending is None or not pending.files:
        await send_response(update, context, response="Нет файлов для загрузки, выберите поставщика заново через /pf")
        return

    title = html.escape(pending.title)
    with tempfile.TemporaryDirectory() as tmp_dir:
        sources: list[Path] = []
        # Каждый файл в своей папке: одинаковые имена не затрут друг друга.
        for index, (file_id, name) in enumerate(pending.files):
            source = Path(tmp_dir) / str(index) / name
            source.parent.mkdir()
            _file = await context.bot.get_file(file_id)
            await _file.download_to_drive(source)
            sources.append(source)
        result = await priceformation.load_supplier_prices(pending.supplier_id, sources)

    if not result.ok:
        await send_response(
            update,
            context,
            response=f"Не удалось загрузить файлы поставщика «{title}»: {html.escape(_error_text(result.output))}",
        )
        return
    placed = "\n".join(f"• {html.escape(name)}" for name in _placed_names(result))
    await send_response(update, context, response=f"Файлы поставщика «{title}» загружены:\n{placed}")


def _placed_names(result: priceformation.CommandResult) -> list[str]:
    """Имена, под которыми priceformation положил файлы (из поля files JSON-ответа)."""
    try:
        payload = result.json()
    except ValueError:
        return []
    files = payload.get("files", []) if isinstance(payload, dict) else []
    return [Path(path).name for path in files if isinstance(path, str)]


def _chat_id(update: Update) -> int:
    if update.effective_chat is None:
        raise RuntimeError("chat недоступен для этого обновления")
    return update.effective_chat.id


def _user_data(context: ContextTypes.DEFAULT_TYPE) -> dict:
    if context.user_data is None:
        raise RuntimeError("user_data недоступна для этого обновления")
    return context.user_data


def _error_text(output: str) -> str:
    """Текст ошибки из JSON-ответа CLI; если ответ не JSON — хвост вывода."""
    last_line = output.strip().rsplit("\n", 1)[-1]
    try:
        error = json.loads(last_line).get("error")
    except ValueError, AttributeError:
        error = None
    if isinstance(error, dict):
        error = error.get("message") or error.get("kind")
    return str(error) if error else priceformation.tail(output, 300) or "неизвестная ошибка"


def _log(output: str) -> str:
    text = priceformation.tail(output, LOG_LIMIT)
    return f"<pre>{html.escape(text)}</pre>" if text else ""
