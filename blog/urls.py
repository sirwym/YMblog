from django.urls import path
from . import views


app_name = "blog"

urlpatterns = [
    # 博客列表页 (对应 /blog/)
    path("", views.post_list, name="post_list"),

    # (预留) 博客详情页 - 我们下一步会写这个
    path("<str:slug>/", views.post_detail, name="post_detail"),
]