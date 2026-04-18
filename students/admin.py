from django.contrib import admin
from .models import Student

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'roll_number', 'student_class', 'section', 'parent_name', 'parent_phone', 'admission_date', 'is_active']
    list_filter = ['student_class', 'section', 'is_active', 'gender']
    search_fields = ['first_name', 'last_name', 'roll_number', 'parent_name']
    list_per_page = 30
