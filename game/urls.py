from django.urls import path
from . import views

app_name = 'game'

urlpatterns = [
    path('', views.game_list, name='game_list'),
    path('<str:slug>/', views.game_detail, name='game_detail'),
    path('<str:slug>/like/', views.like_game, name='like_game'),
]