from django.db import models
from django.utils.translation import gettext_lazy as _


class AccountStatus(models.TextChoices):
    current = "current", _("current")
    delinquent = "delinquent", _("delinquent")
    closed = "closed", _("closed")


class TransactionStatus(models.TextChoices):
    pending = "pending", _("pending")
    posted = "posted", _("posted")


class Account(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    negative_since = models.DateTimeField(default=None, null=True)
    balance_cents = models.IntegerField(default=0)
    settled_balance_cents = models.IntegerField(default=0)
    status = models.CharField(max_length=32, choices=AccountStatus.choices, default=AccountStatus.current)


class Transaction(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="transactions", null=True)
    amount_cents = models.IntegerField(default=0)
    merchant_name = models.CharField(max_length=200, default="")
    status = models.CharField(max_length=32, choices=TransactionStatus.choices, default=TransactionStatus.pending)
    settled_amount_cents = models.IntegerField(default=0)
    ip = models.CharField(max_length=32, default="")
