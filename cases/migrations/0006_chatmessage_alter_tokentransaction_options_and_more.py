# Generated by Django 4.2 on 2025-05-19 08:32

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('cases', '0005_rename_notification_casenotification'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChatMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField()),
                ('response', models.TextField(blank=True, null=True)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('is_user_message', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['timestamp'],
            },
        ),
        migrations.AlterModelOptions(
            name='tokentransaction',
            options={'verbose_name': 'Token Transaction', 'verbose_name_plural': 'Token Transactions'},
        ),
        migrations.AlterModelOptions(
            name='userwallet',
            options={'verbose_name': 'User Wallet', 'verbose_name_plural': 'User Wallets'},
        ),
        migrations.AddField(
            model_name='tokentransaction',
            name='external_tx_id',
            field=models.CharField(blank=True, help_text='Blockchain or Paystack transaction ID', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='userwallet',
            name='eth_address',
            field=models.CharField(blank=True, help_text='Ethereum address for crypto redemptions (e.g., 0x...)', max_length=42, null=True),
        ),
        migrations.AddField(
            model_name='userwallet',
            name='phone_number',
            field=models.CharField(blank=True, help_text='Phone number for M-Pesa redemptions (e.g., +2547xxxxxxxx)', max_length=15, null=True),
        ),
        migrations.AlterField(
            model_name='tokentransaction',
            name='case',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='token_transactions', to='cases.case'),
        ),
        migrations.AlterField(
            model_name='tokentransaction',
            name='description',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='tokentransaction',
            name='transaction_type',
            field=models.CharField(choices=[('earn', 'Earned'), ('spend', 'Spent'), ('adjust', 'Adjustment')], max_length=10),
        ),
        migrations.AddIndex(
            model_name='tokentransaction',
            index=models.Index(fields=['user', 'created_at'], name='cases_token_user_id_3f1c5f_idx'),
        ),
        migrations.AddIndex(
            model_name='tokentransaction',
            index=models.Index(fields=['case'], name='cases_token_case_id_1528f8_idx'),
        ),
        migrations.AddField(
            model_name='chatmessage',
            name='case',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='cases.case'),
        ),
        migrations.AddField(
            model_name='chatmessage',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='case_chat_messages', to=settings.AUTH_USER_MODEL),
        ),
    ]
