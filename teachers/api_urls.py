from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TeacherViewSet, SalaryRecordViewSet

router = DefaultRouter()
router.register('', TeacherViewSet, basename='teacher')
router.register('salary', SalaryRecordViewSet, basename='salary')

urlpatterns = [path('', include(router.urls))]
