from django.db import models


SUBJECT_CHOICES = [
    ('mathematics', 'Mathematics'),
    ('science', 'Science'),
    ('english', 'English'),
    ('hindi', 'Hindi'),
    ('social_science', 'Social Science'),
    ('computer', 'Computer'),
    ('physical_education', 'Physical Education'),
    ('arts', 'Arts'),
    ('music', 'Music'),
    ('other', 'Other'),
]


class Teacher(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    employee_id = models.CharField(max_length=20, unique=True)
    subject = models.CharField(max_length=50, choices=SUBJECT_CHOICES)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    date_of_joining = models.DateField()
    monthly_salary = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    photo = models.ImageField(upload_to='teachers/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['first_name', 'last_name']

    def __str__(self):
        return f"{self.full_name} ({self.get_subject_display()})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def total_salary_paid(self):
        return self.salary_records.filter(status='paid').aggregate(
            total=models.Sum('amount')
        )['total'] or 0


class SalaryRecord(models.Model):
    STATUS_CHOICES = [('paid', 'Paid'), ('unpaid', 'Unpaid')]
    MONTH_CHOICES = [
        (1, 'January'), (2, 'February'), (3, 'March'),
        (4, 'April'), (5, 'May'), (6, 'June'),
        (7, 'July'), (8, 'August'), (9, 'September'),
        (10, 'October'), (11, 'November'), (12, 'December'),
    ]

    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='salary_records')
    month = models.IntegerField(choices=MONTH_CHOICES)
    year = models.IntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='unpaid')
    payment_date = models.DateField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-year', '-month']
        unique_together = ['teacher', 'month', 'year']

    def __str__(self):
        return f"{self.teacher.full_name} - {self.get_month_display()} {self.year}"
