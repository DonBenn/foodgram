from django.urls import path
from short_url import views


urlpatterns = [
    path('<str:index>/', views.redirect_url, name='redirect_url')
]
