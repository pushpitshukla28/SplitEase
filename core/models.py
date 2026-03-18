from django.db import models
from django.contrib.auth.models import User


class Trip(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_trips')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_members(self):
        return User.objects.filter(trip_memberships__trip=self)

    def total_expenses(self):
        return self.expenses.aggregate(total=models.Sum('amount'))['total'] or 0


class TripMember(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trip_memberships')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('trip', 'user')

    def __str__(self):
        return f"{self.user.username} in {self.trip.name}"


class Expense(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='expenses')
    description = models.CharField(max_length=300)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='paid_expenses')
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.description} - {self.amount}"


class ExpenseSplit(models.Model):
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='splits')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expense_splits')
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('expense', 'user')

    def __str__(self):
        return f"{self.user.username} owes {self.amount} for {self.expense.description}"


CATEGORY_CHOICES = [
    ('food', 'Food & Dining'),
    ('transport', 'Transport'),
    ('shopping', 'Shopping'),
    ('entertainment', 'Entertainment'),
    ('health', 'Health'),
    ('utilities', 'Utilities'),
    ('rent', 'Rent'),
    ('travel', 'Travel'),
    ('other', 'Other'),
]


class PersonalExpense(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='personal_expenses')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    note = models.CharField(max_length=300, blank=True)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.category} - {self.amount}"
