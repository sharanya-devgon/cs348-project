from django import forms
from .models import Transaction, Category, Account

class TransactionForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        required=True
    )
    account = forms.ModelChoiceField(
        queryset=Account.objects.none(),  # will fill dynamically
        required=True
    )

    class Meta:
        model = Transaction
        fields = ['account', 'category', 'amount', 'description', 'transaction_date']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['category'].queryset = Category.objects.filter(user=user)
            self.fields['account'].queryset = Account.objects.filter(user=user)

    def save(self, commit=True, user=None):
        transaction = super().save(commit=False)
        if user:
            transaction.user = user
        if commit:
            transaction.save()
        return transaction


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['name', 'balance']


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
