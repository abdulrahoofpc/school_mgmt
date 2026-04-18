from django.contrib import admin
from .models import FeeStructure, Payment

@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ['student', 'academic_year', 'total_fee', 'total_paid', 'balance', 'payment_status']
    list_filter = ['academic_year']
    search_fields = ['student__first_name', 'student__last_name']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['receipt_number', 'student', 'amount_paid', 'payment_date', 'payment_mode', 'status']
    list_filter = ['status', 'payment_mode']
    search_fields = ['receipt_number', 'student__first_name']
