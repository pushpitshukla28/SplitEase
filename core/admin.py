from django.contrib import admin
from .models import Trip, TripMember, Expense, ExpenseSplit, PersonalExpense


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at')
    search_fields = ('name', 'created_by__username')


@admin.register(TripMember)
class TripMemberAdmin(admin.ModelAdmin):
    list_display = ('trip', 'user', 'joined_at')
    list_filter = ('trip',)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('description', 'amount', 'paid_by', 'trip', 'date')
    list_filter = ('trip', 'date')
    search_fields = ('description', 'paid_by__username')


@admin.register(ExpenseSplit)
class ExpenseSplitAdmin(admin.ModelAdmin):
    list_display = ('expense', 'user', 'amount')
    list_filter = ('expense__trip',)


@admin.register(PersonalExpense)
class PersonalExpenseAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'category', 'date', 'note')
    list_filter = ('category', 'date')
    search_fields = ('user__username', 'note')
