import json
from datetime import datetime
from time import sleep

import pytz
from django.urls import reverse
from rest_framework.test import APITransactionTestCase

from api.models import Account, AccountStatus, Transaction, TransactionStatus


class TestAll(APITransactionTestCase):
    def setUp(self) -> None:
        # create account
        self.account = Account.objects.create()
        super().setUp()

    def reload_state(self):
        self.account = Account.objects.get(pk=self.account.id)
        self.trans = Transaction.objects.first()

    def reset_state(self):
        self.account.balance_cents = 0
        self.account.settled_balance_cents = 0
        self.account.status = AccountStatus.current
        self.account.negative_since = None
        self.account.save()
        Transaction.objects.all().delete()

    def test_get_accounts(self):
        # reset
        self.reset_state()

        response = self.client.get(reverse("list_accounts"))
        self.assertTrue(response.status_code == 200)
        res_json = response.json()
        self.assertTrue(len(res_json) == 1)
        self.assertTrue(res_json[0]["balance_cents"] == 0)
        self.assertTrue(res_json[0]["settled_balance_cents"] == 0)
        self.assertTrue(res_json[0]["status"] == "current")

    def test_payments(self):
        # reset
        self.reset_state()
        # +100
        response = self.client.post(reverse("payments"), data={"amount_cents": 100, "account_id": self.account.id, "merchant_name": "TestM"})
        self.assertTrue(response.status_code == 201)
        self.reload_state()
        self.assertTrue(self.account.balance_cents == 100)
        self.assertTrue(self.account.settled_balance_cents == 0)
        self.assertTrue(self.trans.status == "pending")
        self.assertTrue(self.trans.amount_cents == 100)
        self.assertTrue(self.trans.settled_amount_cents == 0)

        # call back 100, pending
        response = self.client.post(reverse("transaction_callback"), data={"amount_cents": 100, "money_movement_id": self.trans.id, "status": "pending"})
        self.assertTrue(response.status_code == 201)
        self.reload_state()
        self.assertTrue(self.account.balance_cents == 100)
        self.assertTrue(self.account.settled_balance_cents == 0)
        self.assertTrue(self.trans.status == "pending")
        self.assertTrue(self.trans.amount_cents == 100)
        self.assertTrue(self.trans.settled_amount_cents == 0)

        # call back 50, pending
        response = self.client.post(reverse("transaction_callback"), data={"amount_cents": 50, "money_movement_id": self.trans.id, "status": "pending"})
        self.assertTrue(response.status_code == 201)
        self.reload_state()
        self.assertTrue(self.account.balance_cents == 100)
        self.assertTrue(self.account.settled_balance_cents == 0)
        self.assertTrue(self.trans.status == "pending")
        self.assertTrue(self.trans.amount_cents == 100)
        self.assertTrue(self.trans.settled_amount_cents == 0)

        # call back 50, posted
        response = self.client.post(reverse("transaction_callback"), data={"amount_cents": 50, "money_movement_id": self.trans.id, "status": "posted"})
        self.assertTrue(response.status_code == 201)
        self.reload_state()
        self.assertTrue(self.account.settled_balance_cents == 50)
        self.assertTrue(self.trans.status == "posted")
        self.assertTrue(self.trans.settled_amount_cents == 50)

        # call back 0, pending
        response = self.client.post(reverse("transaction_callback"), data={"amount_cents": 0, "money_movement_id": self.trans.id, "status": "pending"})
        self.assertTrue(response.status_code == 201)
        self.reload_state()
        self.assertTrue(self.account.settled_balance_cents == 0)
        self.assertTrue(self.trans.status == "pending")
        self.assertTrue(self.trans.settled_amount_cents == 0)

        # call back 50, posted
        response = self.client.post(reverse("transaction_callback"), data={"amount_cents": 50, "money_movement_id": self.trans.id, "status": "posted"})
        self.assertTrue(response.status_code == 201)
        self.reload_state()
        self.assertTrue(self.account.settled_balance_cents == 50)
        self.assertTrue(self.trans.status == "posted")
        self.assertTrue(self.trans.settled_amount_cents == 50)

        # call back 50, posted
        response = self.client.post(reverse("transaction_callback"), data={"amount_cents": 50, "money_movement_id": self.trans.id, "status": "posted"})
        self.assertTrue(response.status_code == 201)
        self.reload_state()
        self.assertTrue(self.account.settled_balance_cents == 50)
        self.assertTrue(self.trans.status == "posted")
        self.assertTrue(self.trans.settled_amount_cents == 50)

        # call back 100, posted
        response = self.client.post(reverse("transaction_callback"), data={"amount_cents": 100, "money_movement_id": self.trans.id, "status": "posted"})
        self.assertTrue(response.status_code == 201)
        self.reload_state()
        self.assertTrue(self.account.settled_balance_cents == 100)
        self.assertTrue(self.trans.status == "posted")
        self.assertTrue(self.trans.settled_amount_cents == 100)

    def test_payments_after_settle_time(self):
        # reset
        self.reset_state()

        # +100
        response = self.client.post(reverse("payments"), data={"amount_cents": 100, "account_id": self.account.id, "merchant_name": "TestM"})
        self.assertTrue(response.status_code == 201)
        self.reload_state()
        self.assertTrue(self.account.balance_cents == 100)
        self.assertTrue(self.account.settled_balance_cents == 0)
        self.assertTrue(self.trans.status == "pending")
        self.assertTrue(self.trans.amount_cents == 100)
        self.assertTrue(self.trans.settled_amount_cents == 0)

        # modify transaction time limit
        self.trans.time_to_settle_seconds = 3
        self.trans.save()

        # call back 50, posted in time
        response = self.client.post(reverse("transaction_callback"), data={"amount_cents": 50, "money_movement_id": self.trans.id, "status": "posted"})
        self.assertTrue(response.status_code == 201)
        self.reload_state()
        self.assertTrue(self.account.settled_balance_cents == 50)
        self.assertTrue(self.trans.status == "posted")
        self.assertTrue(self.trans.settled_amount_cents == 50)

        # call back 100, posted late
        sleep(3)
        response = self.client.post(reverse("transaction_callback"), data={"amount_cents": 100, "money_movement_id": self.trans.id, "status": "posted"})
        self.assertTrue(response.status_code == 406)

    def test_recalculate(self):
        # reset
        self.reset_state()
        # -100
        response = self.client.post(reverse("payments"), data={"amount_cents": -100, "account_id": self.account.id, "merchant_name": "TestM"})
        self.assertTrue(response.status_code == 201)
        self.reload_state()
        self.assertTrue(self.account.balance_cents == -100)
        self.assertTrue(self.account.settled_balance_cents == 0)
        self.assertTrue(self.trans.status == "pending")
        self.assertTrue(self.trans.amount_cents == -100)
        self.assertTrue(self.trans.settled_amount_cents == 0)

        # call back -100, posted
        response = self.client.post(reverse("transaction_callback"), data={"amount_cents": -100, "money_movement_id": self.trans.id, "status": "posted"})
        self.assertTrue(response.status_code == 201)
        self.reload_state()
        self.assertTrue(self.account.settled_balance_cents == -100)
        self.assertTrue(self.trans.status == "posted")
        self.assertTrue(self.trans.settled_amount_cents == -100)

        # check recalculate without sleep
        response = self.client.patch(reverse("recalculate") + "?time_to_delinquency_seconds=3")
        self.assertTrue(response.status_code == 200)
        self.reload_state()
        self.assertTrue(self.account.status == AccountStatus.current)

        # sleep and call recalculate
        sleep(3)
        response = self.client.patch(reverse("recalculate") + "?time_to_delinquency_seconds=3")
        self.assertTrue(response.status_code == 200)
        self.reload_state()
        self.assertTrue(self.account.status == AccountStatus.delinquent)
