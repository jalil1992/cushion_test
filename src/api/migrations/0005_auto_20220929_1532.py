# Generated by Django 3.2.12 on 2022-09-29 19:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_alter_transaction_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='time_to_settle_seconds',
            field=models.IntegerField(default=10),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='status',
            field=models.CharField(choices=[('pending', 'pending'), ('posted', 'posted'), ('none', 'none')], default='none', max_length=32),
        ),
    ]