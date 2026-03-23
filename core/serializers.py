from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Trip, TripMember, Expense, ExpenseSplit, PersonalExpense, FriendRequest, Settlement, CATEGORY_CHOICES


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'full_name', 'email']

    def get_full_name(self, obj):
        return obj.get_full_name()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class ExpenseSplitSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ExpenseSplit
        fields = ['id', 'user', 'amount']


class ExpenseSerializer(serializers.ModelSerializer):
    paid_by = UserSerializer(read_only=True)
    splits = ExpenseSplitSerializer(many=True, read_only=True)

    class Meta:
        model = Expense
        fields = ['id', 'description', 'amount', 'paid_by', 'date', 'created_at', 'splits']


class TripSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    members = serializers.SerializerMethodField()
    total_expenses = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = ['id', 'name', 'description', 'created_by', 'created_at', 'members', 'total_expenses']

    def get_members(self, obj):
        users = obj.get_members()
        return UserSerializer(users, many=True).data

    def get_total_expenses(self, obj):
        return str(obj.total_expenses())


class SettlementSerializer(serializers.ModelSerializer):
    payer = UserSerializer(read_only=True)
    payee = UserSerializer(read_only=True)

    class Meta:
        model = Settlement
        fields = ['id', 'payer', 'payee', 'amount', 'created_at']


class PersonalExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonalExpense
        fields = ['id', 'amount', 'category', 'note', 'date', 'created_at']


class FriendRequestSerializer(serializers.ModelSerializer):
    from_user = UserSerializer(read_only=True)
    to_user = UserSerializer(read_only=True)

    class Meta:
        model = FriendRequest
        fields = ['id', 'from_user', 'to_user', 'created_at', 'accepted']
