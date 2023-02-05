# Docker-команда FROM вказує базовий образ контейнера
# Наш базовий образ - це Linux з попередньо встановленим python-3.10
FROM python:3.10

# Встановимо змінну середовища
ENV APP_HOME /app

# Встановимо робочу директорію усередині контейнера
WORKDIR $APP_HOME

# Скопіюємо файли
COPY . .

# Встановимо залежності усередині контейнера
RUN pip install -r requirements.txt

# Позначимо порт де працює програма всередині контейнера
EXPOSE 3000

# Запустимо нашу програму всередині контейнера
ENTRYPOINT ["python", "main.py"]

# Example to start:
# docker run --volume=/host_folder:/usr/src/app my_image

# sudo docker build . -t sws:latest
# docker run -p 3000:3000 --volume=/media/denys/426AB6046D377CA7/prjs/simple_web_server/storage/:/app/storage sws

