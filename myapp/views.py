from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import TransactionForm, AccountForm, CategoryForm
from django.shortcuts import render
from .models import Transaction, Account, Category
from datetime import datetime
from django.db.models import Sum, Avg, Count
from django.db import transaction


@login_required
def transaction_list(request):
    transactions = Transaction.objects.filter(user=request.user)
    return render(request, 'myapp/transaction_list.html', {'transactions': transactions})


@login_required
def transaction_create(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST, user=request.user)
        if form.is_valid():
            with transaction.atomic():
                account = Account.objects.select_for_update().get(
                    id=form.cleaned_data['account'].id,
                    user=request.user
                )

                t = form.save(commit=False)
                t.user = request.user
                t.save()

                account.balance += t.amount
                account.save()

            return redirect('transaction_list')
    else:
        form = TransactionForm(user=request.user)
    return render(request, 'myapp/transaction_form.html', {'form': form})

@login_required
def transaction_edit(request, pk):
    transaction_obj = get_object_or_404(Transaction, pk=pk, user=request.user)
    old_amount = transaction_obj.amount
    old_account = transaction_obj.account

    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction_obj, user=request.user)
        if form.is_valid():
            with transaction.atomic():
                updated = form.save(commit=False)

                old_acc_locked = Account.objects.select_for_update().get(id=old_account.id)
                new_acc_locked = Account.objects.select_for_update().get(id=updated.account.id)

                if old_account != updated.account:
                    old_acc_locked.balance -= old_amount
                    old_acc_locked.save()

                    new_acc_locked.balance += updated.amount
                    new_acc_locked.save()

                else:
                    diff = updated.amount - old_amount
                    new_acc_locked.balance += diff
                    new_acc_locked.save()

                updated.user = request.user
                updated.save()

            return redirect('transaction_list')
    else:
        form = TransactionForm(instance=transaction_obj, user=request.user)

    return render(request, 'myapp/transaction_form.html', {'form': form})


@login_required
def transaction_delete(request, pk):
    transaction_obj = get_object_or_404(Transaction, pk=pk, user=request.user)

    if request.method == 'POST':
        with transaction.atomic():
            account = Account.objects.select_for_update().get(id=transaction_obj.account.id)

            # reverse balance
            account.balance -= transaction_obj.amount
            account.save()

            transaction_obj.delete()

        return redirect('transaction_list')

    return render(request, 'myapp/transaction_confirm_delete.html', {'transaction': transaction_obj})

@login_required
def account_list(request):
    accounts = Account.objects.filter(user=request.user)
    return render(request, 'accounts/account_list.html', {'accounts': accounts})

@login_required
def account_create(request):
    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            account = form.save(commit=False)
            account.user = request.user
            account.save()
            return redirect('account_list')
    else:
        form = AccountForm()
    return render(request, 'accounts/account_form.html', {'form': form})

@login_required
def account_edit(request, pk):
    account = get_object_or_404(Account, pk=pk, user=request.user)
    if request.method == 'POST':
        form = AccountForm(request.POST, instance=account)
        if form.is_valid():
            form.save()
            return redirect('account_list')
    else:
        form = AccountForm(instance=account)
    return render(request, 'accounts/account_form.html', {'form': form})

@login_required
def account_delete(request, pk):
    account = get_object_or_404(Account, pk=pk, user=request.user)
    if request.method == 'POST':
        account.delete()
        return redirect('account_list')
    return render(request, 'accounts/account_confirm_delete.html', {'account': account})

@login_required
def category_list(request):
    categories = Category.objects.filter(user=request.user)
    return render(request, 'categories/category_list.html', {'categories': categories})

@login_required
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            return redirect('category_list')
    else:
        form = CategoryForm()
    return render(request, 'categories/category_form.html', {'form': form})

@login_required
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'categories/category_form.html', {'form': form})

@login_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == 'POST':
        category.delete()
        return redirect('category_list')
    return render(request, 'categories/category_confirm_delete.html', {'category': category})

@login_required
def report_view(request):
    transactions = Transaction.objects.filter(user=request.user)

    # Filters
    start_date = request.GET.get('start_date') or ''
    end_date = request.GET.get('end_date') or ''
    account_id = request.GET.get('account') or ''
    category_id = request.GET.get('category') or ''

    if start_date:
        transactions = transactions.filter(transaction_date__gte=start_date)
    if end_date:
        transactions = transactions.filter(transaction_date__lte=end_date)
    if account_id:
        transactions = transactions.filter(account_id=account_id)
    if category_id:
        transactions = transactions.filter(category_id=category_id)

    # Sorting
    sort = request.GET.get('sort', 'transaction_date')
    dir = request.GET.get('dir', 'asc')
    toggle_dir = 'desc' if dir == 'asc' else 'asc'
    sort_field = f"-{sort}" if dir == 'desc' else sort
    transactions = transactions.order_by(sort_field)

    # Aggregates
    total_amount = transactions.aggregate(Sum('amount'))['amount__sum'] or 0
    avg_amount = transactions.aggregate(Avg('amount'))['amount__avg'] or 0
    num_transactions = transactions.count()

    context = {
        'transactions': transactions,
        'accounts': Account.objects.filter(user=request.user),
        'categories': Category.objects.filter(user=request.user),
        'start_date': start_date,
        'end_date': end_date,
        'account_id': account_id,
        'category_id': category_id,
        'total_amount': total_amount,
        'avg_amount': avg_amount,
        'num_transactions': num_transactions,
        'sort': sort,
        'dir': dir,
        'toggle_dir': toggle_dir,
    }

    return render(request, 'myapp/report.html', context)


