from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import mimetypes  # Для визначення MIME types файлів у Python існує окремий модуль
import pathlib
import urllib.parse
# import urllib.request  # багато недоліків на відміну від 3party: request
import socket
from threading import Thread

UDP_IP = '127.0.0.1'
UDP_PORT = 5000  # http://127.0.0.1:5000/
file_data = 'data.json'
path_data = pathlib.Path('storage')
"""
Наприклад, при зверненні до маршруту /contact у змінній self.path 
знаходитиметься значення /contact. І в принципі для нашого простого 
прикладу цього достатньо. Але правильнішим буде підхід використання 
спеціальної функції urllib.parse.urlparse, яка повертає 
об'єкт 
ParseResult(scheme='', netloc='', path='/contact', params='', query='', 
fragment=''). 
Вона може отримувати з маршруту, також наприклад 'query' запити. 
Якщо ми звернемося за адресою 
/contact?name=Test 
у змінній self.path буде знаходитись 
/contact?name=Test, 
а ось urllib.parse.urlparse поверне нам те, що потрібно 
ParseResult(scheme='', netloc='', path='/contact', params='', 
query='name=Test', fragment='') 
та в атрибуті path буде маршрут '/contact', 
а 'query' містить значення 'name=Test' 
куди воно і мало потрапити.
"""
class HttpHandler(BaseHTTPRequestHandler):  # оброблювач запитів
    """простий HTTP сервер, який приймає запити за адресами:
     / та /message, і на GET-запит відповідає відповідними сторінками,
     а на POST-запит - див.комент нижче."""
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)  # повертає об'єкт ParseResult(scheme='', netloc='', path='/contact',
        # params='', query=..., fragment='').
        # Сама маршрутизація виконана за допомогою вкладених інструкцій if:
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message':
            self.send_html_file('message.html')
        else:  # додамо до коду маршрутизації обробку статичних ресурсів:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()  # Надсилаємо статичні ресурси (картинки, style.css, others...)
            else:  # Якщо жоден маршрут не визначено, ми повертаємо спеціальну сторінку для помилки 404 Not Found.
                self.send_html_file('error.html', 404)

    # Для відповіді браузеру ми використовуємо метод send_html_file:
    def send_html_file(self, filename, status=200):  # default status = 200
        self.send_response(status)
        # При надсиланні html файлу ми повідомили браузеру контент надсиланням наступного заголовка:
        self.send_header('Content-type', 'text/html')  #  MIME types файлу. Так ми повідомляємо браузеру тип даних, які можуть бути передані за допомогою HTTP протоколу.
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    # Для визначення MIME types файлів у Python існує окремий модуль mimetypes:
    # Картинки та стилі з файлу style.css, які повинні повертатися з сервера,
    # але не є файлами HTML, називають загальним словом статичні ресурси.
    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:  # Якщо модуль визначив тип файлу, то надсилаємо його:
            self.send_header("Content-type", mt[0])
        else:  # У разі невдачі ми вважаємо тип файлу простим текстом:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())

    """
    Обробка форми виконується функцією do_POST. 
    Оскільки в нашому додатку лише одна форма, 
    то ми не писатимемо всередині цієї функції обробку маршрутів. 
    У self.path завжди буде /contact, який прописаний у 
    атрибуті action нашої форми на сторінці contact.html.
    """
    def do_POST(self):  # при натисканні на веб-сторінці Send
        """
        Для отримання даних у додатку з форми ми використовуємо функцію
        self.rfile.read, яка читає байт-рядок певного розміру. Розмір
        даних у байтах браузер (клієнт) передає через заголовок Content-Length.
        Тому наступним рядком коду ми отримуємо дані від браузера:
        """
        data = self.rfile.read(int(self.headers['Content-Length']))
        print(data)  # Це байт-рядок виду: b'username=krabaton&email=krabat%40test.com&message=Hello+my+friend' :
        """"Для форми з enctype="application/x-www-form-urlencoded" пробіли повинні бути замінені на "+", 
        а також браузер застосовує до рядка метод encodeURIComponent ."""
        # Щоб повернути дані до початкового вигляду, нам треба застосувати метод urllib.parse.unquote_plus:
        # data_parse = urllib.parse.unquote_plus(data.decode())
        # пересилає його(байт-рядок) далі на обробку за допомогою socket (протокол UDP), Socket серверу.
        self._send_to_form_handler(UDP_IP, UDP_PORT, data)
   
        """
        Виконуємо редирект на головну сторінку. Для цього відправляємо 
        статус 302 та встановлюємо заголовок Location: /. 
        Коли браузер отримає нашу відповідь, він зрозуміє за 
        заголовком Location: /, що йому треба перейти на головну сторінку:"""
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()  # send end-headers to show ending request

    def _send_to_form_handler(self, ip, port, data):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server = ip, port
        sock.sendto(data, server)
        # print(f'Send data: {data.decode()} to server: {server}')
        # response, address = sock.recvfrom(1024)
        # print(f'Response data: {response.decode()} from address: {address}')
        sock.close()


def run_http_server(server_class=HTTPServer, handler_class=HttpHandler):
    # на якому порті та адресі прийматимемо/очікуємо з'єднання:
    server_address = ('', 3000)  # порт 3000, Якщо аргумент для адреси порожнй рядок - то доступний для всіх інтерфейсів
    http = server_class(server_address, handler_class)  # сам запит
    try:
        http.serve_forever()  # буде працювати доки не викличемо ШатДаун
    except KeyboardInterrupt:  # зупиняємо сервер за виключенням (прериванням клави ctrl+c напирклад)
        http.server_close()


def run_form_handler_server(ip, port):
    # використовується модуль socket:
    # Повертає об'єкт-інтерфейс для комунікації через який. 
    # І клієнт і сервер мають мати інстанси сокета.
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    """
    Корисно вказати системі, що якщо додаток не закрив з'єднання, 
    то треба дозволити повторно відкрити тому ж порті. 
    Для цього налаштуємо сокет:
    """
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Створили сокет для сирих даних, відкриваємо порт port на локальному хості. 
    # Сокетом завідує система.
    server = ip, port
    sock.bind(server)

    try:
        while True:
            ## ///Socket сервер переводить отриманий байт-рядок у словник 
            ## ///і зберігає його в json файл data.json в папку storage.
            data, address = sock.recvfrom(1024)  # отримуємо 1024??? байта
            print(f'Received data: {data.decode()} from: {address}')
            print(data)  # Це байт-рядок виду: b'username=krabaton&email=krabat%40test.com&message=Hello+my+friend' :
            """"Для форми з enctype="application/x-www-form-urlencoded" пробіли повинні бути замінені на "+", 
            а також браузер застосовує до рядка метод encodeURIComponent ."""
            # Щоб повернути дані до початкового вигляду, нам треба застосувати метод urllib.parse.unquote_plus:
            data_parse = urllib.parse.unquote_plus(data.decode())

            # print(data_parse)  # username=krabaton&email=krabat@test.com&message=Hello my friend
            # Після цього рядок можна перетворити на словник таким виразом:
            data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
            print(data_dict)  # {'username': 'krabaton', 'email': 'krabat@test.com', 'message': 'Hello my friend'}
            data_dict = prepare_data(data_dict)
            save_data(data_dict)

    except KeyboardInterrupt:
        print(f'Destroy server')

    finally:
        sock.close()


def prepare_data(data_dict):
    # convert to json...
    if (path_data / file_data).exists():
        with open(path_data / file_data, "r") as fh:
            data_json = json.load(fh)

    else:
        data_json = {}

    new_data_json = {str(datetime.now()):data_dict}
    data_json.update(new_data_json)

    return data_json
    


def save_data(data_dict):
    # save to file
    with open(path_data / file_data, "w") as fh:
        json.dump(data_dict, fh)


if __name__ == '__main__':
    # run_http_server()
    # run_form_handler_server(UDP_IP, UDP_PORT)
    thread_http_server = Thread(target=run_http_server)
    thread_http_server.start()

    thread_form_handler_server = Thread(target=run_form_handler_server, args=(UDP_IP, UDP_PORT))
    thread_form_handler_server.start()


