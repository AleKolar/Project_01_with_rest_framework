from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from rest_framework import permissions
from rest_framework.routers import DefaultRouter
from . import views
from .views import registration_view, home, LoginUser, login_user, AdvertisementCreateView, \
    AdvertisementUpdateView, verify_code_view, display_news, CustomLogoutView, NewsCreateListAPIView
from django.urls import path
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.contrib import admin



# router = DefaultRouter()
# router.register(r'apicreate', NewsCreateAPIView, basename='news_create_api')

schema_view = get_schema_view(
    openapi.Info(
        title="New API",
        default_version='v1',
        url='http://localhost:8000/api/',
    ),
    public=True,

)


urlpatterns = [
    path('signup/', registration_view, name='registration'),
    # path('', login_user, name='login'),
    # path('login', login_user, name='login'),
    path('profile/', login_user, name='login_user'),
    path('', LoginUser.as_view(), name='login'),
    path('login/', LoginUser.as_view(), name='login'),
    path('verify/', verify_code_view, name='verify_code'),

    path('home/', home, name='home'),
    # path('accounts/home/', home, name='home'),

    path('user/responses/', views.user_responses, name='user_responses'),
    path('response/delete/<int:response_id>/', views.delete_response, name='delete_response'),
    path('response/accept/<int:response_id>/', views.accept_response, name='accept_response'),

    path('private/', views.user_responses, name='private'),

    path('advertisement_create/', AdvertisementCreateView.as_view(), name='advertisement_create'),
    path('create_response/<int:advertisement_id>/', views.create_response, name='response_create'),

    path('accounts/create_response/<int:advertisement_id>/', views.create_response, name='response_create'),
    path('create_response/<int:advertisement_id>/', views.create_response, name='create_response'),

    path('response/accept/<int:response_id>/', views.accept_response, name='accept_response'),
    path('accounts/create_response/<int:response_id>/', views.accept_response, name='accept_response'),
    path('accounts/accounts/create_response/<int:response_id>/', views.accept_response, name='accept_response'),


    path('advertisement/update/<int:pk>/', AdvertisementUpdateView.as_view(), name='advertisement_update'),

    path('news/', display_news, name='news_page'),

    path('logout/', CustomLogoutView.as_view(), name='logout'),

    path('apinews/', NewsCreateListAPIView.as_view(), name='rest_framework_form'),


    path('admin/', admin.site.urls),
    path('api/', TemplateView.as_view(template_name='rest_framework_api.html'), name='api-root'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

