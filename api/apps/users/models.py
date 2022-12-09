from django.contrib.auth.base_user import BaseUserManager
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

from model_utils.models import UUIDModel, TimeStampedModel

from api.utils.mixins.models import UserMixin


class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifier for authentication instead of usernames
    """

    def create_user(self, email, password, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()

        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(PermissionsMixin, UUIDModel, TimeStampedModel, AbstractBaseUser):
    email = models.EmailField(
        'email address', max_length=255, unique=True, db_index=True
    )
    full_name = models.CharField('full name', max_length=255)
    short_name = models.CharField('short name', max_length=100)
    is_staff = models.BooleanField('staff status', default=False)
    is_active = models.BooleanField('active', default=True)
    last_login = models.DateTimeField(blank=True, null=True, editable=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'short_name']

    objects = CustomUserManager()

    def __str__(self) -> str:
        return f'{self.get_full_name()} {self.email}'

    def __repr__(self) -> str:
        return f'<User {self.email}>'

    def get_full_name(self) -> str:
        return self.full_name

    def get_short_name(self) -> str:
        return self.short_name

    def has_module_perms(self, app_label) -> bool:
        return True

    def has_perm(self, perm, obj=None) -> bool:
        return True

    def json(self):
        return {
            'id': f'{self.id}',
            'full_name': self.full_name,
            'short_name': self.short_name,
            'email': self.email,
            'last_login': f'{self.last_login}',
        }
