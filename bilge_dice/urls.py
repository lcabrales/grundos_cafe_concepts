from django.urls import path
from bilge_dice import views

urlpatterns = [
    path("", views.home, name='home'),
]