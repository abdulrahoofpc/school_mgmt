from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from students.models import Student
from teachers.models import Teacher, SalaryRecord
from fees.models import Payment, FeeStructure
from expenses.models import Expense
import datetime
import json


@login_required
def dashboard(request):
    today = datetime.date.today()
    current_year = today.year
    current_month = today.month

    # Summary cards
    total_students = Student.objects.filter(is_active=True).count()
    total_teachers = Teacher.objects.filter(is_active=True).count()

    total_income = Payment.objects.aggregate(t=Sum('amount_paid'))['t'] or 0
    total_expenses = Expense.objects.aggregate(t=Sum('amount'))['t'] or 0
    salary_expenses = SalaryRecord.objects.filter(status='paid').aggregate(t=Sum('amount'))['t'] or 0
    total_expenses_all = total_expenses + salary_expenses
    profit_loss = total_income - total_expenses_all

    # Monthly data for chart (last 12 months)
    months_labels = []
    income_data = []
    expense_data = []

    for i in range(11, -1, -1):
        # Step back i whole months from the first of the current month
        # (using 30-day steps drifts and can skip/duplicate months).
        total = (current_year * 12 + (current_month - 1)) - i
        d_year, d_month = divmod(total, 12)
        d_month += 1
        month_income = Payment.objects.filter(
            payment_date__year=d_year, payment_date__month=d_month
        ).aggregate(t=Sum('amount_paid'))['t'] or 0
        month_expense = Expense.objects.filter(
            expense_date__year=d_year, expense_date__month=d_month
        ).aggregate(t=Sum('amount'))['t'] or 0
        month_salary = SalaryRecord.objects.filter(
            year=d_year, month=d_month, status='paid'
        ).aggregate(t=Sum('amount'))['t'] or 0

        months_labels.append(datetime.date(d_year, d_month, 1).strftime('%b %Y'))
        income_data.append(float(month_income))
        expense_data.append(float(month_expense + month_salary))

    # Recent payments
    recent_payments = Payment.objects.select_related('student').order_by('-payment_date')[:10]

    # Fee pending
    pending_fees = FeeStructure.objects.all()
    pending_count = sum(1 for f in pending_fees if f.balance > 0)

    # Unpaid salaries this month
    unpaid_salaries = SalaryRecord.objects.filter(
        month=current_month, year=current_year, status='unpaid'
    ).count()

    context = {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_income': total_income,
        'total_expenses': total_expenses_all,
        'profit_loss': profit_loss,
        'pending_count': pending_count,
        'unpaid_salaries': unpaid_salaries,
        'recent_payments': recent_payments,
        'months_labels': json.dumps(months_labels),
        'income_data': json.dumps(income_data),
        'expense_data': json.dumps(expense_data),
    }
    return render(request, 'core/dashboard.html', context)
