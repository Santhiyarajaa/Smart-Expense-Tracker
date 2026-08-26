"""
Admin panel registration for Expense and Budget models.
"""
from django.contrib import admin

from .models import Budget, Expense


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('user', 'description', 'amount', 'category', 'date', 'created_at')
    list_filter = ('category', 'date', 'user')
    search_fields = ('description', 'notes', 'user__username')
    ordering = ('-date',)


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('user', 'monthly_budget', 'month', 'year', 'created_at')
    list_filter = ('month', 'year', 'user')
    search_fields = ('user__username',)
    ordering = ('-year', '-month')
