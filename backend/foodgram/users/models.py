from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models

from users.constants import EMAIL_LENGTH, USER_CONST
from users.validators import username_valdation


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'last_name', 'first_name']
    email = models.EmailField(
        max_length=EMAIL_LENGTH,
        unique=True,
        blank=False,
        verbose_name='Адрес электронной почты'
    )
    username = models.CharField(
        max_length=USER_CONST,
        blank=False,
        unique=True,
        verbose_name='Уникальный юзернейм',
        validators=[
            username_valdation
        ]
    )
    first_name = models.CharField(
        max_length=USER_CONST,
        blank=False,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=USER_CONST,
        blank=False,
        verbose_name='Фамилия'
    )
    password = models.CharField(
        max_length=USER_CONST,
        blank=False,
        verbose_name='Пароль'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        verbose_name='Аватар пользователя'
    )

    def __str__(self):
        return self.username


class Follow(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='follower'
    )
    following = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='following'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following'],
                name='unique_user_following'
            )
        ]
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'

    def clean(self):
        if self.user == self.following:
            raise ValidationError('Нельзя подписаться на самого себя')

    def __str__(self):
        return 'Подписки'
