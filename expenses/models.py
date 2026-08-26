"""
Database models for the Smart Expense Tracker application.

Every Expense and Budget record is tied to a specific user via a
ForeignKey. All queries in views.py MUST filter by `request.user`
to keep each user's financial data completely isolated.
"""
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models


class Expense(models.Model):
    """Represents a single expense entry created by a user."""

    CATEGORY_CHOICES = [
        ('Food', 'Food'),
        ('Travel', 'Travel'),
        ('Shopping', 'Shopping'),
        ('Bills', 'Bills'),
        ('Education', 'Education'),
        ('Entertainment', 'Entertainment'),
        ('Health', 'Health'),
        ('Groceries', 'Groceries'),
        ('Other', 'Other'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='expenses',
    )
    description = models.CharField(max_length=255)
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='Other',
    )
    date = models.DateField()
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.description} - ₹{self.amount} ({self.category})"


class Budget(models.Model):
    """Represents a user's monthly budget for a given month/year."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='budgets',
    )
    monthly_budget = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )
    month = models.IntegerField()  # 1-12
    year = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'month', 'year')
        ordering = ['-year', '-month']

    def __str__(self):
        return f"{self.user.username} - {self.month}/{self.year}: ₹{self.monthly_budget}"
