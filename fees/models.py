from django.db import models
from students.models import Student


class FeeStructure(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fee_structures')
    academic_year = models.CharField(max_length=10)  # e.g. 2024-25
    admission_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    term1_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    term2_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    term3_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    snacks_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    book_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    uniform_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['student', 'academic_year']
        ordering = ['-academic_year']

    def __str__(self):
        return f"{self.student.full_name} - {self.academic_year}"

    @property
    def total_fee(self):
        return (
            self.admission_fee + self.term1_fee + self.term2_fee +
            self.term3_fee + self.snacks_fee + self.book_fee + self.uniform_fee
        )

    @property
    def total_paid(self):
        return self.payments.aggregate(
            total=models.Sum('amount_paid')
        )['total'] or 0

    @property
    def balance(self):
        return self.total_fee - self.total_paid

    @property
    def payment_status(self):
        paid = self.total_paid
        total = self.total_fee
        if paid == 0:
            return 'pending'
        elif paid >= total:
            return 'paid'
        else:
            return 'partial'


class Payment(models.Model):
    STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('partial', 'Partial'),
        ('pending', 'Pending'),
    ]
    PAYMENT_MODE_CHOICES = [
        ('cash', 'Cash'),
        ('cheque', 'Cheque'),
        ('online', 'Online Transfer'),
        ('upi', 'UPI'),
    ]

    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE, related_name='payments')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='payments')
    receipt_number = models.CharField(max_length=30, unique=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODE_CHOICES, default='cash')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='paid')
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date', '-created_at']

    def __str__(self):
        return f"Receipt #{self.receipt_number} - {self.student.full_name}"

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            import datetime
            last = Payment.objects.order_by('-id').first()
            next_id = (last.id + 1) if last else 1
            self.receipt_number = f"RCP{datetime.date.today().year}{next_id:05d}"
        super().save(*args, **kwargs)
