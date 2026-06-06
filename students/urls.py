from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('',                          views.student_list,       name='list'),
    path('add/',                      views.student_create,     name='create'),
    path('promote/class/',            views.promote_class,      name='promote_class'),
    path('promotions/',               views.promotion_history,  name='promotion_history'),
    path('<int:pk>/',                 views.student_detail,     name='detail'),
    path('<int:pk>/edit/',            views.student_edit,       name='edit'),
    path('<int:pk>/delete/',          views.student_delete,     name='delete'),
    path('<int:pk>/promote/',         views.promote_student,    name='promote'),
]
