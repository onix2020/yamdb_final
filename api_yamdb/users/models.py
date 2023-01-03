from core.validators import validate_username
from django.contrib.auth.models import AbstractUser
from django.db import models

ROLES = (
    ('user', 'user'),
    ('moderator', 'moderator'),
    ('admin', 'admin'),
)


class User(AbstractUser):
    username = models.CharField(
        'Имя пользователя',
        max_length=150,
        unique=True,
        validators=[validate_username],
    )
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    role = models.CharField(
        max_length=20,
        choices=ROLES,
        default='user',
        verbose_name='Роль'
    )
    confirmation_code = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(
        max_length=254,
        unique=True
    )

    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username

    @property
    def is_admin(self):
        return self.role == "admin" or self.is_superuser

    @property
    def is_moderator(self):
        return self.role == "moderator"

    @property
    def is_user(self):
        return self.role == "user"
