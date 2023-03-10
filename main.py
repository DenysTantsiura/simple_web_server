from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import mimetypes  # окремий модуль для визначення MIME types файлів
import logging
import pathlib
import re
import socket
from threading import Thread
import urllib.parse


MESSAGE_LENGTH = 1024
UDP_IP = '127.0.0.1'
UDP_PORT = 5000  # http://localhost:5000/
HTTP_IP = ''  # Якщо аргумент для адреси порожнй рядок - то доступний для всіх інтерфейсів(ip)
HTTP_PORT = 3000
file_data = 'data.json'
path_data = pathlib.Path('storage')
file_path = pathlib.Path(path_data, file_data)  # path_data / file_data

logging.basicConfig(level=logging.DEBUG, format='%(threadName)s %(message)s')


class HttpHandler(BaseHTTPRequestHandler):  # оброблювач запитів
    """простий HTTP сервер, який приймає запити за адресами:
     / та /message, і на GET-запит відповідає відповідними сторінками,
     а на POST-запит - див.комент нижче."""
    def do_GET(self) -> None:
        # повертає об'єкт ParseResult(scheme='', netloc='', path='/message', params='', query=..., fragment=''):
        pr_url: urllib.parse.ParseResult = urllib.parse.urlparse(self.path)  

        match pr_url.path:
            case '/': 
                self.send_html_file('index.html')
            case '/message':
                self.send_html_file('message.html')
            case _:
                # додамо до коду маршрутизації обробку статичних ресурсів:
                if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                    self.send_static()  # Надсилаємо статичні ресурси (картинки, style.css, others...)
                else:
                    self.send_html_file('error.html', 404)

    def send_html_file(self, filename: str, status: int = 200) -> None:  # default status = 200
        """Для відповіді браузеру ми використовуємо метод send_html_file."""
        self.send_response(status)  # send_response(status, 'Hello!')
        # При надсиланні html файлу ми повідомили браузеру контент надсиланням наступного заголовка:
        self.send_header('Content-type', 'text/html')  # MIME types файлу - повідомляємо браузеру тип даних,
        # які можуть бути передані за допомогою HTTP протоколу.
        self.end_headers()  # send end-headers to show ending request
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self) -> None:
        """
        Для визначення MIME types файлів у Python існує окремий модуль mimetypes:
        Картинки та стилі з файлу style.css, які повинні повертатися з сервера,
        але не є файлами HTML, називають загальним словом статичні ресурси.
        """
        self.send_response(200)
        mime_type: tuple = mimetypes.guess_type(self.path)
        if mime_type:  # Якщо модуль визначив тип файлу, то надсилаємо його:
            self.send_header('Content-type', mime_type[0])

        else:  # У разі невдачі ми вважаємо тип файлу простим текстом:
            self.send_header('Content-type', 'text/plain')
        self.end_headers()  # send end-headers to show ending request
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())

    """
    Обробка форми виконується функцією do_POST. 
    Оскільки в нашому додатку лише одна форма, 
    то не писатимемо всередині цієї функції обробку маршрутів. 
    У self.path завжди буде /message, який прописаний у 
    атрибуті action цієї форми на сторінці message.html.
    """
    def do_POST(self) -> None:  # при натисканні на веб-сторінці Send
        """
        Обробка форми.
        Для отримання даних у додатку з форми ми використовуємо функцію
        self.rfile.read, яка читає байт-рядок певного розміру. Розмір
        даних у байтах браузер (клієнт) передає через заголовок Content-Length.
        Тому наступним рядком коду ми отримуємо дані від браузера:
        """
        data: bytes = self.rfile.read(int(self.headers['Content-Length']))
        # data- Це байт-рядок виду: b'username=den&email=den%40test.com&message=Hello+my+friend.'

        # пересилає його(байт-рядок) далі на обробку за допомогою socket (протокол UDP), Socket серверу:
        self._send_to_form_handler(UDP_IP, UDP_PORT, data)
   
        """
        Виконуємо редирект на головну сторінку. Для цього відправляємо 
        статус 302 та встановлюємо заголовок Location: /. 
        Коли браузер отримає нашу відповідь, він зрозуміє за 
        заголовком Location: /, що йому треба перейти на головну сторінку:"""
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()  # send end-headers to show ending request

    @staticmethod
    def _send_to_form_handler(ip: str, port: int, data: bytes) -> None:
        # Пересилаємо Socket серверу data
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server: tuple = ip, port
        sock.sendto(data, server)
        sock.close()


def run_http_server(server_class=HTTPServer, handler_class=HttpHandler) -> None:
    """Запускаємо сервер, перед цим вказуємо на якому порті та адресі прийматимемо/очікуємо з'єднання:"""
    server_address: tuple = (HTTP_IP, HTTP_PORT)
    http = server_class(server_address, handler_class)  # сам запит
    try:
        http.serve_forever()  # сервер буде працювати доки не викличемо 'примусово' (shutdown)

    except KeyboardInterrupt:  # зупиняємо сервер за виключенням (прериванням клави ctrl+c напирклад)
        logging.info(f'Stopping the http server!')
        http.server_close()


def run_form_handler_server(ip: str, port: int) -> None:
    """
    Socket сервер переводить отриманий байт-рядок у словник
    і зберігає його в json файл data.json в папку storage.
    """
    
    """
    Використовується модуль socket:
    Повертає об'єкт-інтерфейс для комунікації через який. 
    І клієнт і сервер мають мати інстанси сокета."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    """
    Корисно вказати системі, що якщо додаток не закрив з'єднання, 
    то треба дозволити повторно відкрити тому ж порті. 
    Для цього налаштуємо сокет: (if lost sock.close())
    """
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Створили сокет для сирих даних, відкриваємо порт port на локальному хості. 
    # Сокетом завідує система.
    server: tuple = ip, port
    sock.bind(server)

    try:
        while True:
            data, address = sock.recvfrom(MESSAGE_LENGTH)  # отримуємо MESSAGE_LENGTH байта (1024)
            # data - Це байт-рядок виду: b'username=den&email=den%40test.com&message=Hello+my+friend.'

            """"Для форми з enctype="application/x-www-form-urlencoded" пробіли повинні бути замінені на "+", 
            а також браузер застосовує до рядка метод encodeURIComponent."""
            # Щоб повернути дані до початкового вигляду, треба застосувати метод urllib.parse.unquote_plus:
            data_parse: str = urllib.parse.unquote_plus(data.decode())
            # data_parse=> username=den&email=den@test.com&message=Hello my friend.
            try:
                # Після цього рядок можна перетворити на словник:
                data_dict: dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
                # data_dict=> {'username': 'den', 'email': 'den@test.com', 'message': 'Hello my friend.'}

            except TypeError:
                logging.info(f'Bad request: incorrect\n{data_parse=}')

            except Exception as error:
                logging.info(f'!Something WRONG!\n{error=}')

            else:
                data_dict: dict = prepare_data(data_dict, file_path)
                save_data(data_dict, file_path) if data_dict else None

    except KeyboardInterrupt:
        logging.info(f'Stopping the form-handler server!')

    finally:
        sock.close()


def data_validation(data: dict) -> None:
    errors = []
    name: str = data.get('username', None)
    if not name or len(name) < 2 or name[0].isdigit() or not name[0].isalpha():
        logging.info(f'{name=} is incorect!')
        errors.append(f'Incorrect name({name})')

    email: str = data.get('email', None)
    if not email or not (re.search(r'\b[a-zA-z][\w_.]+@[a-zA-z]+\.[a-zA-z]{2,}$', email) or\
                re.search(r'\b[a-zA-z][\w_.]+@[a-zA-z]+.[a-zA-z]+.[a-zA-z]{2,}$', email)):
        logging.info(f'{email=} is incorect!')
        errors.append(f'Incorrect email({email})')

    message: str = data.get('message', None)
    if not message or len(message) < 2:
        logging.info(f'{message=} is incorect!')
        errors.append(f'Incorrect message({message})')

    return errors

def prepare_data(data_dict: dict, path_of_file: pathlib.Path) -> dict:
    """
    Read the existing data and convert the new data to json, 
    then add the new json data to the existing data and return it.
    """
    errors = data_validation(data_dict)
    if errors:
        logging.info(f'!Invalid data received!\n{errors=}')
        return {}

    data_json = {}
    if path_of_file.exists():
        try:
            with open(path_of_file, 'r') as fh:
                data_json = json.load(fh)  # try-except forbidden file ...

        except Exception as error:
            logging.info(f'!WRONG json loading!\n{error=}')
        
        else:
            if not isinstance(data_json, dict):
                logging.info(f'!Loaded json is not a dict!\n{error=}')
                return {}

    new_data_json = {str(datetime.now()): data_dict}
    data_json.update(new_data_json)

    return data_json


def save_data(data_dict: dict, path_of_file: pathlib.Path) -> None:
    """Save data_dict to file."""
    path_data.mkdir(parents=True, exist_ok=True) if not path_data.exists() else None
    if path_of_file.exists() and not data_dict:
        return None

    try:
        with open(path_of_file, 'w') as fh:
            json.dump(data_dict, fh)

    except Exception as error:
        logging.info(f'Can\'t save data!\n{error=}')


if __name__ == '__main__':

    thread_http_server = Thread(target=run_http_server)
    thread_http_server.start()

    thread_form_handler_server = Thread(target=run_form_handler_server, args=(UDP_IP, UDP_PORT))
    thread_form_handler_server.start()
