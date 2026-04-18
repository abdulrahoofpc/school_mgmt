from rest_framework import serializers
from .models import Student


class StudentSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    total_fee_paid = serializers.ReadOnlyField()
    total_fee_due = serializers.ReadOnlyField()

    class Meta:
        model = Student
        fields = '__all__'


class StudentListSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = Student
        fields = ['id', 'full_name', 'student_class', 'section',
                  'roll_number', 'parent_name', 'parent_phone', 'admission_date', 'is_active']
