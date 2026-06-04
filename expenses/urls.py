from django.urls import path
from . import views

app_name = 'expenses'

urlpatterns = [
    path('', views.expense_list, name='list'),
    path('add/', views.expense_create, name='create'),
    path('monthly-print/', views.expense_monthly_print, name='monthly_print'),
    path('<int:pk>/edit/', views.expense_edit, name='edit'),
    path('<int:pk>/delete/', views.expense_delete, name='delete'),
    path('<int:pk>/receipt/', views.expense_receipt, name='receipt'),
]
