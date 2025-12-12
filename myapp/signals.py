from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Transaction

@receiver(post_save, sender=Transaction)
def update_account_balance_on_save(sender, instance, created, **kwargs):
    account = instance.account
    category = instance.category

    # Determine direction: positive transaction should DECREASE balance
    if created:
        account.balance -= instance.amount
    else:
        # When updating, find the previous amount to adjust the difference
        try:
            old_instance = Transaction.objects.get(pk=instance.pk)
            diff = instance.amount - old_instance.amount
            account.balance -= diff  # subtract change in amount
        except Transaction.DoesNotExist:
            pass

    account.save()


@receiver(post_delete, sender=Transaction)
def update_account_balance_on_delete(sender, instance, **kwargs):
    account = instance.account
    # Deleting transaction restores balance
    account.balance += instance.amount
    account.save()
