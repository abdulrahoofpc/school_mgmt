import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Q, Case, When, IntegerField
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Student, AcademicRecord, CLASS_CHOICES, SECTION_CHOICES, CLASS_PROGRESSION
from .serializers import StudentSerializer, StudentListSerializer
import django_filters


# ─── DRF ─────────────────────────────────────────────────────────────────────

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


# ─── Helpers ─────────────────────────────────────────────────────────────────

CLASS_ORDER = Case(
    *[When(student_class=val, then=pos) for pos, (val, _) in enumerate(CLASS_CHOICES)],
    output_field=IntegerField(),
)


def _current_academic_year():
    today = datetime.date.today()
    return f"{today.year}-{str(today.year + 1)[2:]}"


def _next_academic_year(year_str):
    """'2025-26' → '2026-27'"""
    try:
        start = int(year_str.split('-')[0])
        return f"{start + 1}-{str(start + 2)[2:]}"
    except (ValueError, IndexError):
        return _current_academic_year()


def _validate_roll_number(roll, student_class, section, exclude_pk=None):
    """
    Returns an error string if `roll` is already taken in class+section,
    or None if it is free.
    """
    qs = Student.objects.filter(
        student_class=student_class, section=section, roll_number=roll
    )
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    if qs.exists():
        clash = qs.first()
        class_label = dict(CLASS_CHOICES).get(student_class, student_class)
        return (
            f"Roll number '{roll}' is already taken in {class_label}-{section} "
            f"by {clash.full_name}. Choose a different roll number."
        )
    return None


# ─── Student CRUD ─────────────────────────────────────────────────────────────

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

    paginator = Paginator(queryset, 200)
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
    records        = student.academic_records.all()
    return render(request, 'students/student_detail.html', {
        'student':        student,
        'payments':       payments,
        'fee_structures': fee_structures,
        'academic_records': records,
    })


@login_required
def student_create(request):
    form_data = {}
    if request.method == 'POST':
        form_data = request.POST.dict()
        roll  = request.POST.get('roll_number', '').strip()
        cls   = request.POST.get('student_class', '')
        sec   = request.POST.get('section', '')
        # Friendly roll-number duplicate check (unique within class+section).
        roll_error = _validate_roll_number(roll, cls, sec)
        if roll_error:
            messages.error(request, roll_error)
        else:
            try:
                student = Student(
                    first_name     = request.POST['first_name'].strip(),
                    last_name      = request.POST['last_name'].strip(),
                    student_class  = cls,
                    section        = sec,
                    roll_number    = roll,
                    academic_year  = request.POST.get('academic_year', '').strip(),
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
            except IntegrityError:
                messages.error(
                    request,
                    f"Roll number '{roll}' already exists in "
                    f"{dict(CLASS_CHOICES).get(cls, cls)}-{sec}. "
                    "Please choose a different roll number."
                )
            except Exception as e:
                messages.error(request, f'Error saving student: {e}')

    return render(request, 'students/student_form.html', {
        'action':          'Add',
        'student':         form_data,
        'class_choices':   CLASS_CHOICES,
        'section_choices': SECTION_CHOICES,
        'current_year':    _current_academic_year(),
    })


@login_required
def student_edit(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        roll = request.POST.get('roll_number', '').strip()
        cls  = request.POST.get('student_class', '')
        sec  = request.POST.get('section', '')
        # Friendly roll-number duplicate check (exclude this student).
        roll_error = _validate_roll_number(roll, cls, sec, exclude_pk=student.pk)
        if roll_error:
            messages.error(request, roll_error)
        else:
            try:
                student.first_name     = request.POST['first_name'].strip()
                student.last_name      = request.POST['last_name'].strip()
                student.student_class  = cls
                student.section        = sec
                student.roll_number    = roll
                student.academic_year  = request.POST.get('academic_year', '').strip()
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
            except IntegrityError:
                messages.error(
                    request,
                    f"Roll number '{roll}' already exists in "
                    f"{dict(CLASS_CHOICES).get(cls, cls)}-{sec}."
                )
            except Exception as e:
                messages.error(request, f'Error updating student: {e}')

    return render(request, 'students/student_form.html', {
        'action':          'Edit',
        'student':         student,
        'class_choices':   CLASS_CHOICES,
        'section_choices': SECTION_CHOICES,
        'current_year':    _current_academic_year(),
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


# ─── Promotion: Single Student ────────────────────────────────────────────────

@login_required
def promote_student(request, pk):
    """Promote (or mark failed/transferred/graduated) a single student."""
    student = get_object_or_404(Student, pk=pk)
    next_cls = student.next_class
    current_year = student.academic_year or _current_academic_year()
    next_year = _next_academic_year(current_year)

    if request.method == 'POST':
        status       = request.POST.get('status', '')
        to_class     = request.POST.get('to_class', '').strip()
        to_section   = request.POST.get('to_section', student.section)
        to_roll      = request.POST.get('to_roll_number', student.roll_number).strip()
        from_year    = request.POST.get('from_academic_year', current_year).strip()
        to_year      = request.POST.get('to_academic_year', next_year).strip()
        remarks      = request.POST.get('remarks', '').strip()

        # Check if a record already exists for this student+year.
        if AcademicRecord.objects.filter(student=student, academic_year=from_year).exists():
            messages.error(
                request,
                f"An academic record for {student.full_name} in {from_year} already exists. "
                "Delete it first to re-process."
            )
            return redirect('students:detail', pk=student.pk)

        # Validate the target roll number (if student stays in system).
        if status in ('promoted', 'failed') and to_class and to_section and to_roll:
            roll_error = _validate_roll_number(to_roll, to_class, to_section, exclude_pk=student.pk)
            if roll_error:
                messages.error(request, roll_error)
                return render(request, 'students/promote_student.html', {
                    'student': student, 'class_choices': CLASS_CHOICES,
                    'section_choices': SECTION_CHOICES,
                    'current_year': current_year, 'next_year': next_year,
                    'next_class': next_cls, 'status_choices': AcademicRecord.STATUS_CHOICES,
                })

        try:
            # 1. Save the academic record (history snapshot).
            AcademicRecord.objects.create(
                student          = student,
                academic_year    = from_year,
                from_class       = student.student_class,
                from_section     = student.section,
                from_roll_number = student.roll_number,
                to_class         = to_class if status in ('promoted', 'failed') else '',
                to_section       = to_section if status in ('promoted', 'failed') else '',
                to_roll_number   = to_roll if status in ('promoted', 'failed') else '',
                status           = status,
                remarks          = remarks,
                promoted_by      = request.user,
            )

            # 2. Update the student record based on status.
            if status == 'promoted' and to_class:
                student.student_class = to_class
                student.section       = to_section
                student.roll_number   = to_roll
                student.academic_year = to_year
                student.is_active     = True
                student.save()
                messages.success(
                    request,
                    f"{student.full_name} promoted to "
                    f"{dict(CLASS_CHOICES).get(to_class, to_class)}-{to_section} "
                    f"for {to_year}."
                )
            elif status == 'failed':
                # Stay in same class; update academic year only.
                student.academic_year = to_year
                student.save()
                messages.warning(
                    request,
                    f"{student.full_name} retained in "
                    f"{student.get_student_class_display()}-{student.section} "
                    f"for {to_year}."
                )
            elif status == 'graduated':
                student.is_active = False
                student.academic_year = from_year
                student.save()
                messages.success(request, f"{student.full_name} marked as graduated.")
            elif status in ('transferred', 'withdrawn'):
                student.is_active = False
                student.save()
                messages.info(request, f"{student.full_name} marked as {status}.")

        except Exception as e:
            messages.error(request, f'Error processing promotion: {e}')
            return redirect('students:detail', pk=student.pk)

        return redirect('students:detail', pk=student.pk)

    return render(request, 'students/promote_student.html', {
        'student':         student,
        'class_choices':   CLASS_CHOICES,
        'section_choices': SECTION_CHOICES,
        'current_year':    current_year,
        'next_year':       next_year,
        'next_class':      next_cls,
        'status_choices':  AcademicRecord.STATUS_CHOICES,
    })


# ─── Promotion: Bulk Class ────────────────────────────────────────────────────

@login_required
def promote_class(request):
    """
    Two-phase bulk promotion:
      GET  (no params)        → show class/section/year selector
      GET  (?from_class=…)    → show student list with per-row status dropdowns
      POST                    → process all rows
    """
    class_choices   = CLASS_CHOICES
    section_choices = SECTION_CHOICES
    current_year    = _current_academic_year()

    # ── Phase 1: selection form ──
    from_class   = request.GET.get('from_class', '') or request.POST.get('from_class', '')
    from_section = request.GET.get('from_section', '') or request.POST.get('from_section', '')
    from_year    = request.GET.get('academic_year', '') or request.POST.get('academic_year', current_year)
    to_year      = _next_academic_year(from_year)
    next_cls     = CLASS_PROGRESSION.get(from_class, '')

    students = []
    if from_class and from_section:
        students = list(
            Student.objects.filter(
                student_class=from_class, section=from_section, is_active=True
            ).order_by('roll_number', 'first_name')
        )

    # ── Phase 2: POST → process ──
    if request.method == 'POST' and students:
        errors   = []
        success  = 0

        for s in students:
            key     = f"student_{s.pk}"
            status  = request.POST.get(f"{key}_status", "")
            to_cls  = request.POST.get(f"{key}_to_class", next_cls or '')
            to_sec  = request.POST.get(f"{key}_to_section", s.section)
            to_roll = request.POST.get(f"{key}_to_roll", s.roll_number).strip()
            remarks = request.POST.get(f"{key}_remarks", '').strip()

            if not status:
                continue   # row not submitted / skipped

            # Skip if already recorded for this year.
            if AcademicRecord.objects.filter(student=s, academic_year=from_year).exists():
                errors.append(f"{s.full_name}: record for {from_year} already exists.")
                continue

            # Validate target roll number for promoted/failed students.
            if status in ('promoted', 'failed') and to_cls:
                roll_error = _validate_roll_number(to_roll, to_cls, to_sec, exclude_pk=s.pk)
                if roll_error:
                    errors.append(f"{s.full_name}: {roll_error}")
                    continue

            try:
                AcademicRecord.objects.create(
                    student          = s,
                    academic_year    = from_year,
                    from_class       = s.student_class,
                    from_section     = s.section,
                    from_roll_number = s.roll_number,
                    to_class         = to_cls if status in ('promoted', 'failed') else '',
                    to_section       = to_sec if status in ('promoted', 'failed') else '',
                    to_roll_number   = to_roll if status in ('promoted', 'failed') else '',
                    status           = status,
                    remarks          = remarks,
                    promoted_by      = request.user,
                )
                if status == 'promoted' and to_cls:
                    s.student_class = to_cls
                    s.section       = to_sec
                    s.roll_number   = to_roll
                    s.academic_year = to_year
                    s.is_active     = True
                    s.save()
                elif status == 'failed':
                    s.academic_year = to_year
                    s.save()
                elif status in ('graduated', 'transferred', 'withdrawn'):
                    s.is_active = False
                    s.save()
                success += 1
            except Exception as e:
                errors.append(f"{s.full_name}: {e}")

        if success:
            messages.success(request, f'{success} student(s) processed successfully.')
        for err in errors:
            messages.error(request, err)
        return redirect('students:promotion_history')

    return render(request, 'students/promote_class.html', {
        'class_choices':   class_choices,
        'section_choices': section_choices,
        'current_year':    current_year,
        'from_class':      from_class,
        'from_section':    from_section,
        'from_year':       from_year,
        'to_year':         to_year,
        'next_cls':        next_cls,
        'students':        students,
        'status_choices':  AcademicRecord.STATUS_CHOICES,
        'next_class_label': dict(CLASS_CHOICES).get(next_cls, '') if next_cls else 'Graduated',
    })


# ─── Promotion History ────────────────────────────────────────────────────────

@login_required
def promotion_history(request):
    """List all academic records with filtering."""
    records = AcademicRecord.objects.select_related('student', 'promoted_by').all()

    q          = request.GET.get('q', '')
    year_f     = request.GET.get('year', '')
    class_f    = request.GET.get('from_class', '')
    status_f   = request.GET.get('status', '')

    if q:
        records = records.filter(
            Q(student__first_name__icontains=q) |
            Q(student__last_name__icontains=q) |
            Q(student__roll_number__icontains=q)
        )
    if year_f:
        records = records.filter(academic_year=year_f)
    if class_f:
        records = records.filter(from_class=class_f)
    if status_f:
        records = records.filter(status=status_f)

    # Distinct years for filter dropdown.
    years = AcademicRecord.objects.values_list('academic_year', flat=True).distinct().order_by('-academic_year')

    paginator = Paginator(records, 50)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'students/promotion_history.html', {
        'page_obj':       page,
        'q':              q,
        'year_f':         year_f,
        'class_f':        class_f,
        'status_f':       status_f,
        'class_choices':  CLASS_CHOICES,
        'status_choices': AcademicRecord.STATUS_CHOICES,
        'years':          years,
        'total':          records.count(),
    })
