
from django.urls import path
from .views import upload_image_api


urlpatterns = [
    path('api/upload/', upload_image_api, name='upload_api'),

]

