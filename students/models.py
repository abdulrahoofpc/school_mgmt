from django.db import models


CLASS_CHOICES = [
    ('IPS1', 'IPS 1'),
    ('IPS2', 'IPS 2'),
    ('1',    'Class 1'),
    ('2',    'Class 2'),
    ('3',    'Class 3'),
    ('4',    'Class 4'),
    ('5',    'Class 5'),
    ('6',    'Class 6'),
    ('7',    'Class 7'),
    ('8',    'Class 8'),
    ('9',    'Class 9'),
    ('10',   'Class 10'),
    ('11',   'Class 11'),
    ('12',   'Class 12'),
]

SECTION_CHOICES = [('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')]


class Student(models.Model):
    first_name    = models.CharField(max_length=100)
    last_name     = models.CharField(max_length=100)
    student_class = models.CharField(max_length=5, choices=CLASS_CHOICES)
    section       = models.CharField(max_length=5, choices=SECTION_CHOICES)
    roll_number   = models.CharField(max_length=20, unique=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender        = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')])
    parent_name   = models.CharField(max_length=200)
    parent_phone  = models.CharField(max_length=15)
    parent_email  = models.EmailField(blank=True)
    address       = models.TextField(blank=True)
    admission_date= models.DateField()
    photo         = models.ImageField(upload_to='students/', blank=True, null=True)
    is_active     = models.BooleanField(default=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['student_class', 'section', 'first_name']
        verbose_name = 'Student'
        verbose_name_plural = 'Students'

    def __str__(self):
        return f"{self.first_name} {self.last_name} (Class {self.student_class}-{self.section})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def total_fee_paid(self):
        from fees.models import Payment
        return self.payments.filter(status__in=['paid', 'partial']).aggregate(
            total=models.Sum('amount_paid')
        )['total'] or 0

    @property
    def total_fee_due(self):
        total_structure = sum(fs.total_fee for fs in self.fee_structures.all())
        return total_structure - self.total_fee_paid