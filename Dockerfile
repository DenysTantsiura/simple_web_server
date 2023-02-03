# Docker-команда FROM вказує базовий образ контейнера
# Наш базовий образ - це Linux з попередньо встановленим python-3.10
FROM python:3.10

ENV POETRY_VIRTUALENVS_CREATE=false

# Встановимо змінну середовища
ENV APP_HOME /app

# Встановимо робочу директорію усередині контейнера
WORKDIR $APP_HOME

COPY ["poetry.lock", "pyproject.toml", "$APP_HOME/"]  # Чому не зразу? Щоб не перероблювати всі шари при
# новому білді, при зміні в програмі (середовище пілготовлене не чіпаємо)

RUN poetry install --no-ansi –no-interaction

# Скопіюємо інші файли до робочої директорії контейнера
COPY . $APP_HOME

# creates the directory if it doesn't exist, and updates some image metadata to specify all relative paths...
WORKDIR /storage

WORKDIR $APP_HOME

# VOLUME . /usr/src/app
# When the RUN command finishes, changes to the image are saved, and changes to the anonymous volume are discarded!
# inside docker-container:
VOLUME storage
# To specify where you want to include volumes with your image, provide a docker-compose.yml

# Встановимо залежності усередині контейнера
# RUN pip install -r requirements.txt
RUN poetry add $(cat requirements.txt)

# Позначимо порт де працює програма всередині контейнера
EXPOSE 3000

# Запустимо нашу програму всередині контейнера
ENTRYPOINT ["python", "main.py"]
# RUN poetry run py .\main.py

# docker run --volume=/host_folder:/usr/src/app my_image
