from django.conf import settings
from django.contrib.auth.models import User, AbstractUser
from django.db import models
from ckeditor.fields import RichTextField


class CustomUser(AbstractUser):
    code = models.CharField(max_length=6, blank=True, null=True)
    is_verified = models.BooleanField(default=False)

    class Meta:
        swappable = 'AUTH_USER_MODEL'


class Group(models.Model):
    custom_user_set = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='custom_user_groups')


class Permission(models.Model):
    custom_user_set = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='custom_user_permissions')


class Advertisement(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    text = models.TextField()
    image = models.ImageField(upload_to='images/', blank=True, null=True)
    video = models.FileField(upload_to='videos/', blank=True, null=True)
    content = RichTextField()
    category_choices = [
        ('Tanks', 'Танки'),
        ('Healers', 'Хилы'),
        ('DPS', 'ДД'),
        ('Traders', 'Торговцы'),
        ('Guild Masters', 'Гилдмастеры'),
        ('Quest Givers', 'Квестгиверы'),
        ('Blacksmiths', 'Кузнецы'),
        ('Leatherworkers', 'Кожевники'),
        ('Alchemists', 'Зельевары'),
        ('Spellcasters', 'Мастера заклинаний'),
    ]
    category = models.CharField(max_length=20, choices=category_choices)


    def __str__(self):
        return self.title


class Response(models.Model):
    objects = models.Manager()
    advertisement = models.ForeignKey(Advertisement, on_delete=models.CASCADE, related_name='responses')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    accepted = models.BooleanField(default=False)
    visible_to_all = models.BooleanField(default=False)

    def __str__(self):
        return f'Response to {self.advertisement.title}'


class Newsletter(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    recipients = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='newsletters')
    sent_date = models.DateTimeField(auto_now_add=True)
