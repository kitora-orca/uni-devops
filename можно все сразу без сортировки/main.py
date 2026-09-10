import flet as ft
import sqlite3
from datetime import datetime
import re
import hashlib

# Функция для инициализации базы данных
def init_database():
    conn = sqlite3.connect('horse_race.db')
    cursor = conn.cursor()
    
    # Создаем таблицу пользователей
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('Пользователь', 'Жокей', 'Администратор'))
    )
    ''')
    
    # Создаем остальные таблицы, если они не существуют
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS owners (
        owner_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS racetracks (
        racetrack_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        location TEXT NOT NULL
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS jockeys (
        jockey_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        address TEXT,
        age INTEGER,
        rating REAL
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS horses (
        horse_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        gender TEXT CHECK(gender IN ('male', 'female')),
        age INTEGER,
        owner_id INTEGER,
        FOREIGN KEY (owner_id) REFERENCES owners (owner_id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS competitions (
        competition_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        date TEXT NOT NULL,
        time TEXT,
        racetrack_id INTEGER,
        FOREIGN KEY (racetrack_id) REFERENCES racetracks (racetrack_id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS race_participants (
        participant_id INTEGER PRIMARY KEY AUTOINCREMENT,
        competition_id INTEGER,
        horse_id INTEGER,
        jockey_id INTEGER,
        position INTEGER,
        finish_time TEXT,
        FOREIGN KEY (competition_id) REFERENCES competitions (competition_id),
        FOREIGN KEY (horse_id) REFERENCES horses (horse_id),
        FOREIGN KEY (jockey_id) REFERENCES jockeys (jockey_id)
    )
    ''')

    conn.commit()
    conn.close()

# Функция для подключения к базе данных
def create_connection():
    try:
        conn = sqlite3.connect('horse_race.db')
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Ошибка подключения к SQLite: {e}")
        return None

# Улучшенная функция для выполнения запросов к БД
def execute_query(query, params=()):
    conn = create_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        if query.strip().upper().startswith('SELECT'):
            result = cursor.fetchall()
        else:
            conn.commit()
            result = cursor.lastrowid
        
        return result
    except sqlite3.Error as e:
        print(f"Ошибка при выполнении запроса: {e}")
        return None
    finally:
        conn.close()

# Функции валидации
def validate_date(date_string):
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def validate_time(time_string):
    pattern = r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'
    return re.match(pattern, time_string) is not None

def validate_race_time(time_string):
    if not time_string:
        return True
    
    pattern = r'^([0-5]?[0-9]):([0-5][0-9])(\.\d{1,3})?$'
    return re.match(pattern, time_string) is not None

# Функция для проверки авторизации
def check_auth(username, password):
    query = "SELECT user_id, username, password_hash, role FROM users WHERE username = ?"
    user = execute_query(query, (username,))
    
    if user and user[0]['password_hash'] == hashlib.sha256(password.encode()).hexdigest():
        return {
            'user_id': user[0]['user_id'],
            'username': user[0]['username'],
            'role': user[0]['role']
        }
    return None

# Функция для проверки прав доступа
def check_permission(user_role, required_roles):
    return user_role in required_roles

# Страница авторизации
def login_page(page):
    username_field = ft.TextField(label="Имя пользователя", width=300)
    password_field = ft.TextField(
        label="Пароль", 
        password=True, 
        can_reveal_password=True,
        width=300
    )
    result_message = ft.Text()

    def on_login(e):
        user = check_auth(username_field.value, password_field.value)
        if user:
            page.session.set("user", user)
            page.go("/main")
        else:
            result_message.value = "Неверное имя пользователя или пароль"
            result_message.color = ft.Colors.RED
            page.update()

    return ft.Container(
        content=ft.Column([
            ft.Text("Авторизация", size=24, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            username_field,
            password_field,
            ft.ElevatedButton("Войти", on_click=on_login),
            result_message
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        alignment=ft.alignment.center,
        expand=True
    )

# Страница 1: Список состязаний с жокеями, лошадьми и местами
def page_competitions_list(page, user_role):
    if not check_permission(user_role, ["Пользователь", "Жокей", "Администратор"]):
        return ft.Text("Доступ запрещен", size=20, color=ft.Colors.RED)

    def load_competitions():
        query = """
            SELECT c.competition_id, c.date, c.time, c.title, 
                   r.name as racetrack_name, r.location
            FROM competitions c
            JOIN racetracks r ON c.racetrack_id = r.racetrack_id
            ORDER BY c.date DESC, c.time DESC
        """
        return execute_query(query) or []

    def load_competition_details(competition_id):
        query = """
            SELECT rp.position, rp.finish_time,
                   h.name as horse_name, h.gender, h.age,
                   j.name as jockey_name, j.age as jockey_age, j.rating,
                   o.name as owner_name
            FROM race_participants rp
            JOIN horses h ON rp.horse_id = h.horse_id
            JOIN jockeys j ON rp.jockey_id = j.jockey_id
            JOIN owners o ON h.owner_id = o.owner_id
            WHERE rp.competition_id = ?
            ORDER BY rp.position IS NULL, rp.position
        """
        return execute_query(query, (competition_id,)) or []

    def show_competition_results(competition_id):
        details = load_competition_details(competition_id)
        results_table.rows.clear()
        
        if not details:
            results_table.rows.append(
                ft.DataRow(cells=[ft.DataCell(ft.Text("Нет данных о результатах"))])
            )
        else:
            for participant in details:
                position = participant['position'] if participant['position'] is not None else "Н/Ф"
                finish_time = participant['finish_time'] if participant['finish_time'] else "Н/Д"
                gender = "Жеребец" if participant['gender'] == 'male' else "Кобыла"
                
                # Проверяем наличие данных о жокее
                jockey_name = participant['jockey_name'] if participant['jockey_name'] else "Не указан"
                jockey_age = participant['jockey_age'] if participant['jockey_age'] is not None else "Н/Д"
                jockey_rating = participant['rating'] if participant['rating'] is not None else "Н/Д"
                
                results_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(position))),
                            ft.DataCell(ft.Text(participant['horse_name'])),
                            ft.DataCell(ft.Text(gender)),
                            ft.DataCell(ft.Text(str(participant['age']))),
                            ft.DataCell(ft.Text(jockey_name)),
                            ft.DataCell(ft.Text(str(jockey_age))),
                            ft.DataCell(ft.Text(str(jockey_rating))),
                            ft.DataCell(ft.Text(str(finish_time))),
                            ft.DataCell(ft.Text(participant['owner_name'])),
                        ]
                    )
                )
        
        page.update()

    def update_competitions_list():
        competitions = load_competitions()
        competitions_list.controls.clear()
        
        if not competitions:
            competitions_list.controls.append(ft.Text("Нет данных о состязаниях"))
        else:
            for comp in competitions:
                comp_date = comp['date']
                comp_time = comp['time']
                
                comp_card = ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text(f"{comp['title'] or 'Состязание без названия'}", 
                                    weight=ft.FontWeight.BOLD),
                            ft.Divider(),
                            ft.Row([
                                ft.Text(f"Дата: {comp_date}", expand=1),
                                ft.Text(f"Время: {comp_time}", expand=1),
                            ]),
                            ft.Text(f"Ипподром: {comp['racetrack_name']}"),
                            ft.Text(f"Местоположение: {comp['location']}"),
                            ft.ElevatedButton(
                                "Показать результаты",
                                on_click=lambda e, cid=comp['competition_id']: show_competition_results(cid)
                            )
                        ], spacing=10),
                        padding=15,
                    )
                )
                competitions_list.controls.append(comp_card)
        
        page.update()

    # Создаем элементы интерфейса
    competitions_list = ft.Column()
    results_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Место")),
            ft.DataColumn(ft.Text("Лошадь")),
            ft.DataColumn(ft.Text("Пол")),
            ft.DataColumn(ft.Text("Возраст")),
            ft.DataColumn(ft.Text("Жокей")),
            ft.DataColumn(ft.Text("Возраст")),
            ft.DataColumn(ft.Text("Рейтинг")),
            ft.DataColumn(ft.Text("Время")),
            ft.DataColumn(ft.Text("Владелец")),
        ],
        rows=[]
    )

    # Загружаем данные
    update_competitions_list()

    # Добавляем кнопку обновления
    refresh_button = ft.IconButton(
        icon=ft.Icons.REFRESH,
        tooltip="Обновить список",
        on_click=lambda e: update_competitions_list()
    )

    return ft.Column([
        ft.Row([
            ft.Text("Список состязаний", size=20, weight=ft.FontWeight.BOLD),
            refresh_button
        ]),
        ft.Divider(),
        competitions_list,
        ft.Text("Результаты состязания", size=16, weight=ft.FontWeight.BOLD),
        ft.Container(
            content=results_table,
            padding=10,
            border=ft.border.all(1),
            border_radius=5,
        )
    ], scroll=ft.ScrollMode.AUTO, expand=True)

# Страница 2: Добавление нового состязания
def page_add_competition(page, user_role):
    if not check_permission(user_role, ["Администратор"]):
        return ft.Text("Доступ запрещен. Только для администраторов.", size=20, color=ft.Colors.RED)

    def load_racetracks():
        query = "SELECT racetrack_id, name, location FROM racetracks"
        return execute_query(query) or []

    racetracks = load_racetracks()

    title_field = ft.TextField(label="Название состязания", width=400)
    date_field = ft.TextField(
        label="Дата (ГГГГ-ММ-ДД)", 
        hint_text="2023-12-31",
        width=200
    )
    time_field = ft.TextField(
        label="Время (ЧЧ:ММ)", 
        hint_text="14:30",
        width=200
    )
    racetrack_dropdown = ft.Dropdown(
        label="Ипподром",
        options=[ft.dropdown.Option(text=f"{r['name']} ({r['location']})", key=r['racetrack_id']) for r in racetracks],
        width=400
    )
    result_message = ft.Text()

    def add_competition(e):
        # Валидация данных
        if not all([title_field.value, date_field.value, time_field.value, racetrack_dropdown.value]):
            result_message.value = "Все поля обязательны для заполнения"
            result_message.color = ft.Colors.RED
            page.update()
            return

        if not validate_date(date_field.value):
            result_message.value = "Неверный формат даты. Используйте ГГГГ-ММ-ДД"
            result_message.color = ft.Colors.RED
            page.update()
            return

        if not validate_time(time_field.value):
            result_message.value = "Неверный формат времени. Используйте ЧЧ:ММ"
            result_message.color = ft.Colors.RED
            page.update()
            return

        # Добавление в базу данных
        query = """
            INSERT INTO competitions (title, date, time, racetrack_id) 
            VALUES (?, ?, ?, ?)
        """
        params = (title_field.value, date_field.value, time_field.value, racetrack_dropdown.value)
        
        result = execute_query(query, params)
        
        if result is not None:
            result_message.value = "Состязание успешно добавлено!"
            result_message.color = ft.Colors.GREEN
            
            # Очищаем поля
            title_field.value = ""
            date_field.value = ""
            time_field.value = ""
            racetrack_dropdown.value = None
        else:
            result_message.value = "Ошибка при добавлении состязания"
            result_message.color = ft.Colors.RED
        
        page.update()

    return ft.Column([
        ft.Text("Добавление нового состязания", size=20, weight=ft.FontWeight.BOLD),
        ft.Divider(),
        ft.Row([title_field], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([date_field, time_field], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([racetrack_dropdown], alignment=ft.MainAxisAlignment.CENTER),
        ft.ElevatedButton("Добавить состязание", on_click=add_competition),
        result_message
    ], scroll=ft.ScrollMode.AUTO, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)

# Страница 3: Добавление нового жокея
def page_add_jockey(page, user_role):
    if not check_permission(user_role, ["Жокей", "Администратор"]):
        return ft.Text("Доступ запрещен. Только для жокеев и администраторов.", size=20, color=ft.Colors.RED)

    name_field = ft.TextField(label="Имя жокея", width=300)
    address_field = ft.TextField(label="Адрес", multiline=True, width=300)
    age_field = ft.TextField(
        label="Возраст", 
        keyboard_type=ft.KeyboardType.NUMBER,
        width=150
    )
    rating_field = ft.TextField(
        label="Рейтинг (0-5)", 
        keyboard_type=ft.KeyboardType.NUMBER,
        width=150
    )
    result_message = ft.Text()

    def add_jockey(e):
        if not all([name_field.value, age_field.value, rating_field.value]):
            result_message.value = "Имя, возраст и рейтинг обязательны для заполнения"
            result_message.color = ft.Colors.RED
            page.update()
            return

        try:
            age = int(age_field.value)
            if age <= 0 or age > 100:
                result_message.value = "Возраст должен быть между 1 и 100"
                result_message.color = ft.Colors.RED
                page.update()
                return
        except ValueError:
            result_message.value = "Возраст должен быть целым числом"
            result_message.color = ft.Colors.RED
            page.update()
            return

        try:
            rating = float(rating_field.value)
            if rating < 0 or rating > 5:
                result_message.value = "Рейтинг должен быть между 0 и 5"
                result_message.color = ft.Colors.RED
                page.update()
                return
        except ValueError:
            result_message.value = "Рейтинг должен быть числом"
            result_message.color = ft.Colors.RED
            page.update()
            return

        # Добавление в базу данных
        query = """
            INSERT INTO jockeys (name, address, age, rating) 
            VALUES (?, ?, ?, ?)
        """
        params = (name_field.value, address_field.value, int(age_field.value), float(rating_field.value))
        
        result = execute_query(query, params)
        
        if result is not None:
            result_message.value = "Жокей успешно добавлен!"
            result_message.color = ft.Colors.GREEN
            
            # Очищаем поля
            name_field.value = ""
            address_field.value = ""
            age_field.value = ""
            rating_field.value = ""
        else:
            result_message.value = "Ошибка при добавлении жокея"
            result_message.color = ft.Colors.RED
        
        page.update()

    return ft.Column([
        ft.Text("Добавление нового жокея", size=20, weight=ft.FontWeight.BOLD),
        ft.Divider(),
        ft.Row([name_field], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([address_field], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([age_field, rating_field], alignment=ft.MainAxisAlignment.CENTER),
        ft.ElevatedButton("Добавить жокея", on_click=add_jockey),
        result_message
    ], scroll=ft.ScrollMode.AUTO, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)

# Страница 4: Добавление новой лошади
def page_add_horse(page, user_role):
    if not check_permission(user_role, ["Жокей", "Администратор"]):
        return ft.Text("Доступ запрещен. Только для жокеев и администраторов.", size=20, color=ft.Colors.RED)

    def load_owners():
        query = "SELECT owner_id, name FROM owners"
        return execute_query(query) or []

    owners = load_owners()

    name_field = ft.TextField(label="Кличка лошади", width=300)
    gender_dropdown = ft.Dropdown(
        label="Пол",
        options=[
            ft.dropdown.Option(key="male", text="Жеребец"),
            ft.dropdown.Option(key="female", text="Кобыла")
        ],
        width=200
    )
    age_field = ft.TextField(
        label="Возраст", 
        keyboard_type=ft.KeyboardType.NUMBER,
        width=150
    )
    owner_dropdown = ft.Dropdown(
        label="Владелец",
        options=[ft.dropdown.Option(text=o['name'], key=o['owner_id']) for o in owners],
        width=300
    )
    result_message = ft.Text()

    def add_horse(e):
        if not all([name_field.value, gender_dropdown.value, age_field.value, owner_dropdown.value]):
            result_message.value = "Все поля обязательны для заполнения"
            result_message.color = ft.Colors.RED
            page.update()
            return

        try:
            age = int(age_field.value)
            if age <= 0 or age > 30:
                result_message.value = "Возраст лошади должен быть между 1 и 30"
                result_message.color = ft.Colors.RED
                page.update()
                return
        except ValueError:
            result_message.value = "Возраст должен быть целым числом"
            result_message.color = ft.Colors.RED
            page.update()
            return

        # Добавление в базу данных
        query = """
            INSERT INTO horses (name, gender, age, owner_id) 
            VALUES (?, ?, ?, ?)
        """
        params = (name_field.value, gender_dropdown.value, int(age_field.value), owner_dropdown.value)
        
        result = execute_query(query, params)
        
        if result is not None:
            result_message.value = "Лошадь успешно добавлена!"
            result_message.color = ft.Colors.GREEN
            
            # Очищаем поля
            name_field.value = ""
            gender_dropdown.value = None
            age_field.value = ""
            owner_dropdown.value = None
        else:
            result_message.value = "Ошибка при добавлении лошади"
            result_message.color = ft.Colors.RED
        
        page.update()

    return ft.Column([
        ft.Text("Добавление новой лошади", size=20, weight=ft.FontWeight.BOLD),
        ft.Divider(),
        ft.Row([name_field], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([gender_dropdown, age_field], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([owner_dropdown], alignment=ft.MainAxisAlignment.CENTER),
        ft.ElevatedButton("Добавить лошадь", on_click=add_horse),
        result_message
    ], scroll=ft.ScrollMode.AUTO, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)

# Страница 5: Добавление результатов состязания (с расширенными проверками)
def page_add_competition_results(page, user_role):
    if not check_permission(user_role, ["Администратор"]):
        return ft.Text("Доступ запрещен. Только для администраторов.", size=20, color=ft.Colors.RED)

    def load_competitions():
        query = "SELECT competition_id, title, date FROM competitions ORDER BY date DESC"
        return execute_query(query) or []

    def load_horses():
        query = "SELECT horse_id, name FROM horses ORDER BY name"
        return execute_query(query) or []

    def load_jockeys():
        query = "SELECT jockey_id, name FROM jockeys ORDER BY name"
        return execute_query(query) or []

    def update_dropdowns():
        # Загружаем актуальные данные
        competitions = load_competitions()
        horses = load_horses()
        jockeys = load_jockeys()
        
        # Обновляем выпадающие списки
        competition_dropdown.options = [ft.dropdown.Option(text=f"{c['title']} ({c['date']})", key=c['competition_id']) for c in competitions]
        horse_dropdown.options = [ft.dropdown.Option(text=h['name'], key=h['horse_id']) for h in horses]
        jockey_dropdown.options = [ft.dropdown.Option(text=j['name'], key=j['jockey_id']) for j in jockeys]
        
        # Очищаем выбранные значения
        competition_dropdown.value = None
        horse_dropdown.value = None
        jockey_dropdown.value = None
        
        page.update()

    # Инициализация данных
    competitions = load_competitions()
    horses = load_horses()
    jockeys = load_jockeys()

    competition_dropdown = ft.Dropdown(
        label="Состязание",
        options=[ft.dropdown.Option(text=f"{c['title']} ({c['date']})", key=c['competition_id']) for c in competitions],
        width=400
    )
    horse_dropdown = ft.Dropdown(
        label="Лошадь",
        options=[ft.dropdown.Option(text=h['name'], key=h['horse_id']) for h in horses],
        width=300
    )
    jockey_dropdown = ft.Dropdown(
        label="Жокей",
        options=[ft.dropdown.Option(text=j['name'], key=j['jockey_id']) for j in jockeys],
        width=300
    )
    position_field = ft.TextField(
        label="Занятое место", 
        keyboard_type=ft.KeyboardType.NUMBER,
        width=150
    )
    time_field = ft.TextField(
        label="Время (ММ:СС.ссс)", 
        hint_text="01:23.456",
        width=200
    )
    result_message = ft.Text()

    # Добавляем кнопку обновления
    refresh_button = ft.IconButton(
        icon=ft.Icons.REFRESH,
        tooltip="Обновить списки",
        on_click=lambda e: update_dropdowns()
    )

    # Функция для проверки, участвовала ли лошадь уже в этом состязании
    def is_horse_already_in_competition(competition_id, horse_id):
        query = """
            SELECT COUNT(*) as count 
            FROM race_participants 
            WHERE competition_id = ? AND horse_id = ?
        """
        result = execute_query(query, (competition_id, horse_id))
        return result and result[0]['count'] > 0

    # Функция для проверки, занято ли уже место в состязании
    def is_position_already_taken(competition_id, position):
        query = """
            SELECT COUNT(*) as count 
            FROM race_participants 
            WHERE competition_id = ? AND position = ?
        """
        result = execute_query(query, (competition_id, position))
        return result and result[0]['count'] > 0

    # Функция для проверки соответствия времени и места
    def is_time_consistent_with_position(competition_id, position, time_str):
        # Если время не указано, пропускаем проверку
        if not time_str:
            return True, None
        
        # Проверяем формат времени
        if not validate_race_time(time_str):
            return False, "Неверный формат времени. Используйте ММ:СС.ссс"
        
        # Преобразуем время в секунды
        try:
            time_parts = time_str.split(':')
            minutes = int(time_parts[0])
            seconds_parts = time_parts[1].split('.')
            seconds = int(seconds_parts[0])
            milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
            
            total_seconds = minutes * 60 + seconds + milliseconds / 1000
        except:
            return False, "Неверный формат времени. Используйте ММ:СС.ссс"
        
        # Получаем результаты других участников этого состязания
        query = """
            SELECT position, finish_time 
            FROM race_participants 
            WHERE competition_id = ? AND finish_time IS NOT NULL
        """
        results = execute_query(query, (competition_id,)) or []
        
        for result in results:
            other_position = result['position']
            other_time_str = result['finish_time']
            
            # Пропускаем, если место или время не определены
            if other_position is None or not other_time_str:
                continue
            
            # Преобразуем время другого участника в секунды
            try:
                other_time_parts = other_time_str.split(':')
                other_minutes = int(other_time_parts[0])
                other_seconds_parts = other_time_parts[1].split('.')
                other_seconds = int(other_seconds_parts[0])
                other_milliseconds = int(other_seconds_parts[1]) if len(other_seconds_parts) > 1 else 0
                
                other_total_seconds = other_minutes * 60 + other_seconds + other_milliseconds / 1000
            except:
                continue
            
            # Проверяем соответствие времени и места
            if position < other_position and total_seconds >= other_total_seconds:
                return False, f"Время {time_str} слишком медленное для места {position}. У участника на месте {other_position} время {other_time_str}"
            
            if position > other_position and total_seconds <= other_total_seconds:
                return False, f"Время {time_str} слишком быстрое для места {position}. У участника на месте {other_position} время {other_time_str}"
        
        return True, None

    def add_result(e):
        if not all([competition_dropdown.value, horse_dropdown.value, jockey_dropdown.value, position_field.value]):
            result_message.value = "Состязание, лошадь, жокей и место обязательны для заполнения"
            result_message.color = ft.Colors.RED
            page.update()
            return

        # Проверяем, что место является числом
        try:
            position = int(position_field.value)
            if position <= 0:
                result_message.value = "Место должно быть положительным числом"
                result_message.color = ft.Colors.RED
                page.update()
                return
        except ValueError:
            result_message.value = "Место должно быть числом"
            result_message.color = ft.Colors.RED
            page.update()
            return

        # Проверяем, не участвует ли лошадь уже в этом состязании
        if is_horse_already_in_competition(competition_dropdown.value, horse_dropdown.value):
            result_message.value = "Эта лошадь уже участвует в выбранном состязании!"
            result_message.color = ft.Colors.RED
            page.update()
            return

        # Проверяем, не занято ли уже это место в состязании
        if is_position_already_taken(competition_dropdown.value, position):
            result_message.value = f"Место {position} в этом состязании уже занято!"
            result_message.color = ft.Colors.RED
            page.update()
            return

        # Проверяем соответствие времени и места
        time_ok, time_error = is_time_consistent_with_position(
            competition_dropdown.value, position, time_field.value
        )
        if not time_ok:
            result_message.value = time_error
            result_message.color = ft.Colors.RED
            page.update()
            return

        # Добавление в базу данных
        query = """
            INSERT INTO race_participants 
            (competition_id, horse_id, jockey_id, position, finish_time) 
            VALUES (?, ?, ?, ?, ?)
        """
        params = (
            competition_dropdown.value, horse_dropdown.value, jockey_dropdown.value, 
            position, time_field.value or None
        )
        
        result = execute_query(query, params)
        
        if result is not None:
            result_message.value = "Результат успешно добавлен!"
            result_message.color = ft.Colors.GREEN
            
            # Очищаем поля
            horse_dropdown.value = None
            jockey_dropdown.value = None
            position_field.value = ""
            time_field.value = ""
        else:
            result_message.value = "Ошибка при добавлении результата"
            result_message.color = ft.Colors.RED
        
        page.update()

    return ft.Column([
        ft.Row([
            ft.Text("Добавление результатов состязания", size=20, weight=ft.FontWeight.BOLD),
            refresh_button  # Добавляем кнопку обновления рядом с заголовком
        ]),
        ft.Divider(),
        ft.Row([competition_dropdown], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([horse_dropdown, jockey_dropdown], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([position_field, time_field], alignment=ft.MainAxisAlignment.CENTER),
        ft.ElevatedButton("Добавить результат", on_click=add_result),
        result_message
    ], scroll=ft.ScrollMode.AUTO, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)

# Страница 6: Список состязаний каждого жокея
def page_jockey_competitions(page, user_role):
    if not check_permission(user_role, ["Пользователь", 'Жокей', 'Администратор']):
        return ft.Text("Доступ запрещен", size=20, color=ft.Colors.RED)

    def load_jockeys():
        query = "SELECT jockey_id, name FROM jockeys ORDER BY name"
        return execute_query(query) or []

    jockeys = load_jockeys()

    jockey_dropdown = ft.Dropdown(
        label="Выберите жокея",
        options=[ft.dropdown.Option(text=j['name'], key=j['jockey_id']) for j in jockeys],
        width=300
    )
    competitions_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Дата")),
            ft.DataColumn(ft.Text("Состязание")),
            ft.DataColumn(ft.Text("Лошадь")),
            ft.DataColumn(ft.Text("Место")),
            ft.DataColumn(ft.Text("Время")),
        ],
        rows=[]
    )
    result_message = ft.Text()

    def load_jockey_competitions(e):
        if not jockey_dropdown.value:
            result_message.value = "Выберите жокея"
            result_message.color = ft.Colors.RED
            page.update()
            return

        query = """
            SELECT c.date, c.title, h.name as horse_name, 
                   rp.position, rp.finish_time
            FROM race_participants rp
            JOIN competitions c ON rp.competition_id = c.competition_id
            JOIN horses h ON rp.horse_id = h.horse_id
            WHERE rp.jockey_id = ?
            ORDER BY c.date DESC
        """
        competitions = execute_query(query, (jockey_dropdown.value,)) or []

        competitions_table.rows.clear()
        if not competitions:
            competitions_table.rows.append(
                ft.DataRow(cells=[ft.DataCell(ft.Text("Нет данных о состязаниях"))])
            )
        else:
            for comp in competitions:
                position = comp['position'] if comp['position'] is not None else "Н/Ф"
                finish_time = comp['finish_time'] if comp['finish_time'] else "Н/Д"
                
                competitions_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(comp['date'])),
                            ft.DataCell(ft.Text(comp['title'] or "Без названия")),
                            ft.DataCell(ft.Text(comp['horse_name'])),
                            ft.DataCell(ft.Text(str(position))),
                            ft.DataCell(ft.Text(str(finish_time))),
                        ]
                    )
                )
        
        page.update()

    return ft.Column([
        ft.Text("Список состязаний жокея", size=20, weight=ft.FontWeight.BOLD),
        ft.Divider(),
        ft.Row([jockey_dropdown], alignment=ft.MainAxisAlignment.CENTER),
        ft.ElevatedButton("Показать состязания", on_click=load_jockey_competitions),
        ft.Container(
            content=competitions_table,
            padding=10,
            border=ft.border.all(1),
            border_radius=5,
        ),
        result_message
    ], scroll=ft.ScrollMode.AUTO, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)

# Страница 7: Список состязаний каждой лошади
def page_horse_competitions(page, user_role):
    if not check_permission(user_role, ["Пользователь", 'Жокей', 'Администратор']):
        return ft.Text("Доступ запрещен", size=20, color=ft.Colors.RED)

    def load_horses():
        query = "SELECT horse_id, name FROM horses ORDER BY name"
        return execute_query(query) or []

    horses = load_horses()

    horse_dropdown = ft.Dropdown(
        label="Выберите лошадь",
        options=[ft.dropdown.Option(text=h['name'], key=h['horse_id']) for h in horses],
        width=300
    )
    competitions_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Дата")),
            ft.DataColumn(ft.Text("Состязание")),
            ft.DataColumn(ft.Text("Жокей")),
            ft.DataColumn(ft.Text("Место")),
            ft.DataColumn(ft.Text("Время")),
        ],
        rows=[]
    )
    result_message = ft.Text()

    def load_horse_competitions(e):
        if not horse_dropdown.value:
            result_message.value = "Выберите лошадь"
            result_message.color = ft.Colors.RED
            page.update()
            return

        query = """
            SELECT c.date, c.title, j.name as jockey_name, 
                   rp.position, rp.finish_time
            FROM race_participants rp
            JOIN competitions c ON rp.competition_id = c.competition_id
            JOIN jockeys j ON rp.jockey_id = j.jockey_id
            WHERE rp.horse_id = ?
            ORDER BY c.date DESC
        """
        competitions = execute_query(query, (horse_dropdown.value,)) or []

        competitions_table.rows.clear()
        if not competitions:
            competitions_table.rows.append(
                ft.DataRow(cells=[ft.DataCell(ft.Text("Нет данных о состязаниях"))])
            )
        else:
            for comp in competitions:
                position = comp['position'] if comp['position'] is not None else "Н/Ф"
                finish_time = comp['finish_time'] if comp['finish_time'] else "Н/Д"
                
                competitions_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(comp['date'])),
                            ft.DataCell(ft.Text(comp['title'] or "Без названия")),
                            ft.DataCell(ft.Text(comp['jockey_name'])),
                            ft.DataCell(ft.Text(str(position))),
                            ft.DataCell(ft.Text(str(finish_time))),
                        ]
                    )
                )
        
        page.update()

    return ft.Column([
        ft.Text("Список состязаний лошади", size=20, weight=ft.FontWeight.BOLD),
        ft.Divider(),
        ft.Row([horse_dropdown], alignment=ft.MainAxisAlignment.CENTER),
        ft.ElevatedButton("Показать состязания", on_click=load_horse_competitions),
        ft.Container(
            content=competitions_table,
            padding=10,
            border=ft.border.all(1),
            border_radius=5,
        ),
        result_message
    ], scroll=ft.ScrollMode.AUTO, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)


# Главная функция приложения
def main(page: ft.Page):
    # Инициализация базы данных
    init_database()
    
    # Настройка страницы
    page.title = "Информационная система клуба любителей скачек"
    page.window.width = 1200
    page.window.height = 800
    page.window.min_width = 1000
    page.window.min_height = 700
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    
    # Переменные для хранения текущего состояния
    current_user = None
    current_tab_index = 0
    
    # Функция для выхода из системы
    def logout(e):
        nonlocal current_user
        current_user = None
        page.session.remove("user")
        show_login_page()
    
    # Функция для отображения страницы авторизации
    def show_login_page():
        page.clean()
        page.add(login_page(page))
        page.update()
    
    # Функция для отображения основной страницы
    def show_main_page():
        nonlocal current_user
        current_user = page.session.get("user")
        
        if not current_user:
            show_login_page()
            return
        
        user_role = current_user['role']
        
        # Создаем навигацию с вкладками в зависимости от роли
        tabs_list = [
            ft.Tab(
                text="Состязания",
                content=ft.Container(
                    content=page_competitions_list(page, user_role),
                    padding=10,
                    expand=True
                )
            ),
            ft.Tab(
                text="Состязания жокея",
                content=ft.Container(
                    content=page_jockey_competitions(page, user_role),
                    padding=10,
                    expand=True
                )
            ),
            ft.Tab(
                text="Состязания лошади",
                content=ft.Container(
                    content=page_horse_competitions(page, user_role),
                    padding=10,
                    expand=True
                )
            )
        ]
        
        # Добавляем вкладки для жокеев
        if user_role in ["Жокей", "Администратор"]:
            tabs_list.extend([
                ft.Tab(
                    text="Добавить жокея",
                    content=ft.Container(
                        content=page_add_jockey(page, user_role),
                        padding=10,
                        expand=True
                    )
                ),
                ft.Tab(
                    text="Добавить лошадь",
                    content=ft.Container(
                        content=page_add_horse(page, user_role),
                        padding=10,
                        expand=True
                    )
                )
            ])
        
        # Добавляем вкладки для администраторов
        if user_role == "Администратор":
            tabs_list.extend([
                ft.Tab(
                    text="Добавить состязание",
                    content=ft.Container(
                        content=page_add_competition(page, user_role),
                        padding=10,
                        expand=True
                    )
                ),
                ft.Tab(
                    text="Добавить результаты",
                    content=ft.Container(
                        content=page_add_competition_results(page, user_role),
                        padding=10,
                        expand=True
                    )
                )
            ])
        
        tabs = ft.Tabs(
            selected_index=current_tab_index,
            animation_duration=300,
            tabs=tabs_list,
            expand=True,
            on_change=lambda e: setattr(main, 'current_tab_index', e.control.selected_index)
        )
        
        header = ft.Row([
            ft.Text("Информационная система клуба любителей скачек", 
                   size=24, weight=ft.FontWeight.BOLD, expand=True),
            ft.Text(f"Пользователь: {current_user['username']} ({current_user['role']})", size=14),
            ft.IconButton(icon=ft.Icons.LOGOUT, tooltip="Выход", on_click=logout)
        ])
        
        page.clean()
        page.add(ft.Column([header, ft.Divider(), tabs], expand=True))
        page.update()
    
    # Функция для обработки входа в систему
    def handle_login(e):
        username_field = None
        password_field = None
        result_message = None
        
        # Находим элементы управления на странице
        for control in page.controls[0].content.controls:
            if isinstance(control, ft.TextField) and control.label == "Имя пользователя":
                username_field = control
            elif isinstance(control, ft.TextField) and control.label == "Пароль":
                password_field = control
            elif isinstance(control, ft.Text):
                result_message = control
        
        if username_field and password_field:
            user = check_auth(username_field.value, password_field.value)
            if user:
                page.session.set("user", user)
                show_main_page()
            elif result_message:
                result_message.value = "Неверное имя пользователя или пароль"
                result_message.color = ft.Colors.RED
                page.update()
    
    # Создаем страницу авторизации
    def login_page(page):
        username_field = ft.TextField(label="Имя пользователя", width=300)
        password_field = ft.TextField(
            label="Пароль", 
            password=True, 
            can_reveal_password=True,
            width=300
        )
        result_message = ft.Text()
        
        login_button = ft.ElevatedButton("Войти", on_click=handle_login)
        
        return ft.Container(
            content=ft.Column([
                ft.Text("Авторизация", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                username_field,
                password_field,
                login_button,
                result_message
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.alignment.center,
            expand=True
        )
    
    # Проверяем, есть ли уже авторизованный пользователь
    if page.session.contains_key("user"):
        show_main_page()
    else:
        show_login_page()


# Запуск приложения
if __name__ == "__main__":
    ft.app(target=main)