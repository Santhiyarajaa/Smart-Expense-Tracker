"""
Django forms for authentication, expenses, and budgets.
"""
from django import forms
from django.contrib.auth.models import User

from .models import Budget, Expense


class SignUpForm(forms.Form):
    """Custom signup form with username, email, password & confirmation."""

    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Choose a username',
        }),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'you@example.com',
        }),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
        }),
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password',
        }),
    )

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if len(password) < 6:
            raise forms.ValidationError('Password must be at least 6 characters long.')
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError('Passwords do not match.')
        return cleaned_data


class LoginForm(forms.Form):
    """Simple username/password login form."""

    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username',
            'autofocus': True,
        }),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
        }),
    )


class ExpenseForm(forms.ModelForm):
    """Form used for both adding and editing an expense.

    Category is intentionally excluded from the form fields shown to
    the user - it is predicted automatically from the description in
    the view and saved behind the scenes.
    """

    class Meta:
        model = Expense
        fields = ['description', 'amount', 'date', 'notes']
        widgets = {
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Uber ride to college',
                'id': 'id_description',
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0.01',
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Optional notes',
                'rows': 3,
            }),
        }

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount is None or amount <= 0:
            raise forms.ValidationError('Amount must be greater than 0.')
        return amount

    def clean_description(self):
        description = self.cleaned_data['description'].strip()
        if not description:
            raise forms.ValidationError('Description is required.')
        return description


class BudgetForm(forms.ModelForm):
    """Form for setting/updating a monthly budget."""

    class Meta:
        model = Budget
        fields = ['monthly_budget']
        widgets = {
            'monthly_budget': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 10000',
                'step': '0.01',
                'min': '0.01',
            }),
        }

    def clean_monthly_budget(self):
        amount = self.cleaned_data['monthly_budget']
        if amount is None or amount <= 0:
            raise forms.ValidationError('Monthly budget must be greater than 0.')
        return amount
