# Generated by Django 3.2.12 on 2022-09-29 17:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_auto_20220929_1306'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='status',
            field=models.CharField(choices=[('pending', 'pending'), ('posted', 'posted'), ('expired', 'expired')], default='pending', max_length=32),
        ),
    ]
