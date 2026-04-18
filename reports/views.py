from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from students.models import Student
from teachers.models import Teacher, SalaryRecord
from fees.models import Payment, FeeStructure
from expenses.models import Expense, CATEGORY_CHOICES
import datetime


@login_required
def student_fee_report(request):
    year = request.GET.get('year', '')
    class_filter = request.GET.get('class', '')
    fee_structures = FeeStructure.objects.select_related('student').all()
    if year:
        fee_structures = fee_structures.filter(academic_year=year)
    if class_filter:
        fee_structures = fee_structures.filter(student__student_class=class_filter)
    report_data = []
    for fs in fee_structures:
        report_data.append({
            'student': fs.student,
            'academic_year': fs.academic_year,
            'total_fee': fs.total_fee,
            'total_paid': fs.total_paid,
            'balance': fs.balance,
            'status': fs.payment_status,
        })
    total_fee = sum(r['total_fee'] for r in report_data)
    total_paid = sum(r['total_paid'] for r in report_data)
    total_balance = sum(r['balance'] for r in report_data)
    from students.models import CLASS_CHOICES
    return render(request, 'reports/student_fee_report.html', {
        'report_data': report_data,
        'total_fee': total_fee,
        'total_paid': total_paid,
        'total_balance': total_balance,
        'year': year,
        'class_filter': class_filter,
        'class_choices': CLASS_CHOICES,
    })


@login_required
def salary_report(request):
    month = request.GET.get('month', '')
    year = request.GET.get('year', str(datetime.date.today().year))
    status = request.GET.get('status', '')
    records = SalaryRecord.objects.select_related('teacher').all()
    if month:
        records = records.filter(month=month)
    if year:
        records = records.filter(year=year)
    if status:
        records = records.filter(status=status)
    total_amount = records.aggregate(t=Sum('amount'))['t'] or 0
    total_paid = records.filter(status='paid').aggregate(t=Sum('amount'))['t'] or 0
    total_unpaid = records.filter(status='unpaid').aggregate(t=Sum('amount'))['t'] or 0
    return render(request, 'reports/salary_report.html', {
        'records': records,
        'total_amount': total_amount,
        'total_paid': total_paid,
        'total_unpaid': total_unpaid,
        'month': month,
        'year': year,
        'status': status,
        'months': SalaryRecord.MONTH_CHOICES,
        'years': range(2020, datetime.date.today().year + 2),
    })


@login_required
def expense_report(request):
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    category = request.GET.get('category', '')
    expenses = Expense.objects.all()
    if date_from:
        expenses = expenses.filter(expense_date__gte=date_from)
    if date_to:
        expenses = expenses.filter(expense_date__lte=date_to)
    if category:
        expenses = expenses.filter(category=category)
    total = expenses.aggregate(t=Sum('amount'))['t'] or 0
    # Category breakdown
    by_category = expenses.values('category').annotate(total=Sum('amount')).order_by('-total')
    return render(request, 'reports/expense_report.html', {
        'expenses': expenses,
        'total': total,
        'by_category': by_category,
        'date_from': date_from,
        'date_to': date_to,
        'category': category,
        'category_choices': CATEGORY_CHOICES,
    })


@login_required
def financial_summary(request):
    year = request.GET.get('year', str(datetime.date.today().year))
    # Monthly breakdown
    monthly_data = []
    total_income_year = 0
    total_expense_year = 0
    for m in range(1, 13):
        income = Payment.objects.filter(
            payment_date__year=year, payment_date__month=m
        ).aggregate(t=Sum('amount_paid'))['t'] or 0
        expense = Expense.objects.filter(
            expense_date__year=year, expense_date__month=m
        ).aggregate(t=Sum('amount'))['t'] or 0
        salary = SalaryRecord.objects.filter(
            year=year, month=m, status='paid'
        ).aggregate(t=Sum('amount'))['t'] or 0
        total_exp = expense + salary
        total_income_year += float(income)
        total_expense_year += float(total_exp)
        monthly_data.append({
            'month': datetime.date(int(year), m, 1).strftime('%B'),
            'income': income,
            'expenses': total_exp,
            'profit': income - total_exp,
        })
    return render(request, 'reports/financial_summary.html', {
        'monthly_data': monthly_data,
        'year': year,
        'years': range(2020, datetime.date.today().year + 2),
        'total_income': total_income_year,
        'total_expenses': total_expense_year,
        'net_profit': total_income_year - total_expense_year,
    })
