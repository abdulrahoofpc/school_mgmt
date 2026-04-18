from django.urls import path
from . import views

app_name = 'fees'

urlpatterns = [
    path('', views.fee_list, name='list'),
    path('add/', views.fee_create, name='create'),
    path('<int:pk>/', views.fee_detail, name='detail'),
    path('<int:pk>/edit/', views.fee_edit, name='edit'),
    path('<int:pk>/delete/', views.fee_delete, name='delete'),
    path('<int:fee_pk>/pay/', views.payment_create, name='payment_create'),
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/<int:pk>/receipt/', views.payment_receipt, name='receipt'),
]
