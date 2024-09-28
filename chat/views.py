import logging
import os
import random
import string
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.core.cache import cache
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from rest_framework import status
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView
from moviepy.video.io.VideoFileClip import VideoFileClip


from . import models
from .forms import RegistrationForm, ConfirmationForm, AdvertisementForm, ResponseForm

from django import forms

from .serializers import NewsSerializer
from .tasks import send_one_time_code_email, \
    send_response_email, send_accept_response_task, send_newsletter_task, send_confirmation_code
from .models import CustomUser
from django.conf import settings
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from .models import Advertisement
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import UpdateView

from .models import Newsletter


def generate_confirmation_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


def clean_email(self):
    email = self.cleaned_data['email']
    if CustomUser.objects.filter(email=email).exists():
        raise forms.ValidationError("Такой E-mail уже существует!")
    return email


# ПРОВЕРКА КООДА В БД
def confirm_code(request):
    if request.method == 'POST':
        form = ConfirmationForm(request.POST)
        if form.is_valid():
            code_entered = form.cleaned_data['code']
            user = request.user
            code_stored = user.customuser.code

            if code_entered == code_stored:

                return redirect('home')
            else:
                return redirect('registration')

    else:
        form = ConfirmationForm()

    return render(request, 'confirm_code_template.html', {'form': form})


# РЕГИСТРАЦИЯ
def registration_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            code = generate_confirmation_code()
            user.code = code
            expiration_time = timezone.now() + timedelta(seconds=300)
            user.code_expiration = expiration_time
            user.save()

            send_one_time_code_email.delay(user.pk)

            # Аутентификация пользователя после регистрации
            user = authenticate(username=user.username, password=form.cleaned_data['password'])
            login(request, user)

            print(f'One-time code generated: {code}')

            return render(request, 'verify_code.html', {'form': form})
        else:
            return render(request, 'registration.html', {'form': form})
    else:
        form = RegistrationForm()
        return render(request, 'registration.html', {'form': form})


# ВХОД (АВТОРИЗАЦИЯ)
class LoginUser(LoginView):
    form_class = AuthenticationForm
    template_name = 'login.html'
    extra_context = {'title': "Авторизация"}

    def form_valid(self, form):
        response = super().form_valid(form)

        user = self.request.user
        code = generate_confirmation_code()
        user.code = code
        user.save()
        send_confirmation_code.delay(user.id)

        return redirect('verify_code')


# ОТПРАВЛЯЕТ КОД НА ПОЧТУ
def login_user(request):
    if request.user.is_authenticated:
        user = request.user

        send_confirmation_code.delay(user.pk)
        print(f'Confirmation code sent to user: {user.code}')

        return redirect('verify_code_view')

    return render(request, 'login.html', {'form': AuthenticationForm()})


# ВВОДИМ КОД ПОДТВЕРЖДЕНИЯ
def verify_code_view(request):
    if request.method == 'POST':
        code = request.POST.get('code')
        try:
            user = CustomUser.objects.get(code=code)
            user.is_verified = True
            user.save()
            return redirect('home')
        except CustomUser.DoesNotExist:
            return HttpResponse("Invalid code entered. Please try again.", status=400)

    return render(request, 'verify_code.html')


# ЗАРЕГИСТРИРОВАННЫХ НАДЕЛЯЕМ ПОЛНОМОЧИЯМИ
# ДОМАШНЯЯ
from django.db.models import Q


def home(request):
    all_responses = models.Response.objects.filter(accepted=True, visible_to_all=True)
    all_advertisements = Advertisement.objects.all().order_by('-id')
    admin_news = Newsletter.objects.filter(sent_date__isnull=False)
    user = request.user
    paginator = Paginator(all_advertisements, 10)
    page = request.GET.get('page')

    try:
        all_advertisements = paginator.page(page)
    except PageNotAnInteger:
        all_advertisements = paginator.page(1)
    except EmptyPage:
        all_advertisements = paginator.page(paginator.num_pages)

    return render(request, 'home.html',
                  {'all_responses': all_responses, 'all_advertisements': all_advertisements, 'admin_news': admin_news,
                   'user': user})


logger = logging.getLogger(__name__)


# СОЗДАЕМ ОБЪЯВЛЕНИЕ

class AdvertisementCreateView(LoginRequiredMixin, CreateView):
    model = Advertisement
    fields = ['title', 'text', 'category', 'image', 'video']
    template_name = 'advertisement_create.html'

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    # @staticmethod
    # def resize_image(image, output_path, width, height):
    #     img = Image.open(image)
    #     img_resized = img.resize((width, height))
    #     img_resized.save(output_path)
    #
    # @staticmethod
    # def resize_video(video, output_path, width, height):
    #     video = VideoFileClip(video.temporary_file_path())
    #     video_resized = video.resize(width=width, height=height)
    #     video_resized.write_videofile(output_path)

    def form_valid(self, form):
        form.instance.user_id = self.request.user.id
        category = form.cleaned_data.get('category')
        valid_categories = ['Tanks', 'Healers', 'DPS', 'Traders', 'Guild Masters', 'Quest Givers', 'Blacksmiths',
                            'Leatherworkers', 'Alchemists', 'Spellcasters']

        if category not in valid_categories:
            form.add_error('category',
                           'Выберите категорию из списка: Танки, Хилы, ДД, Торговцы, Гилдмастеры, Квестгиверы, Кузнецы, Кожевники, Зельевары, Мастера заклинаний')
            return self.form_invalid(form)

        return super().form_valid(form)

    success_url = reverse_lazy('home')


# ШАБЛОН РЕДАКТИРОВАНИЯ ОБЪЯВЛЕНИЙ
class AdvertisementUpdateView(LoginRequiredMixin, UpdateView):
    model = Advertisement
    fields = ['title', 'text', 'category', 'image', 'video']
    template_name = 'advertisement_update.html'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.user != self.request.user:
            return HttpResponse("Вы не являетесь автором этого объявления", status=403)
        return super().dispatch(request, *args, **kwargs)

    # @staticmethod
    # def resize_image(image, output_path, width, height):
    #     from PIL import Image
    #     img = Image.open(image)
    #     img_resized = img.resize((width, height))
    #     img_resized.save(output_path)
    #
    # @staticmethod
    # def resize_video(video, output_path, width, height):
    #     video = VideoFileClip(video.temporary_file_path())
    #     video_resized = video.resize(width=width, height=height)
    #     video_resized.write_videofile(output_path)

    def form_valid(self, form):
        form.instance.user_id = self.request.user.id
        category = form.cleaned_data.get('category')
        valid_categories = ['Tanks', 'Healers', 'DPS', 'Traders', 'Guild Masters', 'Quest Givers', 'Blacksmiths',
                            'Leatherworkers', 'Alchemists', 'Spellcasters']

        if category not in valid_categories:
            form.add_error('category',
                           'Выберите категорию из списка: Танки, Хилы, ДД, Торговцы, Гилдмастеры, Квестгиверы, Кузнецы, Кожевники, Зельевары, Мастера заклинаний')
            return self.form_invalid(form)

        images_path = os.path.join(settings.MEDIA_ROOT, 'images')
        os.makedirs(images_path, exist_ok=True)

        videos_path = os.path.join(settings.MEDIA_ROOT, 'videos')
        os.makedirs(videos_path, exist_ok=True)

        # Замена изображения, если выбрано новое изображение
        if self.request.FILES.get('new_image'):
            new_image = self.request.FILES.get('new_image')
            new_image_output_path = os.path.join(images_path, new_image.name)
            self.resize_image(new_image, new_image_output_path, 640, 480)
            form.instance.image = new_image_output_path

        # Замена видео, если выбрано новое видео
        if self.request.FILES.get('new_video'):
            new_video = self.request.FILES.get('new_video')
            new_video_output_path = os.path.join(videos_path, new_video.name)
            self.resize_video(new_video, new_video_output_path, 640, 480)
            form.instance.video = new_video_output_path

        return super().form_valid(form)

    success_url = reverse_lazy('home')


# ДЛЯ ФИЛЬТРАЦИИ ОТКЛИКОВ ПОЛЬЗ-ЛЯ
def user_responses(request, advertisement_id=None):
    form = AdvertisementForm()
    user_id = request.user.id
    user_advertisements = Advertisement.objects.filter(user_id=user_id)
    user_responses = models.Response.objects.filter(advertisement__in=user_advertisements)

    title = request.GET.get('title')
    category = request.GET.get('category')

    if title:
        user_responses = user_responses.filter(advertisement__title__icontains=title)

    if category:
        user_responses = user_responses.filter(advertisement__category=category)

    if advertisement_id:
        user_responses = user_responses.filter(advertisement_id=advertisement_id)

    user_responses = user_responses.order_by('-id')

    return render(request, 'private.html',
                  {'form': form, 'user_responses': user_responses, 'user_advertisements': user_advertisements})


# СОЗДАЮ ОТКЛИК
@login_required
def create_response(request, advertisement_id):
    advertisement = get_object_or_404(Advertisement, id=advertisement_id)

    if request.method == 'POST':
        form = ResponseForm(request.POST)

        if form.is_valid():
            text = form.cleaned_data['content']
            user = request.user
            response = models.Response(user=user, advertisement=advertisement, content=text)
            response.save()
            response.advertisement.responses.add(response)
            response.save()
            send_response_email.delay(advertisement_id, text)
            return redirect('home')
    else:
        form = ResponseForm()

    return render(request, 'create_response.html', {'form': form, 'advertisement_id': advertisement_id})


def delete_response(request, response_id):
    response = get_object_or_404(Response, id=response_id)
    response.delete()

    cache.clear()  # Очистка кэша

    return redirect('private')


def accept_response(request, response_id):
    response = models.Response.objects.get(id=response_id)

    if request.user == response.advertisement.user:
        response.accepted = True
        response.visible_to_all = True
        response.save()

        # Отправка уведомления пользователю, оставившему отклик
        notification_message = "Ваш отклик был принят!"
        send_accept_response_task.delay(response_id, notification_message)

    return redirect('home')


# СОЗДАЕМ НОВОСТЬ
class AdminOnlyPermission(BasePermission):
    def has_permission(self, request, view):
        # Проверяем, является ли пользователь администратором
        return request.user and request.user.is_staff


class NewsCreateListAPIView(APIView):
    permission_classes = [AdminOnlyPermission]

    def post(self, request):
        serializer = NewsSerializer(data=request.data)
        if serializer.is_valid():
            newsletter_instance = serializer.save()
            send_newsletter_task.delay(newsletter_instance.id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        newsletters = Newsletter.objects.all()
        serializer = NewsSerializer(newsletters, many=True)
        return Response(serializer.data)


# class NewsletterCreateAPIView(APIView):
#     def post(self, request):
#         serializer = NewsletterSerializer(data=request.data)
#         if serializer.is_valid():
#             newsletter = serializer.save()
#             send_newsletter_task.delay(newsletter.id)
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def display_news(request):
    all_news = Newsletter.objects.all().order_by('-sent_date')  # Получаем все новости из базы данных
    context = {'all_news': all_news}
    return render(request, 'news_page.html', context)


class CustomLogoutView(TemplateView):
    template_name = 'logout.html'

    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect('login')
