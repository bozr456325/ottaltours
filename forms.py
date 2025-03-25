from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, TelField, SelectField
from wtforms.fields import EmailField
from wtforms.validators import DataRequired, Email, Length, InputRequired, Regexp, Optional

class ContactForm(FlaskForm):
    name = StringField(
        'Ваше имя*',
        validators=[
            DataRequired(message="Пожалуйста, укажите имя"),
            Length(min=2, max=50, message="Имя должно быть от 2 до 50 символов"),
            Regexp(
                r'^[а-яА-ЯёЁa-zA-Z\s\-]+$',
                message="Имя может содержать только буквы и дефисы"
            )
        ],
        render_kw={
            "placeholder": "Иван Иванов",
            "class": "form-control"
        }
    )

    email = EmailField(
        'Email*',
        validators=[
            DataRequired(message="Пожалуйста, укажите email"),
            Email(message="Введите корректный email адрес"),
            Length(max=100, message="Email слишком длинный")
        ],
        render_kw={
            "placeholder": "example@mail.com",
            "class": "form-control"
        }
    )

    phone = TelField(
        'Телефон*',
        validators=[
            InputRequired(message="Пожалуйста, укажите телефон"),
            Regexp(
                r'^\+?[0-9\s\-\(\)]{5,20}$',
                message="Введите корректный номер телефона"
            )
        ],
        render_kw={
            "placeholder": "+7 (999) 123-45-67",
            "class": "form-control"
        }
    )

    tour_interest = SelectField(
        'Интересующий тур',
        choices=[
            ('', 'Не выбрано'),
            ('turkey', 'Турция'),
            ('italy', 'Италия'),
            ('alps', 'Альпы'),
            ('other', 'Другое')
        ],
        validators=[Optional()],
        render_kw={
            "class": "form-control"
        }
    )

    message = TextAreaField(
        'Ваше сообщение*',
        validators=[
            DataRequired(message="Пожалуйста, напишите сообщение"),
            Length(min=10, max=500, message="Сообщение должно быть от 10 до 500 символов")
        ],
        render_kw={
            "placeholder": "Напишите здесь ваши пожелания...",
            "class": "form-control",
            "rows": 5
        }
    )

    def validate_phone(self, field):
        """Дополнительная валидация телефона"""
        phone = field.data
        # Удаляем все нецифровые символы, кроме плюса
        digits = ''.join(c for c in phone if c.isdigit() or c == '+')
        if len(digits) < 5:
            raise ValueError('Телефон слишком короткий')