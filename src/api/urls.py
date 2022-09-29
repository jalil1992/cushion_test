from django.urls import path

from . import views

urlpatterns = [
    path("", views.HomeView.as_view()),
    path("accounts", views.AccountListView.as_view()),
    path("payments", views.PaymentCreateView.as_view()),
]
