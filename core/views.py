from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db import models as db_models
from decimal import Decimal
from collections import defaultdict

from .models import Trip, TripMember, Expense, ExpenseSplit, PersonalExpense
from .forms import RegisterForm, TripForm, ExpenseForm, PersonalExpenseForm


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to SplitEase, {user.username}!')
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    user_trips = Trip.objects.filter(members__user=request.user).order_by('-created_at')
    personal_total = PersonalExpense.objects.filter(user=request.user).aggregate(
        total=db_models.Sum('amount')
    )['total'] or Decimal('0')

    total_owed = Decimal('0')
    total_owe = Decimal('0')
    for trip in user_trips:
        balances = calculate_balances(trip)
        for (debtor, creditor), amount in balances.items():
            if creditor == request.user:
                total_owed += amount
            if debtor == request.user:
                total_owe += amount

    context = {
        'trips': user_trips,
        'personal_total': personal_total,
        'total_owed': total_owed,
        'total_owe': total_owe,
    }
    return render(request, 'dashboard.html', context)


@login_required
def create_trip(request):
    if request.method == 'POST':
        form = TripForm(request.POST, current_user=request.user)
        if form.is_valid():
            trip = form.save(commit=False)
            trip.created_by = request.user
            trip.save()
            TripMember.objects.create(trip=trip, user=request.user)
            for member in form.cleaned_data.get('members', []):
                TripMember.objects.get_or_create(trip=trip, user=member)
            messages.success(request, f'Trip "{trip.name}" created successfully!')
            return redirect('trip_detail', pk=trip.pk)
    else:
        form = TripForm(current_user=request.user)
    return render(request, 'create_trip.html', {'form': form})


def calculate_balances(trip):
    net = defaultdict(Decimal)
    for expense in trip.expenses.all():
        net[expense.paid_by] += expense.amount
        for split in expense.splits.all():
            net[split.user] -= split.amount

    debtors = sorted([(u, -amt) for u, amt in net.items() if amt < 0], key=lambda x: x[1], reverse=True)
    creditors = sorted([(u, amt) for u, amt in net.items() if amt > 0], key=lambda x: x[1], reverse=True)

    settlements = {}
    i, j = 0, 0
    while i < len(debtors) and j < len(creditors):
        debtor, debt = debtors[i]
        creditor, credit = creditors[j]
        amount = min(debt, credit)
        if amount > Decimal('0.01'):
            settlements[(debtor, creditor)] = amount
        debt -= amount
        credit -= amount
        debtors[i] = (debtor, debt)
        creditors[j] = (creditor, credit)
        if debt < Decimal('0.01'):
            i += 1
        if credit < Decimal('0.01'):
            j += 1

    return settlements


@login_required
def trip_detail(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    if not TripMember.objects.filter(trip=trip, user=request.user).exists():
        messages.error(request, 'You are not a member of this trip.')
        return redirect('dashboard')

    expenses = trip.expenses.select_related('paid_by').prefetch_related('splits__user').order_by('-date', '-created_at')
    members = trip.get_members()
    balances = calculate_balances(trip)

    balance_list = [
        {'debtor': debtor, 'creditor': creditor, 'amount': amount}
        for (debtor, creditor), amount in balances.items()
    ]

    context = {
        'trip': trip,
        'expenses': expenses,
        'members': members,
        'balance_list': balance_list,
        'total': trip.total_expenses(),
    }
    return render(request, 'trip_detail.html', context)


@login_required
def add_expense(request, trip_pk):
    trip = get_object_or_404(Trip, pk=trip_pk)
    if not TripMember.objects.filter(trip=trip, user=request.user).exists():
        messages.error(request, 'You are not a member of this trip.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = ExpenseForm(request.POST, trip=trip)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.trip = trip
            expense.save()
            split_members = form.cleaned_data['split_members']
            count = split_members.count()
            if count > 0:
                share = (expense.amount / count).quantize(Decimal('0.01'))
                for member in split_members:
                    ExpenseSplit.objects.create(expense=expense, user=member, amount=share)
            messages.success(request, f'Expense "{expense.description}" added!')
            return redirect('trip_detail', pk=trip.pk)
    else:
        from django.utils import timezone
        form = ExpenseForm(trip=trip, initial={'date': timezone.now().date(), 'paid_by': request.user})

    return render(request, 'add_expense.html', {'form': form, 'trip': trip})


@login_required
def delete_expense(request, expense_pk):
    expense = get_object_or_404(Expense, pk=expense_pk)
    trip = expense.trip
    if not TripMember.objects.filter(trip=trip, user=request.user).exists():
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')
    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Expense deleted.')
    return redirect('trip_detail', pk=trip.pk)


@login_required
def personal_expenses(request):
    if request.method == 'POST':
        form = PersonalExpenseForm(request.POST)
        if form.is_valid():
            pe = form.save(commit=False)
            pe.user = request.user
            pe.save()
            messages.success(request, 'Personal expense added.')
            return redirect('personal_expenses')
    else:
        from django.utils import timezone
        form = PersonalExpenseForm(initial={'date': timezone.now().date()})

    expenses = PersonalExpense.objects.filter(user=request.user)
    total = expenses.aggregate(total=db_models.Sum('amount'))['total'] or Decimal('0')

    from .models import CATEGORY_CHOICES
    cat_totals = {}
    for code, label in CATEGORY_CHOICES:
        amt = expenses.filter(category=code).aggregate(s=db_models.Sum('amount'))['s'] or Decimal('0')
        if amt > 0:
            cat_totals[label] = amt

    context = {
        'form': form,
        'expenses': expenses,
        'total': total,
        'cat_totals': cat_totals,
    }
    return render(request, 'personal_expenses.html', context)


@login_required
def delete_personal_expense(request, pk):
    pe = get_object_or_404(PersonalExpense, pk=pk, user=request.user)
    if request.method == 'POST':
        pe.delete()
        messages.success(request, 'Expense deleted.')
    return redirect('personal_expenses')
