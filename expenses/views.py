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