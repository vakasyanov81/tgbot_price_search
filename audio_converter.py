from pydub import AudioSegment


def save_oga_to_new_format(oga_file: str, output_format: str = "wav"):
    _file = oga_file.replace(".oga", f".{output_format}")

    # Открываем файл формата oga
    oga_audio = AudioSegment.from_file(oga_file, format="ogg")

    # Конвертируем и сохраняем
    oga_audio.export(_file, format=output_format)
    return _file
