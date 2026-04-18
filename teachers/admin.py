from django.contrib import admin
from .models import Teacher, SalaryRecord

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'employee_id', 'subject', 'phone', 'monthly_salary', 'is_active']
    list_filter = ['subject', 'is_active']
    search_fields = ['first_name', 'last_name', 'employee_id']

@admin.register(SalaryRecord)
class SalaryRecordAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'month', 'year', 'amount', 'status', 'payment_date']
    list_filter = ['status', 'month', 'year']
