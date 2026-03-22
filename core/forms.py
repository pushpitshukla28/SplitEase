from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Trip, Expense, PersonalExpense, CATEGORY_CHOICES, get_friends


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=50, required=False)
    last_name = forms.CharField(max_length=50, required=False)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user


class TripForm(forms.ModelForm):
    members = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Invite Friends',
        help_text='Only your friends appear here. Add friends from the Friends page first.'
    )

    class Meta:
        model = Trip
        fields = ('name', 'description')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        if current_user:
            self.fields['members'].queryset = get_friends(current_user)


class ExpenseForm(forms.ModelForm):
    split_members = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        label='Split Between'
    )

    class Meta:
        model = Expense
        fields = ('description', 'amount', 'paid_by', 'date', 'split_members')
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        trip = kwargs.pop('trip', None)
        super().__init__(*args, **kwargs)
        if trip:
            members_qs = trip.get_members()
            self.fields['paid_by'].queryset = members_qs
            self.fields['split_members'].queryset = members_qs


class PersonalExpenseForm(forms.ModelForm):
    class Meta:
        model = PersonalExpense
        fields = ('amount', 'category', 'note', 'date')
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'note': forms.TextInput(attrs={'placeholder': 'Optional note...'}),
        }
