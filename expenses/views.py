"""
Views for the Smart Expense Tracker.

Every view that touches Expense/Budget data is protected with
@login_required and every queryset is scoped with `user=request.user`
so that one user can never see or modify another user's data.
"""
import csv
import json
import os
from datetime import date as date_cls

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from .category_predictor import predict_category
from .forms import BudgetForm, ExpenseForm, LoginForm, SignUpForm
from .models import Budget, Expense
from .utils import (
    get_budget_status, get_category_breakdown, get_daily_trend,
    get_dashboard_summary, get_month_range, get_spending_insights,
    get_today, get_week_range,
)


# ---------------------------------------------------------------------
# PDF font setup
# ---------------------------------------------------------------------
# ReportLab's built-in fonts (Helvetica, Times, etc.) only support the
# WinAnsi/Latin-1 character set and CANNOT render the Indian Rupee sign
# (₹, U+20B9) — it silently prints as a black square instead. We bundle
# DejaVu Sans (which does include the ₹ glyph) with the project and
# register it once at import time so it works identically on any OS,
# regardless of what fonts happen to be installed system-wide.
_FONTS_DIR = os.path.join(os.path.dirname(__file__), 'fonts')
PDF_FONT_REGULAR = 'Helvetica'
PDF_FONT_BOLD = 'Helvetica-Bold'
try:
    pdfmetrics.registerFont(TTFont('DejaVuSans', os.path.join(_FONTS_DIR, 'DejaVuSans.ttf')))
    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', os.path.join(_FONTS_DIR, 'DejaVuSans-Bold.ttf')))
    PDF_FONT_REGULAR = 'DejaVuSans'
    PDF_FONT_BOLD = 'DejaVuSans-Bold'
except Exception:
    # Falls back to Helvetica if the bundled font is ever missing; the
    # PDF will still generate, just with "Rs." rendering issues for ₹.
    pass


# ---------------------------------------------------------------------
# Authentication views
# ---------------------------------------------------------------------

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
            )
            login(request, user)
            messages.success(request, '✓ Account created successfully! Welcome aboard.')
            return redirect('dashboard')
    else:
        form = SignUpForm()

    return render(request, 'expenses/signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
            )
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            messages.error(request, '⚠ Invalid username or password.')
    else:
        form = LoginForm()

    return render(request, 'expenses/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, '✓ You have been logged out successfully.')
    return redirect('login')


# ---------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------

@login_required
def dashboard_view(request):
    summary = get_dashboard_summary(request.user)
    today = get_today()
    month_start, month_end = get_month_range(today)

    category_breakdown = get_category_breakdown(request.user, month_start, month_end)
    daily_trend = get_daily_trend(request.user, month_start, month_end)
    budget_status = get_budget_status(request.user, today)
    insights = get_spending_insights(request.user, today)

    recent_expenses = Expense.objects.filter(user=request.user)[:5]

    context = {
        'summary': summary,
        'category_labels': json.dumps([row['category'] for row in category_breakdown]),
        'category_values': json.dumps([float(row['total']) for row in category_breakdown]),
        'trend_labels': json.dumps([d['date'].strftime('%d %b') for d in daily_trend]),
        'trend_values': json.dumps([float(d['total']) for d in daily_trend]),
        'has_category_data': bool(category_breakdown),
        'has_trend_data': any(day['total'] for day in daily_trend),
        'budget_status': budget_status,
        'insights': insights,
        'recent_expenses': recent_expenses,
        'has_expenses': Expense.objects.filter(user=request.user).exists(),
    }
    return render(request, 'expenses/dashboard.html', context)


# ---------------------------------------------------------------------
# Expense CRUD
# ---------------------------------------------------------------------

@login_required
def add_expense_view(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.category = predict_category(expense.description)
            expense.save()
            messages.success(request, '✓ Expense added successfully!')
            return redirect('expense_list')
    else:
        form = ExpenseForm()

    return render(request, 'expenses/add_expense.html', {'form': form})


@login_required
def predict_category_ajax(request):
    """Lightweight endpoint used by JS to preview the predicted category
    as the user types the description (progressive enhancement)."""
    description = request.GET.get('description', '')
    category = predict_category(description)
    return HttpResponse(category)


@login_required
def expense_list_view(request):
    expenses = Expense.objects.filter(user=request.user)

    search_query = request.GET.get('search', '').strip()
    if search_query:
        from django.db.models import Q
        expenses = expenses.filter(
            Q(description__icontains=search_query)
            | Q(category__icontains=search_query)
            | Q(notes__icontains=search_query)
        )

    date_filter = request.GET.get('filter', 'all')
    today = get_today()
    if date_filter == 'today':
        expenses = expenses.filter(date=today)
    elif date_filter == 'week':
        week_start, week_end = get_week_range(today)
        expenses = expenses.filter(date__gte=week_start, date__lte=week_end)
    elif date_filter == 'month':
        month_start, month_end = get_month_range(today)
        expenses = expenses.filter(date__gte=month_start, date__lte=month_end)
    # 'all' -> no additional filtering

    context = {
        'expenses': expenses,
        'search_query': search_query,
        'date_filter': date_filter,
    }
    return render(request, 'expenses/expense_list.html', context)


@login_required
def edit_expense_view(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id, user=request.user)
    old_description = expense.description

    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            updated_expense = form.save(commit=False)
            if updated_expense.description != old_description:
                updated_expense.category = predict_category(updated_expense.description)
            updated_expense.save()
            messages.success(request, '✓ Expense updated successfully!')
            return redirect('expense_list')
    else:
        form = ExpenseForm(instance=expense)

    return render(request, 'expenses/edit_expense.html', {'form': form, 'expense': expense})


@login_required
def delete_expense_view(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id, user=request.user)

    if request.method == 'POST':
        expense.delete()
        messages.success(request, '✓ Expense deleted successfully!')
        return redirect('expense_list')

    return render(request, 'expenses/delete_expense.html', {'expense': expense})


# ---------------------------------------------------------------------
# Budget management
# ---------------------------------------------------------------------

@login_required
def budget_view(request):
    today = get_today()
    budget = Budget.objects.filter(user=request.user, month=today.month, year=today.year).first()

    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=budget)
        if form.is_valid():
            new_budget = form.save(commit=False)
            new_budget.user = request.user
            new_budget.month = today.month
            new_budget.year = today.year
            new_budget.save()
            messages.success(request, '✓ Budget updated successfully!')
            return redirect('budget')
    else:
        form = BudgetForm(instance=budget)

    budget_status = get_budget_status(request.user, today)

    context = {
        'form': form,
        'budget_status': budget_status,
    }
    return render(request, 'expenses/budget.html', context)


# ---------------------------------------------------------------------
# Reports: HTML preview, CSV download, PDF download
# ---------------------------------------------------------------------

def _get_report_queryset(request):
    """Shared helper: applies an optional period filter (?period=today|week|month|all)."""
    expenses = Expense.objects.filter(user=request.user)
    period = request.GET.get('period', 'month')
    today = get_today()

    if period == 'today':
        expenses = expenses.filter(date=today)
        label = 'Today'
    elif period == 'week':
        week_start, week_end = get_week_range(today)
        expenses = expenses.filter(date__gte=week_start, date__lte=week_end)
        label = f"Week of {week_start.strftime('%d %b %Y')}"
    elif period == 'all':
        label = 'All Time'
    else:
        month_start, month_end = get_month_range(today)
        expenses = expenses.filter(date__gte=month_start, date__lte=month_end)
        label = today.strftime('%B %Y')

    return expenses, label, period


@login_required
def report_view(request):
    expenses, period_label, period = _get_report_queryset(request)
    category_summary = get_category_breakdown(request.user) if period == 'all' else None
    if category_summary is None:
        from django.db.models import Sum
        category_summary = list(
            expenses.values('category').annotate(total=Sum('amount')).order_by('-total')
        )
    total = sum((e.amount for e in expenses), start=0)

    context = {
        'expenses': expenses,
        'period_label': period_label,
        'period': period,
        'category_summary': category_summary,
        'total': total,
    }
    return render(request, 'expenses/report.html', context)


def _build_csv_response(expenses):
    """Shared CSV-building logic used by both the web view and the API."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="expense_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Description', 'Category', 'Amount', 'Notes'])
    for expense in expenses:
        writer.writerow([
            expense.date.strftime('%d-%m-%Y'),
            expense.description,
            expense.category,
            expense.amount,
            expense.notes or '',
        ])

    return response


def _build_pdf_response(username, expenses, period_label, category_summary, total):
    """Shared PDF-building logic used by both the web view and the API."""
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="expense_report.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4)
    base_styles = getSampleStyleSheet()

    # Custom paragraph styles using the Unicode-capable bundled font so
    # the ₹ symbol renders correctly instead of as a missing-glyph box.
    title_style = ParagraphStyle(
        'RupeeTitle', parent=base_styles['Title'], fontName=PDF_FONT_BOLD,
    )
    heading_style = ParagraphStyle(
        'RupeeHeading2', parent=base_styles['Heading2'], fontName=PDF_FONT_BOLD,
    )
    normal_style = ParagraphStyle(
        'RupeeNormal', parent=base_styles['Normal'], fontName=PDF_FONT_REGULAR,
    )

    elements = []

    elements.append(Paragraph('SMART EXPENSE REPORT', title_style))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"User: {username}", normal_style))
    elements.append(Paragraph(f"Report Period: {period_label}", normal_style))
    elements.append(Paragraph(f"Total Expenses: ₹{total:.2f}", normal_style))
    elements.append(Spacer(1, 16))

    elements.append(Paragraph('Category Summary', heading_style))
    cat_data = [['Category', 'Amount (₹)']]
    for row in category_summary:
        cat_data.append([row['category'], f"₹{row['total']:.2f}"])
    if len(cat_data) == 1:
        cat_data.append(['No data', '₹0.00'])
    cat_table = Table(cat_data, hAlign='LEFT', colWidths=[200, 150])
    cat_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#5b21b6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 0), (-1, -1), PDF_FONT_REGULAR),
        ('FONTNAME', (0, 0), (-1, 0), PDF_FONT_BOLD),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f0ff')]),
    ]))
    elements.append(cat_table)
    elements.append(Spacer(1, 16))

    elements.append(Paragraph('Expense Details', heading_style))
    detail_data = [['Date', 'Description', 'Category', 'Amount', 'Notes']]
    for expense in expenses:
        detail_data.append([
            expense.date.strftime('%d-%m-%Y'),
            expense.description,
            expense.category,
            f"₹{expense.amount:.2f}",
            (expense.notes or '')[:40],
        ])
    if len(detail_data) == 1:
        detail_data.append(['-', 'No expenses found', '-', '-', '-'])

    detail_table = Table(detail_data, hAlign='LEFT', colWidths=[65, 140, 80, 60, 120])
    detail_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#5b21b6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), PDF_FONT_REGULAR),
        ('FONTNAME', (0, 0), (-1, 0), PDF_FONT_BOLD),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f0ff')]),
    ]))
    elements.append(detail_table)

    doc.build(elements)
    return response


@login_required
def download_csv_view(request):
    expenses, period_label, _ = _get_report_queryset(request)
    return _build_csv_response(expenses)


@login_required
def download_pdf_view(request):
    expenses, period_label, _ = _get_report_queryset(request)
    from django.db.models import Sum
    category_summary = list(
        expenses.values('category').annotate(total=Sum('amount')).order_by('-total')
    )
    total = sum((e.amount for e in expenses), start=0)
    return _build_pdf_response(request.user.username, expenses, period_label, category_summary, total)


@login_required
def profile_view(request):
    summary = get_dashboard_summary(request.user)
    context = {
        'summary': summary,
        'expense_count': Expense.objects.filter(user=request.user).count(),
        'member_since': request.user.date_joined,
    }
    return render(request, 'expenses/profile.html', context)


def home_redirect_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')
