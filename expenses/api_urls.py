"""
URL routes for the REST API (mounted at /api/ from the project's
root urls.py). Kept separate from expenses/urls.py so the existing
template-based web routes are completely untouched.
"""
from django.urls import path

from . import api_views

urlpatterns = [
    path('register/', api_views.RegisterAPIView.as_view(), name='api_register'),
    path('login/', api_views.LoginAPIView.as_view(), name='api_login'),
    path('logout/', api_views.LogoutAPIView.as_view(), name='api_logout'),

    path('dashboard/', api_views.DashboardAPIView.as_view(), name='api_dashboard'),

    path('expenses/', api_views.ExpenseListCreateAPIView.as_view(), name='api_expense_list'),
    path('expenses/<int:pk>/', api_views.ExpenseDetailAPIView.as_view(), name='api_expense_detail'),

    path('budget/', api_views.BudgetAPIView.as_view(), name='api_budget'),

    path('reports/', api_views.ReportsAPIView.as_view(), name='api_reports'),
    path('report-file/csv/', api_views.ReportCSVAPIView.as_view(), name='api_report_csv'),
    path('report-file/pdf/', api_views.ReportPDFAPIView.as_view(), name='api_report_pdf'),
]
