from django.db import models


CATEGORY_CHOICES = [
    ('program', 'Program'),
    ('stationary', 'Stationary'),
    ('fixed_asset', 'Fixed Asset'),
    ('gift', 'Gift'),
    ('travelling', 'Travelling'),
    ('salary', 'Salary'),
    ('maintenance', 'Maintenance'),
    ('other', 'Other'),
]


class Expense(models.Model):
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    expense_date = models.DateField()
    description = models.TextField(blank=True)
    receipt = models.FileField(upload_to='expense_receipts/', blank=True, null=True)
    created_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-expense_date', '-created_at']

    def __str__(self):
        return f"{self.title} - ₹{self.amount} ({self.expense_date})"
