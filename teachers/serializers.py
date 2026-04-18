from rest_framework import serializers
from .models import Teacher, SalaryRecord


class SalaryRecordSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.full_name', read_only=True)
    month_display = serializers.CharField(source='get_month_display', read_only=True)

    class Meta:
        model = SalaryRecord
        fields = '__all__'


class TeacherSerializer(serializers.ModelSerializer):
    salary_records = SalaryRecordSerializer(many=True, read_only=True)
    subject_display = serializers.CharField(source='get_subject_display', read_only=True)
    total_salary_paid = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Teacher
        fields = '__all__'


class TeacherListSerializer(serializers.ModelSerializer):
    subject_display = serializers.CharField(source='get_subject_display', read_only=True)

    class Meta:
        model = Teacher
        fields = ['id', 'first_name', 'last_name', 'employee_id', 'subject',
                  'subject_display', 'phone', 'monthly_salary', 'is_active']
