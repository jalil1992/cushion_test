from django.contrib import admin

from .models import Account, Transaction

# Register your models here.


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "balance_cents", "settled_balance_cents", "status")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "account", "merchant_name", "created_at", "amount_cents", "settled_amount_cents", "status")
