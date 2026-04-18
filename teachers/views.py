from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Teacher, SalaryRecord, SUBJECT_CHOICES
from .serializers import TeacherSerializer, TeacherListSerializer, SalaryRecordSerializer
import datetime


class TeacherViewSet(viewsets.ModelViewSet):
    queryset = Teacher.objects.all()
    permission_classes = [IsAuthenticated]
    search_fields = ['first_name', 'last_name', 'employee_id', 'subject']
    filterset_fields = ['subject', 'is_active']

    def get_serializer_class(self):
        if self.action == 'list':
            return TeacherListSerializer
        return TeacherSerializer


class SalaryRecordViewSet(viewsets.ModelViewSet):
    queryset = SalaryRecord.objects.all()
    serializer_class = SalaryRecordSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['teacher', 'month', 'year', 'status']


@login_required
def teacher_list(request):
    queryset = Teacher.objects.all()
    q = request.GET.get('q', '')
    subject_filter = request.GET.get('subject', '')
    if q:
        queryset = queryset.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) |
            Q(employee_id__icontains=q)
        )
    if subject_filter:
        queryset = queryset.filter(subject=subject_filter)
    paginator = Paginator(queryset, 20)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'teachers/teacher_list.html', {
        'page_obj': page,
        'q': q,
        'subject_filter': subject_filter,
        'subject_choices': SUBJECT_CHOICES,
        'total': queryset.count(),
    })


@login_required
def teacher_detail(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    salary_records = teacher.salary_records.all()
    return render(request, 'teachers/teacher_detail.html', {
        'teacher': teacher,
        'salary_records': salary_records,
    })


@login_required
def teacher_create(request):
    if request.method == 'POST':
        try:
            teacher = Teacher(
                first_name=request.POST['first_name'],
                last_name=request.POST['last_name'],
                employee_id=request.POST['employee_id'],
                subject=request.POST['subject'],
                phone=request.POST['phone'],
                email=request.POST.get('email', ''),
                address=request.POST.get('address', ''),
                date_of_joining=request.POST['date_of_joining'],
                monthly_salary=request.POST['monthly_salary'],
            )
            if 'photo' in request.FILES:
                teacher.photo = request.FILES['photo']
            teacher.save()
            messages.success(request, f'Teacher {teacher.full_name} added successfully.')
            return redirect('teachers:detail', pk=teacher.pk)
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return render(request, 'teachers/teacher_form.html', {
        'action': 'Add', 'subject_choices': SUBJECT_CHOICES
    })


@login_required
def teacher_edit(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    if request.method == 'POST':
        try:
            teacher.first_name = request.POST['first_name']
            teacher.last_name = request.POST['last_name']
            teacher.employee_id = request.POST['employee_id']
            teacher.subject = request.POST['subject']
            teacher.phone = request.POST['phone']
            teacher.email = request.POST.get('email', '')
            teacher.address = request.POST.get('address', '')
            teacher.date_of_joining = request.POST['date_of_joining']
            teacher.monthly_salary = request.POST['monthly_salary']
            if 'photo' in request.FILES:
                teacher.photo = request.FILES['photo']
            teacher.save()
            messages.success(request, 'Teacher updated successfully.')
            return redirect('teachers:detail', pk=teacher.pk)
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return render(request, 'teachers/teacher_form.html', {
        'action': 'Edit', 'teacher': teacher, 'subject_choices': SUBJECT_CHOICES
    })


@login_required
def teacher_delete(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    if request.method == 'POST':
        name = teacher.full_name
        teacher.delete()
        messages.success(request, f'Teacher {name} deleted.')
        return redirect('teachers:list')
    return render(request, 'teachers/teacher_confirm_delete.html', {'teacher': teacher})


@login_required
def salary_list(request):
    queryset = SalaryRecord.objects.select_related('teacher').all()
    teacher_id = request.GET.get('teacher', '')
    month = request.GET.get('month', '')
    year = request.GET.get('year', str(datetime.date.today().year))
    status = request.GET.get('status', '')
    if teacher_id:
        queryset = queryset.filter(teacher_id=teacher_id)
    if month:
        queryset = queryset.filter(month=month)
    if year:
        queryset = queryset.filter(year=year)
    if status:
        queryset = queryset.filter(status=status)
    paginator = Paginator(queryset, 20)
    page = paginator.get_page(request.GET.get('page'))
    teachers = Teacher.objects.filter(is_active=True)
    return render(request, 'teachers/salary_list.html', {
        'page_obj': page,
        'teachers': teachers,
        'teacher_id': teacher_id,
        'month': month,
        'year': year,
        'status': status,
        'months': SalaryRecord.MONTH_CHOICES,
        'years': range(2020, datetime.date.today().year + 2),
    })


@login_required
def salary_create(request):
    if request.method == 'POST':
        try:
            teacher = get_object_or_404(Teacher, pk=request.POST['teacher'])
            salary = SalaryRecord(
                teacher=teacher,
                month=request.POST['month'],
                year=request.POST['year'],
                amount=request.POST['amount'],
                status=request.POST.get('status', 'unpaid'),
                payment_date=request.POST.get('payment_date') or None,
                remarks=request.POST.get('remarks', ''),
            )
            salary.save()
            messages.success(request, 'Salary record created.')
            return redirect('teachers:salary_list')
        except Exception as e:
            messages.error(request, f'Error: {e}')
    teachers = Teacher.objects.filter(is_active=True)
    return render(request, 'teachers/salary_form.html', {
        'action': 'Add',
        'teachers': teachers,
        'months': SalaryRecord.MONTH_CHOICES,
        'years': range(2020, datetime.date.today().year + 2),
        'current_year': datetime.date.today().year,
    })


@login_required
def salary_edit(request, pk):
    salary = get_object_or_404(SalaryRecord, pk=pk)
    if request.method == 'POST':
        try:
            salary.month = request.POST['month']
            salary.year = request.POST['year']
            salary.amount = request.POST['amount']
            salary.status = request.POST.get('status', 'unpaid')
            salary.payment_date = request.POST.get('payment_date') or None
            salary.remarks = request.POST.get('remarks', '')
            salary.save()
            messages.success(request, 'Salary record updated.')
            return redirect('teachers:salary_list')
        except Exception as e:
            messages.error(request, f'Error: {e}')
    teachers = Teacher.objects.filter(is_active=True)
    return render(request, 'teachers/salary_form.html', {
        'action': 'Edit', 'salary': salary, 'teachers': teachers,
        'months': SalaryRecord.MONTH_CHOICES,
        'years': range(2020, datetime.date.today().year + 2),
    })


@login_required
def salary_delete(request, pk):
    salary = get_object_or_404(SalaryRecord, pk=pk)
    if request.method == 'POST':
        salary.delete()
        messages.success(request, 'Salary record deleted.')
        return redirect('teachers:salary_list')
    return render(request, 'teachers/salary_confirm_delete.html', {'salary': salary})
