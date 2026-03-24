from decimal import Decimal
from django.contrib.auth.models import User
from django.db import models as db_models
from django.db.models.functions import TruncMonth
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    Trip, TripMember, Expense, ExpenseSplit,
    PersonalExpense, FriendRequest, Settlement,
    CATEGORY_CHOICES, get_friends,
)
from .serializers import (
    UserSerializer, RegisterSerializer, TripSerializer,
    ExpenseSerializer, SettlementSerializer,
    PersonalExpenseSerializer, FriendRequestSerializer,
)
from .views import calculate_balances


# ── Auth ───────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def api_register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    from django.contrib.auth import authenticate
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '')
    user = authenticate(username=username, password=password)
    if user:
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data,
        })
    return Response({'detail': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
def api_me(request):
    return Response(UserSerializer(request.user).data)


# ── Dashboard ─────────────────────────────────────────────────────────────────

@api_view(['GET'])
def api_dashboard(request):
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

    return Response({
        'trips': TripSerializer(user_trips, many=True).data,
        'personal_total': str(personal_total),
        'total_owed': str(total_owed),
        'total_owe': str(total_owe),
    })


# ── Trips ─────────────────────────────────────────────────────────────────────

@api_view(['POST'])
def api_create_trip(request):
    name = request.data.get('name', '').strip()
    description = request.data.get('description', '').strip()
    member_ids = request.data.get('member_ids', [])

    if not name:
        return Response({'detail': 'Name is required.'}, status=status.HTTP_400_BAD_REQUEST)

    trip = Trip.objects.create(name=name, description=description, created_by=request.user)
    TripMember.objects.create(trip=trip, user=request.user)
    for uid in member_ids:
        try:
            user = User.objects.get(pk=uid)
            TripMember.objects.get_or_create(trip=trip, user=user)
        except User.DoesNotExist:
            pass

    return Response(TripSerializer(trip).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def api_trip_detail(request, pk):
    try:
        trip = Trip.objects.get(pk=pk)
    except Trip.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    if not TripMember.objects.filter(trip=trip, user=request.user).exists():
        return Response({'detail': 'Not a member.'}, status=status.HTTP_403_FORBIDDEN)

    expenses = trip.expenses.select_related('paid_by').prefetch_related('splits__user').order_by('-date', '-created_at')
    balances = calculate_balances(trip)
    balance_list = [
        {
            'debtor': UserSerializer(debtor).data,
            'creditor': UserSerializer(creditor).data,
            'amount': str(amount),
        }
        for (debtor, creditor), amount in balances.items()
    ]
    settlements = trip.settlements.select_related('payer', 'payee').order_by('-created_at')

    return Response({
        'trip': TripSerializer(trip).data,
        'expenses': ExpenseSerializer(expenses, many=True).data,
        'balance_list': balance_list,
        'total': str(trip.total_expenses()),
        'settlements': SettlementSerializer(settlements, many=True).data,
    })


@api_view(['DELETE'])
def api_delete_trip(request, pk):
    try:
        trip = Trip.objects.get(pk=pk)
    except Trip.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    if trip.created_by != request.user:
        return Response({'detail': 'Only the creator can delete this trip.'}, status=status.HTTP_403_FORBIDDEN)

    trip.delete()
    return Response({'detail': 'Trip deleted.'})


# ── Expenses ──────────────────────────────────────────────────────────────────

@api_view(['POST'])
def api_add_expense(request, trip_pk):
    try:
        trip = Trip.objects.get(pk=trip_pk)
    except Trip.DoesNotExist:
        return Response({'detail': 'Trip not found.'}, status=status.HTTP_404_NOT_FOUND)

    if not TripMember.objects.filter(trip=trip, user=request.user).exists():
        return Response({'detail': 'Not a member.'}, status=status.HTTP_403_FORBIDDEN)

    description = request.data.get('description', '').strip()
    amount_str = request.data.get('amount', '0')
    date = request.data.get('date')
    paid_by_id = request.data.get('paid_by_id')
    split_type = request.data.get('split_type', 'equal')
    split_member_ids = request.data.get('split_member_ids', [])
    custom_amounts = request.data.get('custom_amounts', {})  # {user_id: amount}

    if not description or not date or not paid_by_id:
        return Response({'detail': 'description, date, paid_by_id are required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        amount = Decimal(str(amount_str))
        paid_by = User.objects.get(pk=paid_by_id)
    except Exception:
        return Response({'detail': 'Invalid amount or paid_by_id.'}, status=status.HTTP_400_BAD_REQUEST)

    expense = Expense.objects.create(trip=trip, description=description, amount=amount, paid_by=paid_by, date=date)

    members = User.objects.filter(pk__in=split_member_ids)
    if split_type == 'custom':
        for member in members:
            amt_str = custom_amounts.get(str(member.pk), '0')
            try:
                custom_amt = Decimal(str(amt_str)).quantize(Decimal('0.01'))
            except Exception:
                custom_amt = Decimal('0')
            if custom_amt > 0:
                ExpenseSplit.objects.create(expense=expense, user=member, amount=custom_amt)
    else:
        count = members.count()
        if count > 0:
            share = (expense.amount / count).quantize(Decimal('0.01'))
            for member in members:
                ExpenseSplit.objects.create(expense=expense, user=member, amount=share)

    return Response(ExpenseSerializer(expense).data, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
def api_delete_expense(request, expense_pk):
    try:
        expense = Expense.objects.get(pk=expense_pk)
    except Expense.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    if not TripMember.objects.filter(trip=expense.trip, user=request.user).exists():
        return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

    expense.delete()
    return Response({'detail': 'Expense deleted.'})


# ── Settle Up ─────────────────────────────────────────────────────────────────

@api_view(['POST'])
def api_settle_up(request, trip_pk):
    try:
        trip = Trip.objects.get(pk=trip_pk)
    except Trip.DoesNotExist:
        return Response({'detail': 'Trip not found.'}, status=status.HTTP_404_NOT_FOUND)

    if not TripMember.objects.filter(trip=trip, user=request.user).exists():
        return Response({'detail': 'Not a member.'}, status=status.HTTP_403_FORBIDDEN)

    payee_id = request.data.get('payee_id')
    amount_str = request.data.get('amount', '0')

    try:
        payee = User.objects.get(pk=payee_id)
        amount = Decimal(str(amount_str))
        if amount <= 0:
            raise ValueError
    except Exception:
        return Response({'detail': 'Invalid payee_id or amount.'}, status=status.HTTP_400_BAD_REQUEST)

    settlement = Settlement.objects.create(trip=trip, payer=request.user, payee=payee, amount=amount)
    return Response(SettlementSerializer(settlement).data, status=status.HTTP_201_CREATED)


# ── Personal Expenses ─────────────────────────────────────────────────────────

@api_view(['GET'])
def api_personal_expenses(request):
    expenses = PersonalExpense.objects.filter(user=request.user)
    total = expenses.aggregate(total=db_models.Sum('amount'))['total'] or Decimal('0')

    cat_totals = {}
    for code, label in CATEGORY_CHOICES:
        amt = expenses.filter(category=code).aggregate(s=db_models.Sum('amount'))['s'] or Decimal('0')
        if amt > 0:
            cat_totals[code] = {'label': label, 'amount': str(amt)}

    monthly = (
        expenses
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total=db_models.Sum('amount'))
        .order_by('-month')[:12]
    )

    return Response({
        'expenses': PersonalExpenseSerializer(expenses, many=True).data,
        'total': str(total),
        'category_totals': cat_totals,
        'monthly_totals': [{'month': str(m['month'])[:7], 'total': str(m['total'])} for m in monthly],
    })


@api_view(['POST'])
def api_add_personal_expense(request):
    amount_str = request.data.get('amount', '0')
    category = request.data.get('category', 'other')
    note = request.data.get('note', '')
    date = request.data.get('date')

    if not date:
        return Response({'detail': 'date is required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        amount = Decimal(str(amount_str))
    except Exception:
        return Response({'detail': 'Invalid amount.'}, status=status.HTTP_400_BAD_REQUEST)

    pe = PersonalExpense.objects.create(user=request.user, amount=amount, category=category, note=note, date=date)
    return Response(PersonalExpenseSerializer(pe).data, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
def api_delete_personal_expense(request, pk):
    try:
        pe = PersonalExpense.objects.get(pk=pk, user=request.user)
    except PersonalExpense.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
    pe.delete()
    return Response({'detail': 'Deleted.'})


# ── Friends ───────────────────────────────────────────────────────────────────

@api_view(['GET'])
def api_friends(request):
    query = request.query_params.get('q', '').strip()
    search_results = []
    if query:
        friend_ids = get_friends(request.user).values_list('pk', flat=True)
        sent_ids = FriendRequest.objects.filter(from_user=request.user).values_list('to_user_id', flat=True)
        received_ids = FriendRequest.objects.filter(to_user=request.user).values_list('from_user_id', flat=True)
        exclude_ids = set(list(friend_ids) + list(sent_ids) + list(received_ids) + [request.user.pk])
        search_results = User.objects.filter(username__icontains=query).exclude(pk__in=exclude_ids)

    friends = get_friends(request.user)
    pending_received = FriendRequest.objects.filter(to_user=request.user, accepted=False).select_related('from_user')
    pending_sent = FriendRequest.objects.filter(from_user=request.user, accepted=False).select_related('to_user')

    return Response({
        'friends': UserSerializer(friends, many=True).data,
        'pending_received': FriendRequestSerializer(pending_received, many=True).data,
        'pending_sent': FriendRequestSerializer(pending_sent, many=True).data,
        'search_results': UserSerializer(search_results, many=True).data,
    })


@api_view(['POST'])
def api_send_friend_request(request, user_id):
    try:
        to_user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

    if to_user == request.user:
        return Response({'detail': 'Cannot send request to yourself.'}, status=status.HTTP_400_BAD_REQUEST)

    _, created = FriendRequest.objects.get_or_create(from_user=request.user, to_user=to_user)
    return Response({'created': created}, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@api_view(['POST'])
def api_accept_friend_request(request, request_id):
    try:
        freq = FriendRequest.objects.get(pk=request_id, to_user=request.user)
    except FriendRequest.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
    freq.accepted = True
    freq.save()
    return Response({'detail': 'Friend request accepted.'})


@api_view(['DELETE'])
def api_decline_friend_request(request, request_id):
    try:
        freq = FriendRequest.objects.get(pk=request_id, to_user=request.user)
    except FriendRequest.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
    freq.delete()
    return Response({'detail': 'Declined.'})


@api_view(['DELETE'])
def api_remove_friend(request, user_id):
    try:
        other = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
    FriendRequest.objects.filter(from_user=request.user, to_user=other, accepted=True).delete()
    FriendRequest.objects.filter(from_user=other, to_user=request.user, accepted=True).delete()
    return Response({'detail': 'Removed.'})


# ── Account ────────────────────────────────────────────────────────────────────

@api_view(['POST'])
def api_delete_account(request):
    confirm = request.data.get('confirm_username', '').strip()
    if confirm != request.user.username:
        return Response({'detail': 'Username did not match.'}, status=status.HTTP_400_BAD_REQUEST)
    request.user.delete()
    return Response({'detail': 'Account deleted.'})
