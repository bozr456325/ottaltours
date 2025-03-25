from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
import requests
from datetime import datetime

# Загрузка переменных окружения
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tours.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Telegram настройки
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

db = SQLAlchemy(app)


# Модель "Тур"
class Tour(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    duration = db.Column(db.String(50), nullable=False)
    image = db.Column(db.String(100), nullable=False)


# Создание БД
@app.cli.command("init-db")
def init_db():
    db.create_all()
    if not Tour.query.first():
        tours_data = [
            Tour(title='Отдых в Турции',
                 description='Прекрасный отдых на берегу Средиземного моря',
                 price=45000, duration='7 дней', image='turkey.jpg'),
            Tour(title='Экскурсия по Италии',
                 description='Путешествие по самым красивым городам Италии',
                 price=78000, duration='10 дней', image='italy.jpg'),
            Tour(title='Горнолыжный курорт в Альпах',
                 description='Катание на лыжах в лучших курортах Швейцарии',
                 price=92000, duration='8 дней', image='alps.jpg')
        ]
        db.session.add_all(tours_data)
        db.session.commit()
    print("БД создана и заполнена тестовыми данными!")

def send_telegram_notification(name, phone, message):
    """Отправка уведомления в Telegram с корректной обработкой номера"""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Ошибка: Не настроены параметры Telegram")
        return False

    # 1. Очищаем номер от всего, кроме цифр
    clean_phone = ''.join(c for c in phone if c.isdigit())

    # 2. Определяем, российский ли номер (начинается на 7, 8 или +7)
    is_russian = (
        clean_phone.startswith('7') or
        clean_phone.startswith('8') or
        phone.lstrip('+').startswith('7')
    )

    # 3. Обрабатываем российские номера
    if is_russian:
        if clean_phone.startswith('8') and len(clean_phone) == 11:
            clean_phone = '7' + clean_phone[1:]  # Превращаем 89... в 79...
        elif len(clean_phone) == 10:
            clean_phone = '7' + clean_phone  # Добавляем 7, если её нет
        elif clean_phone.startswith('7') and len(clean_phone) > 11:
            clean_phone = clean_phone.lstrip('7')  # Убираем лишние 7

    # 4. Форматируем для отображения (только для российских номеров)
    if is_russian and len(clean_phone) == 11 and clean_phone.startswith('7'):
        formatted_phone = f"+7 ({clean_phone[1:4]}) {clean_phone[4:7]}-{clean_phone[7:9]}-{clean_phone[9:]}"
    else:
        formatted_phone = phone  # Оставляем исходный формат для иностранных номеров

    # 5. Создаем кнопки (только для российских номеров)
    keyboard = None
    if is_russian and len(clean_phone) == 11:
        keyboard = {
            "inline_keyboard": [
                [
                    {
                        "text": "📞 Позвонить через Telegram",
                        "url": f"https://t.me/+7{clean_phone[1:]}"  # +79XXXXXXXXX
                    },
                    {
                        "text": "💬 WhatsApp",
                        "url": f"https://wa.me/7{clean_phone[1:]}"  # 79XXXXXXXXX
                    }
                ]
            ]
        }

    # 6. Отправляем сообщение
    text = f"""
<b>🚀 Новая заявка с сайта</b>
┌ <b>Имя:</b> {name}
├ <b>Телефон:</b> <code>{formatted_phone}</code>
└ <b>Сообщение:</b> {message}

<i>🕒 {datetime.now().strftime('%d.%m.%Y %H:%M')}</i>
    """

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={
                'chat_id': TELEGRAM_CHAT_ID,
                'text': text,
                'parse_mode': 'HTML',
                'reply_markup': keyboard,
                'disable_web_page_preview': True
            },
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Ошибка отправки: {str(e)}")
        return False

# Роуты
@app.route('/get-chat-id')
def get_chat_id():
    updates_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    try:
        response = requests.get(updates_url)
        return f"Ваши обновления: {response.json()}"
    except Exception as e:
        return f"Ошибка: {str(e)}"


@app.route('/')
def index():
    featured_tours = Tour.query.limit(3).all()
    return render_template('index.html', featured_tours=featured_tours)


@app.route('/tours')
def tours_page():
    all_tours = Tour.query.all()
    return render_template('tours.html', tours=all_tours)


@app.route('/tour/<int:tour_id>')
def tour_detail(tour_id):
    tour = Tour.query.get_or_404(tour_id)
    return render_template('tour_detail.html', tour=tour)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        message = request.form.get('message')

        if send_telegram_notification(name, phone, message):
            return render_template('contact.html', success=True)
        else:
            return render_template('contact.html', error=True)

    return render_template('contact.html')


@app.route('/terms')
def terms():
    return render_template('legal/terms.html', title='Пользовательское соглашение')


@app.route('/privacy')
def privacy():
    return render_template('legal/privacy.html', title='Политика конфиденциальности')


@app.route('/personal-data')
def personal_data():
    return render_template('legal/personal_data.html', title='Политика обработки персональных данных')


if __name__ == '__main__':
    app.run(debug=True)