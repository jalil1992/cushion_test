from django.urls import path

from . import views

urlpatterns = [
    path("", views.HomeView.as_view()),
    path("accounts/", views.AccountListView.as_view(), name="list_accounts"),
    path("accounts/recalculate/", views.RecalculateAccountsView.as_view(), name="recalculate"),
    path("payments/", views.PaymentCreateView.as_view(), name="payments"),
    path("money_movement_request_callback/", views.TransactionCallbackView.as_view(), name="transaction_callback"),
]
