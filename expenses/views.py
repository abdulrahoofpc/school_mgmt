from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Expense, CATEGORY_CHOICES
from .serializers import ExpenseSerializer
import datetime


class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['category']
    search_fields = ['title', 'description']


@login_required
def expense_list(request):
    queryset = Expense.objects.all()
    q = request.GET.get('q', '')
    category = request.GET.get('category', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if q:
        queryset = queryset.filter(Q(title__icontains=q) | Q(description__icontains=q))
    if category:
        queryset = queryset.filter(category=category)
    if date_from:
        queryset = queryset.filter(expense_date__gte=date_from)
    if date_to:
        queryset = queryset.filter(expense_date__lte=date_to)
    total_amount = queryset.aggregate(t=Sum('amount'))['t'] or 0
    paginator = Paginator(queryset, 20)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'expenses/expense_list.html', {
        'page_obj': page,
        'q': q,
        'category': category,
        'date_from': date_from,
        'date_to': date_to,
        'category_choices': CATEGORY_CHOICES,
        'total_amount': total_amount,
        'total': queryset.count(),
        'month_choices': _expense_month_choices(),
    })


@login_required
def expense_create(request):
    if request.method == 'POST':
        try:
            expense = Expense(
                title=request.POST['title'],
                category=request.POST['category'],
                amount=request.POST['amount'],
                expense_date=request.POST['expense_date'],
                description=request.POST.get('description', ''),
                created_by=request.user,
            )
            if 'receipt' in request.FILES:
                expense.receipt = request.FILES['receipt']
            expense.save()
            messages.success(request, 'Expense recorded successfully.')
            return redirect('expenses:list')
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return render(request, 'expenses/expense_form.html', {
        'action': 'Add',
        'category_choices': CATEGORY_CHOICES,
        'today': datetime.date.today(),
    })


@login_required
def expense_edit(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        try:
            expense.title = request.POST['title']
            expense.category = request.POST['category']
            expense.amount = request.POST['amount']
            expense.expense_date = request.POST['expense_date']
            expense.description = request.POST.get('description', '')
            if 'receipt' in request.FILES:
                expense.receipt = request.FILES['receipt']
            expense.save()
            messages.success(request, 'Expense updated.')
            return redirect('expenses:list')
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return render(request, 'expenses/expense_form.html', {
        'action': 'Edit',
        'expense': expense,
        'category_choices': CATEGORY_CHOICES,
        'today': datetime.date.today(),  # ← this was missing
    })


@login_required
def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Expense deleted.')
        return redirect('expenses:list')
    return render(request, 'expenses/expense_confirm_delete.html', {'expense': expense})


@login_required
def expense_receipt(request, pk):
    """Print-ready receipt for a single expense entry."""
    expense = get_object_or_404(Expense.objects.select_related('created_by'), pk=pk)
    return render(request, 'expenses/expense_receipt.html', {'expense': expense})


def _expense_month_choices():
    """Distinct YYYY-MM values for which expenses exist, newest first."""
    import datetime
    months = set()
    for d in Expense.objects.values_list('expense_date', flat=True):
        if d:
            months.add((d.year, d.month))
    out = []
    for y, m in sorted(months, reverse=True):
        out.append((f"{y}-{m:02d}", datetime.date(y, m, 1).strftime('%B %Y')))
    return out


@login_required
def expense_monthly_print(request):
    """Print-ready report listing all expenses for a selected month."""
    import datetime
    month = request.GET.get('month', '')
    if not month:
        today = datetime.date.today()
        month = f"{today.year}-{today.month:02d}"

    expenses = Expense.objects.none()
    total_amount = 0
    category_totals = []
    label = month
    try:
        year, mon = month.split('-')
        year, mon = int(year), int(mon)
        expenses = Expense.objects.filter(
            expense_date__year=year, expense_date__month=mon
        ).select_related('created_by').order_by('expense_date')
        total_amount = expenses.aggregate(t=Sum('amount'))['t'] or 0
        label = datetime.date(year, mon, 1).strftime('%B %Y')
        # per-category breakdown
        cat_map = {}
        for e in expenses:
            cat_map.setdefault(e.get_category_display(), 0)
            cat_map[e.get_category_display()] += e.amount
        category_totals = sorted(cat_map.items(), key=lambda kv: kv[1], reverse=True)
    except (ValueError, TypeError):
        messages.error(request, 'Invalid month selected.')

    return render(request, 'expenses/expense_monthly_print.html', {
        'expenses': expenses,
        'total_amount': total_amount,
        'month_value': month,
        'month_label': label,
        'category_totals': category_totals,
        'count': expenses.count() if expenses is not None else 0,
        'month_choices': _expense_month_choices(),
        'today': datetime.date.today(),
    })