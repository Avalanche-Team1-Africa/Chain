from django.db import transaction
from cases.models import UserWallet, TokenTransaction
from django.contrib.auth.models import User

def award_tokens(user, amount, description, case=None):
    """
    Award tokens to a user and record the transaction.
    """
    with transaction.atomic():
        # Get or create user wallet
        wallet, created = UserWallet.objects.get_or_create(user=user)
        
        # Update wallet balance
        wallet.balance += amount
        wallet.save()
        
        # Record transaction
        TokenTransaction.objects.create(
            user=user,
            amount=amount,
            transaction_type='EARN',
            description=description,
            case=case
        )