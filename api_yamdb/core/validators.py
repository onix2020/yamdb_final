import re
from datetime import datetime

from rest_framework.exceptions import ValidationError


def validate_username(value):
    if value == 'me':
        raise ValidationError(
            'Недопустимое имя пользователя')
    pattern = re.compile(r'^[\w.@+-]+$')
    if not pattern.match(value):
        raise ValidationError(
            'Имя пользователя может содержать только буквы, цифры и @/./+/-/_')
    return value


def validate_year(value):
    if value < 0:
        raise ValidationError(
            'Год не может быть отрицательным')
    if value > datetime.now().year:
        raise ValidationError(
            'Год не может быть больше текущего')
    return value
