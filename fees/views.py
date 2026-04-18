from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import FeeStructure, Payment
from .serializers import FeeStructureSerializer, PaymentSerializer
from students.models import Student
import datetime


class FeeStructureViewSet(viewsets.ModelViewSet):
    queryset = FeeStructure.objects.all()
    serializer_class = FeeStructureSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['student', 'academic_year']
    search_fields = ['student__first_name', 'student__last_name', 'academic_year']


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['student', 'status', 'payment_mode']
    search_fields = ['receipt_number', 'student__first_name', 'student__last_name']


def get_current_year():
    today = datetime.date.today()
    return f"{today.year}-{str(today.year + 1)[2:]}"


@login_required
def fee_list(request):
    queryset = FeeStructure.objects.select_related('student').all()
    q = request.GET.get('q', '')
    year = request.GET.get('year', '')
    if q:
        queryset = queryset.filter(
            Q(student__first_name__icontains=q) | Q(student__last_name__icontains=q)
        )
    if year:
        queryset = queryset.filter(academic_year=year)
    paginator = Paginator(queryset, 20)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'fees/fee_list.html', {
        'page_obj': page,
        'q': q,
        'year': year,
        'total': queryset.count(),
    })


@login_required
def fee_create(request):
    if request.method == 'POST':
        try:
            student = get_object_or_404(Student, pk=request.POST['student'])
            fee = FeeStructure(
                student=student,
                academic_year=request.POST['academic_year'],
                admission_fee=request.POST.get('admission_fee') or 0,
                term1_fee=request.POST.get('term1_fee') or 0,
                term2_fee=request.POST.get('term2_fee') or 0,
                term3_fee=request.POST.get('term3_fee') or 0,
                snacks_fee=request.POST.get('snacks_fee') or 0,
                book_fee=request.POST.get('book_fee') or 0,
                uniform_fee=request.POST.get('uniform_fee') or 0,
            )
            fee.save()
            messages.success(request, 'Fee structure created.')
            return redirect('fees:detail', pk=fee.pk)
        except Exception as e:
            messages.error(request, f'Error: {e}')
    students = Student.objects.filter(is_active=True)
    return render(request, 'fees/fee_form.html', {
        'action': 'Create',
        'students': students,
        'current_year': get_current_year(),
    })


@login_required
def fee_detail(request, pk):
    fee = get_object_or_404(FeeStructure, pk=pk)
    payments = fee.payments.all()
    return render(request, 'fees/fee_detail.html', {
        'fee': fee,
        'payments': payments,
    })


@login_required
def fee_edit(request, pk):
    fee = get_object_or_404(FeeStructure, pk=pk)
    if request.method == 'POST':
        try:
            fee.academic_year = request.POST['academic_year']
            fee.admission_fee = request.POST.get('admission_fee') or 0
            fee.term1_fee = request.POST.get('term1_fee') or 0
            fee.term2_fee = request.POST.get('term2_fee') or 0
            fee.term3_fee = request.POST.get('term3_fee') or 0
            fee.snacks_fee = request.POST.get('snacks_fee') or 0
            fee.book_fee = request.POST.get('book_fee') or 0
            fee.uniform_fee = request.POST.get('uniform_fee') or 0
            fee.save()
            messages.success(request, 'Fee structure updated.')
            return redirect('fees:detail', pk=fee.pk)
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return render(request, 'fees/fee_form.html', {
        'action': 'Edit',
        'fee': fee,
        'current_year': get_current_year(),
    })


@login_required
def fee_delete(request, pk):
    fee = get_object_or_404(FeeStructure, pk=pk)
    if request.method == 'POST':
        fee.delete()
        messages.success(request, 'Fee structure deleted.')
        return redirect('fees:list')
    return render(request, 'fees/fee_confirm_delete.html', {'fee': fee})


@login_required
def payment_create(request, fee_pk):
    fee = get_object_or_404(FeeStructure, pk=fee_pk)
    if request.method == 'POST':
        try:
            payment = Payment(
                fee_structure=fee,
                student=fee.student,
                amount_paid=request.POST['amount_paid'],
                payment_date=request.POST['payment_date'],
                payment_mode=request.POST.get('payment_mode', 'cash'),
                status=request.POST.get('status', 'paid'),
                remarks=request.POST.get('remarks', ''),
            )
            payment.save()
            messages.success(request, f'Payment recorded. Receipt: {payment.receipt_number}')
            return redirect('fees:receipt', pk=payment.pk)
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return render(request, 'fees/payment_form.html', {
        'fee': fee,
        'today': datetime.date.today(),
        'payment_modes': Payment.PAYMENT_MODE_CHOICES,
    })


@login_required
def payment_receipt(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    return render(request, 'fees/receipt.html', {'payment': payment})


@login_required
def payment_list(request):
    queryset = Payment.objects.select_related('student', 'fee_structure').all()
    q = request.GET.get('q', '')
    status = request.GET.get('status', '')
    if q:
        queryset = queryset.filter(
            Q(receipt_number__icontains=q) |
            Q(student__first_name__icontains=q) |
            Q(student__last_name__icontains=q)
        )
    if status:
        queryset = queryset.filter(status=status)
    paginator = Paginator(queryset, 20)
    page = paginator.get_page(request.GET.get('page'))
    total_collected = queryset.aggregate(t=Sum('amount_paid'))['t'] or 0
    return render(request, 'fees/payment_list.html', {
        'page_obj': page,
        'q': q,
        'status': status,
        'total_collected': total_collected,
    })