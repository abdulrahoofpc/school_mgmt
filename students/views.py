from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Case, When, IntegerField
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Student, CLASS_CHOICES, SECTION_CHOICES
from .serializers import StudentSerializer, StudentListSerializer
import django_filters


class StudentFilter(django_filters.FilterSet):
    class Meta:
        model = Student
        fields = {'student_class': ['exact'], 'section': ['exact'], 'is_active': ['exact']}


class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    permission_classes = [IsAuthenticated]
    filterset_class = StudentFilter
    search_fields = ['first_name', 'last_name', 'roll_number', 'parent_name']
    ordering_fields = ['first_name', 'student_class', 'admission_date']

    def get_serializer_class(self):
        if self.action == 'list':
            return StudentListSerializer
        return StudentSerializer


# Build a preserved ordering from CLASS_CHOICES so the list always goes
# IPS1 → IPS2 → Class 1 → Class 2 → … → Class 12
CLASS_ORDER = Case(
    *[When(student_class=val, then=pos) for pos, (val, _) in enumerate(CLASS_CHOICES)],
    output_field=IntegerField(),
)


# ─── Template Views ───────────────────────────────────────────────────────────

@login_required
def student_list(request):
    queryset = Student.objects.annotate(class_order=CLASS_ORDER).order_by(
        'class_order', 'section', 'first_name'
    )

    q              = request.GET.get('q', '')
    class_filter   = request.GET.get('class', '')
    section_filter = request.GET.get('section', '')

    if q:
        queryset = queryset.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) |
            Q(roll_number__icontains=q) | Q(parent_name__icontains=q)
        )
    if class_filter:
        queryset = queryset.filter(student_class=class_filter)
    if section_filter:
        queryset = queryset.filter(section=section_filter)

    paginator = Paginator(queryset, 200)   # large page so regroup sees all records
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'students/student_list.html', {
        'page_obj':        page,
        'q':               q,
        'class_filter':    class_filter,
        'section_filter':  section_filter,
        'class_choices':   CLASS_CHOICES,
        'section_choices': SECTION_CHOICES,
        'total':           queryset.count(),
    })


@login_required
def student_detail(request, pk):
    student        = get_object_or_404(Student, pk=pk)
    payments       = student.payments.all().order_by('-payment_date')
    fee_structures = student.fee_structures.all()
    return render(request, 'students/student_detail.html', {
        'student':        student,
        'payments':       payments,
        'fee_structures': fee_structures,
    })


@login_required
def student_create(request):
    form_data = {}

    if request.method == 'POST':
        form_data = request.POST.dict()
        try:
            student = Student(
                first_name     = request.POST['first_name'].strip(),
                last_name      = request.POST['last_name'].strip(),
                student_class  = request.POST['student_class'],
                section        = request.POST['section'],
                roll_number    = request.POST['roll_number'].strip(),
                gender         = request.POST['gender'],
                parent_name    = request.POST['parent_name'].strip(),
                parent_phone   = request.POST['parent_phone'].strip(),
                parent_email   = request.POST.get('parent_email', '').strip(),
                address        = request.POST.get('address', '').strip(),
                admission_date = request.POST['admission_date'],
                date_of_birth  = request.POST.get('date_of_birth') or None,
                is_active      = request.POST.get('is_active') == 'on',
            )
            if 'photo' in request.FILES:
                student.photo = request.FILES['photo']
            student.save()
            messages.success(request, f'Student {student.full_name} added successfully.')
            return redirect('students:detail', pk=student.pk)
        except Exception as e:
            messages.error(request, f'Error saving student: {e}')

    return render(request, 'students/student_form.html', {
        'action':          'Add',
        'student':         form_data,
        'class_choices':   CLASS_CHOICES,
        'section_choices': SECTION_CHOICES,
    })


@login_required
def student_edit(request, pk):
    student = get_object_or_404(Student, pk=pk)

    if request.method == 'POST':
        try:
            student.first_name     = request.POST['first_name'].strip()
            student.last_name      = request.POST['last_name'].strip()
            student.student_class  = request.POST['student_class']
            student.section        = request.POST['section']
            student.roll_number    = request.POST['roll_number'].strip()
            student.gender         = request.POST['gender']
            student.parent_name    = request.POST['parent_name'].strip()
            student.parent_phone   = request.POST['parent_phone'].strip()
            student.parent_email   = request.POST.get('parent_email', '').strip()
            student.address        = request.POST.get('address', '').strip()
            student.admission_date = request.POST['admission_date']
            student.date_of_birth  = request.POST.get('date_of_birth') or None
            student.is_active      = request.POST.get('is_active') == 'on'
            if 'photo' in request.FILES:
                student.photo = request.FILES['photo']
            student.save()
            messages.success(request, f'Student {student.full_name} updated successfully.')
            return redirect('students:detail', pk=student.pk)
        except Exception as e:
            messages.error(request, f'Error updating student: {e}')

    return render(request, 'students/student_form.html', {
        'action':          'Edit',
        'student':         student,
        'class_choices':   CLASS_CHOICES,
        'section_choices': SECTION_CHOICES,
    })


@login_required
def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        name = student.full_name
        student.delete()
        messages.success(request, f'Student {name} deleted.')
        return redirect('students:list')
    return render(request, 'students/student_confirm_delete.html', {'student': student})