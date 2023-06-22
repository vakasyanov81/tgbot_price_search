from pydub import AudioSegment


def save_oga_to_mp3(oga_file: str):
    mp3_file = oga_file.replace('.oga', '.mp3')

    # Открываем файл формата oga
    oga_audio = AudioSegment.from_file(oga_file, format="ogg")

    # Конвертируем в MP3 и сохраняем
    oga_audio.export(mp3_file, format="mp3")
    return mp3_file
