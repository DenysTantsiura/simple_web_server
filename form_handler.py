"""
Для роботи з формою створіть Socket сервер на порту 5000. 
Алгоритм роботи такий. Ви вводите дані у форму, вони потрапляють 
у ваш веб-додаток, який пересилає його далі на обробку 
за допомогою socket (протокол UDP), Socket серверу. 
Socket сервер переводить отриманий байт-рядок у словник 
і зберігає його в json файл data.json в папку storage.

Формат запису файлу data.json наступний:

{
  "2022-10-29 20:20:58.020261": {
    "username": "krabaton",
    "message": "First message"
  },
  "2022-10-29 20:21:11.812177": {
    "username": "Krabat",
    "message": "Second message"
  }
}

Де ключ кожного повідомлення - це час отримання 
повідомлення: datetime.now(). 
Тобто кожне нове повідомлення від веб-програми 
дописується до файлу storage/data.json з часом отримання.

Використовуйте для створення вашої веб-програми 
один файл main.py. Запустіть HTTP сервер і 
Socket сервер у різних потоках.
"""

"""
Сокет (Socket) — це програмний інтерфейс для забезпечення 
інформаційного обміну між процесами. Існують клієнтські та 
серверні сокети. Серверний сокет прослуховує певний порт 
і чекає на підключення клієнта, 
а клієнтський підключається до сервера. 
"""
# У Python для роботи з сокетами використовується модуль socket:
import socket
import urllib.parse


UDP_IP = '127.0.0.1'
UDP_PORT = 5000  # http://localhost:5000/   http://127.0.0.1:5000/


def run_server(ip, port):
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


            # sock.sendto(data, address) # ???? повернемо клієнту
            # print(f'Send data: {data.decode()} to: {address}')

    except KeyboardInterrupt:
        print(f'Destroy server')

    finally:
        sock.close()

def prepare_data():
    ...

def save_data(data_dict):
    ...

if __name__ == '__main__':
    run_server(UDP_IP, UDP_PORT)
                

