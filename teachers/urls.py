from django.urls import path
from . import views

app_name = 'teachers'

urlpatterns = [
    path('', views.teacher_list, name='list'),
    path('add/', views.teacher_create, name='create'),
    path('<int:pk>/', views.teacher_detail, name='detail'),
    path('<int:pk>/edit/', views.teacher_edit, name='edit'),
    path('<int:pk>/delete/', views.teacher_delete, name='delete'),
    path('salary/', views.salary_list, name='salary_list'),
    path('salary/add/', views.salary_create, name='salary_create'),
    path('salary/<int:pk>/edit/', views.salary_edit, name='salary_edit'),
    path('salary/<int:pk>/delete/', views.salary_delete, name='salary_delete'),
]
