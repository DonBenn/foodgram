from django.urls import path
from short_url import views

app_name = 'short_url'

urlpatterns = [
    path('<str:index>/', views.redirect_url, name='redirect_url')
]
