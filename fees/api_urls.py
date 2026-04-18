from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FeeStructureViewSet, PaymentViewSet

router = DefaultRouter()
router.register('structures', FeeStructureViewSet, basename='feestructure')
router.register('payments', PaymentViewSet, basename='payment')

urlpatterns = [path('', include(router.urls))]
