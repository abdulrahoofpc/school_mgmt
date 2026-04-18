from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('fee/', views.student_fee_report, name='fee'),
    path('salary/', views.salary_report, name='salary'),
    path('expense/', views.expense_report, name='expense'),
    path('financial/', views.financial_summary, name='financial'),
]
