# Используем образ Python 3.11 в качестве базового
FROM python:3.11.1-slim-buster
# Установка зависимостей ffmpeg
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Создание рабочей директории внутри контейнера и копирование кода
WORKDIR /app
COPY .. .

# Установка зависимостей Python из файла requirements.txt
RUN python3 -m pip install update pip
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r ./requirements.txt

# Запуск бота
CMD ["python3", "main.py"]