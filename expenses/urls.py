"""
URL patterns for the expenses app.
"""
from django.urls import path

from . import views

urlpatterns = [
    path('', views.home_redirect_view, name='home'),

    # Authentication
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Expense CRUD
    path('expenses/', views.expense_list_view, name='expense_list'),
    path('add-expense/', views.add_expense_view, name='add_expense'),
    path('edit-expense/<int:expense_id>/', views.edit_expense_view, name='edit_expense'),
    path('delete-expense/<int:expense_id>/', views.delete_expense_view, name='delete_expense'),
    path('predict-category/', views.predict_category_ajax, name='predict_category_ajax'),

    # Budget
    path('budget/', views.budget_view, name='budget'),

    # Profile
    path('profile/', views.profile_view, name='profile'),

    # Reports
    path('report/', views.report_view, name='report'),
    path('report/csv/', views.download_csv_view, name='report_csv'),
    path('report/pdf/', views.download_pdf_view, name='report_pdf'),
]
