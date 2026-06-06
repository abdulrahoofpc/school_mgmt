from django.db import models
from django.conf import settings


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

# Maps each class to the class students move into when promoted.
# '12' maps to None (graduated).
CLASS_PROGRESSION = {
    'IPS1': 'IPS2',
    'IPS2': '1',
    '1': '2', '2': '3',  '3': '4',  '4': '5',
    '5': '6', '6': '7',  '7': '8',  '8': '9',
    '9': '10','10': '11','11': '12','12': None,
}


class Student(models.Model):
    first_name     = models.CharField(max_length=100)
    last_name      = models.CharField(max_length=100)
    student_class  = models.CharField(max_length=5, choices=CLASS_CHOICES)
    section        = models.CharField(max_length=5, choices=SECTION_CHOICES)
    # Roll number is unique within a class+section — NOT globally unique.
    # Two students in different classes may share the same roll number.
    roll_number    = models.CharField(max_length=20)
    # Current academic year the student is enrolled in, e.g. "2025-26".
    academic_year  = models.CharField(max_length=10, blank=True)
    date_of_birth  = models.DateField(null=True, blank=True)
    gender         = models.CharField(
        max_length=10,
        choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')]
    )
    parent_name    = models.CharField(max_length=200)
    parent_phone   = models.CharField(max_length=15)
    parent_email   = models.EmailField(blank=True)
    address        = models.TextField(blank=True)
    admission_date = models.DateField()
    photo          = models.ImageField(upload_to='students/', blank=True, null=True)
    is_active      = models.BooleanField(default=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['student_class', 'section', 'first_name']
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
        # Roll number must be unique within the same class and section.
        # Students in different classes can share the same roll number.
        constraints = [
            models.UniqueConstraint(
                fields=['student_class', 'section', 'roll_number'],
                name='unique_roll_per_class_section',
            )
        ]

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

    @property
    def next_class(self):
        """Returns the class this student would move to on promotion, or None if graduating."""
        return CLASS_PROGRESSION.get(self.student_class)

    @property
    def latest_promotion(self):
        return self.academic_records.order_by('-created_at').first()


class AcademicRecord(models.Model):
    """
    Records the outcome for a student at the end of each academic year.
    Created when a student is promoted, failed, transferred, or graduated.
    Preserves the full academic history for reporting.
    """
    STATUS_CHOICES = [
        ('promoted',    'Promoted'),
        ('failed',      'Failed / Detained'),
        ('transferred', 'Transferred Out'),
        ('graduated',   'Graduated'),
        ('withdrawn',   'Withdrawn'),
    ]

    student          = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name='academic_records'
    )
    academic_year    = models.CharField(max_length=10)        # e.g. "2025-26"
    from_class       = models.CharField(max_length=5, choices=CLASS_CHOICES)
    from_section     = models.CharField(max_length=5, choices=SECTION_CHOICES)
    from_roll_number = models.CharField(max_length=20)
    to_class         = models.CharField(max_length=5, choices=CLASS_CHOICES, blank=True)
    to_section       = models.CharField(max_length=5, choices=SECTION_CHOICES, blank=True)
    to_roll_number   = models.CharField(max_length=20, blank=True)
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES)
    remarks          = models.TextField(blank=True)
    promoted_by      = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='promotions_made'
    )
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Academic Record'
        verbose_name_plural = 'Academic Records'
        # Only one promotion record per student per academic year.
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'academic_year'],
                name='unique_record_per_student_year',
            )
        ]

    def __str__(self):
        return (
            f"{self.student.full_name} – {self.academic_year} "
            f"({self.get_status_display()})"
        )

    @property
    def from_class_display(self):
        return dict(CLASS_CHOICES).get(self.from_class, self.from_class)

    @property
    def to_class_display(self):
        return dict(CLASS_CHOICES).get(self.to_class, self.to_class) if self.to_class else '—'
