"""
api_views.py

REST API for the Smart Expense Tracker, built with Django REST
Framework. This is an additive layer only — it reuses the exact same
models, category predictor, and utils.py helper functions as the
existing Django template-based web app, so the web app and the
Flutter mobile app always compute identical totals, insights, and
budget status from the same database.

Every endpoint here enforces `user=request.user` (directly or via
get_object_or_404), matching the same data-isolation rule used
throughout views.py.
"""
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Budget, Expense
from .serializers import (
    BudgetSerializer, ExpenseSerializer, LoginSerializer,
    RegisterSerializer, UserSerializer,
)
from .utils import (
    get_budget_status, get_category_breakdown, get_daily_trend,
    get_dashboard_summary, get_month_range, get_spending_insights,
    get_today, get_week_range,
)


# ---------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------

class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(
            request,
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password'],
        )
        if user is None:
            return Response(
                {'detail': 'Invalid username or password.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data,
        })


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Deleting the token immediately invalidates it for all devices
        # using it; the client should also discard it locally.
        Token.objects.filter(user=request.user).delete()
        return Response({'detail': 'Logged out successfully.'})


# ---------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------

class DashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = get_today()
        month_start, month_end = get_month_range(today)

        summary = get_dashboard_summary(user)
        category_breakdown = get_category_breakdown(user, month_start, month_end)
        daily_trend = get_daily_trend(user, month_start, month_end)
        budget_status = get_budget_status(user, today)
        insights = get_spending_insights(user, today)
        recent = Expense.objects.filter(user=user)[:5]

        return Response({
            'summary': {
                'today_total': summary['today_total'],
                'week_total': summary['week_total'],
                'month_total': summary['month_total'],
                'overall_total': summary['overall_total'],
            },
            'category_breakdown': [
                {'category': row['category'], 'total': row['total']}
                for row in category_breakdown
            ],
            'spending_trend': [
                {'date': day['date'], 'total': day['total']}
                for day in daily_trend
            ],
            'budget_status': {
                'has_budget': bool(budget_status['budget']),
                'monthly_budget': budget_status['monthly_budget'],
                'current_spending': budget_status['current_spending'],
                'remaining': budget_status['remaining'],
                'percentage_used': budget_status['percentage_used'],
                'is_warning': budget_status['is_warning'],
                'is_exceeded': budget_status['is_exceeded'],
            },
            'insights': insights,
            'recent_expenses': ExpenseSerializer(recent, many=True).data,
        })


# ---------------------------------------------------------------------
# Expenses (list/create/retrieve/update/delete)
# ---------------------------------------------------------------------

class ExpenseListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        expenses = Expense.objects.filter(user=request.user)

        search = request.query_params.get('search', '').strip()
        if search:
            from django.db.models import Q
            expenses = expenses.filter(
                Q(description__icontains=search)
                | Q(category__icontains=search)
                | Q(notes__icontains=search)
            )

        date_filter = request.query_params.get('filter', 'all')
        today = get_today()
        if date_filter == 'today':
            expenses = expenses.filter(date=today)
        elif date_filter == 'week':
            week_start, week_end = get_week_range(today)
            expenses = expenses.filter(date__gte=week_start, date__lte=week_end)
        elif date_filter == 'month':
            month_start, month_end = get_month_range(today)
            expenses = expenses.filter(date__gte=month_start, date__lte=month_end)

        return Response(ExpenseSerializer(expenses, many=True).data)

    def post(self, request):
        serializer = ExpenseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExpenseDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        return get_object_or_404(Expense, id=pk, user=request.user)

    def get(self, request, pk):
        expense = self.get_object(request, pk)
        return Response(ExpenseSerializer(expense).data)

    def put(self, request, pk):
        expense = self.get_object(request, pk)
        serializer = ExpenseSerializer(expense, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        expense = self.get_object(request, pk)
        expense.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------
# Budget
# ---------------------------------------------------------------------

class BudgetAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = get_today()
        budget = Budget.objects.filter(
            user=request.user, month=today.month, year=today.year
        ).first()
        status_data = get_budget_status(request.user, today)
        return Response({
            'budget': BudgetSerializer(budget).data if budget else None,
            'status': {
                'monthly_budget': status_data['monthly_budget'],
                'current_spending': status_data['current_spending'],
                'remaining': status_data['remaining'],
                'percentage_used': status_data['percentage_used'],
                'is_warning': status_data['is_warning'],
                'is_exceeded': status_data['is_exceeded'],
            },
        })

    def put(self, request):
        today = get_today()
        budget = Budget.objects.filter(
            user=request.user, month=today.month, year=today.year
        ).first()
        serializer = BudgetSerializer(budget, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(user=request.user, month=today.month, year=today.year)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------

class ReportsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        period = request.query_params.get('period', 'month')
        today = get_today()
        expenses = Expense.objects.filter(user=request.user)

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

        from django.db.models import Sum
        category_summary = list(
            expenses.values('category').annotate(total=Sum('amount')).order_by('-total')
        )
        total = sum((e.amount for e in expenses), start=0)

        return Response({
            'period': period,
            'period_label': label,
            'total': total,
            'category_summary': category_summary,
            'expenses': ExpenseSerializer(expenses, many=True).data,
        })


def _get_period_expenses(user, period):
    """Shared period-filtering logic for the file-download API views below."""
    today = get_today()
    expenses = Expense.objects.filter(user=user)
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
    return expenses, label


class ReportCSVAPIView(APIView):
    """Token-authenticated CSV download for the Flutter app.
    Reuses the exact same CSV-building logic as the web app's
    /report/csv/ view (see expenses/views.py:_build_csv_response)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .views import _build_csv_response
        period = request.query_params.get('period', 'month')
        expenses, _ = _get_period_expenses(request.user, period)
        return _build_csv_response(expenses)


class ReportPDFAPIView(APIView):
    """Token-authenticated PDF download for the Flutter app.
    Reuses the exact same PDF-building logic (with the bundled
    Unicode font for ₹) as the web app's /report/pdf/ view."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.db.models import Sum

        from .views import _build_pdf_response
        period = request.query_params.get('period', 'month')
        expenses, label = _get_period_expenses(request.user, period)
        category_summary = list(
            expenses.values('category').annotate(total=Sum('amount')).order_by('-total')
        )
        total = sum((e.amount for e in expenses), start=0)
        return _build_pdf_response(request.user.username, expenses, label, category_summary, total)
