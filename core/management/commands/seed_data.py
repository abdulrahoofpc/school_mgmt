import datetime
import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from students.models import Student
from teachers.models import Teacher, SalaryRecord
from fees.models import FeeStructure, Payment
from expenses.models import Expense

User = get_user_model()

FIRST_NAMES = ['Arjun', 'Priya', 'Rahul', 'Anjali', 'Vikram', 'Sneha', 'Rohan', 'Pooja',
               'Kiran', 'Deepa', 'Suresh', 'Meena', 'Arun', 'Kavya', 'Nitin', 'Radha',
               'Amit', 'Divya', 'Sanjay', 'Lakshmi']
LAST_NAMES  = ['Sharma', 'Patel', 'Nair', 'Reddy', 'Kumar', 'Singh', 'Iyer', 'Menon',
               'Gupta', 'Rao', 'Joshi', 'Verma', 'Pillai', 'Chandra', 'Das']
PARENT_FIRST = ['Suresh', 'Ramesh', 'Mahesh', 'Rajesh', 'Naresh', 'Dinesh', 'Ganesh']


class Command(BaseCommand):
    help = 'Seed the database with sample data'

    def handle(self, *args, **kwargs):
        self.stdout.write('🌱 Seeding database...')

        # ── Users ──────────────────────────────────
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@school.com', 'admin123',
                                          first_name='Admin', last_name='User', role='admin')
            self.stdout.write(self.style.SUCCESS('  ✓ Admin user created'))

        for username, role, pw, fn, ln in [
            ('teacher1',    'teacher',    'teacher123', 'Priya',   'Sharma'),
            ('teacher2',    'teacher',    'teacher123', 'Ravi',    'Kumar'),
            ('accountant1', 'accountant', 'acc123',     'Anjali',  'Patel'),
        ]:
            if not User.objects.filter(username=username).exists():
                User.objects.create_user(username, f'{username}@school.com', pw,
                                         first_name=fn, last_name=ln, role=role)
        self.stdout.write(self.style.SUCCESS('  ✓ Staff users created'))

        # ── Teachers ───────────────────────────────
        subjects = ['mathematics', 'science', 'english', 'hindi', 'social_science',
                    'computer', 'physical_education', 'arts']
        teachers = []
        for i, (fn, ln, subj) in enumerate([
            ('Priya',    'Sharma',   'mathematics'),
            ('Ravi',     'Kumar',    'science'),
            ('Sunita',   'Patel',    'english'),
            ('Mohan',    'Reddy',    'hindi'),
            ('Kavitha',  'Nair',     'social_science'),
            ('Rajesh',   'Iyer',     'computer'),
            ('Shalini',  'Menon',    'arts'),
            ('Deepak',   'Singh',    'physical_education'),
        ], 1):
            t, _ = Teacher.objects.get_or_create(
                employee_id=f'EMP{i:03d}',
                defaults=dict(
                    first_name=fn, last_name=ln, subject=subj,
                    phone=f'98765{i:05d}', email=f'{fn.lower()}@school.com',
                    date_of_joining=datetime.date(2020, 6, i % 28 + 1),
                    monthly_salary=random.choice([25000, 28000, 30000, 32000, 35000]),
                )
            )
            teachers.append(t)
        self.stdout.write(self.style.SUCCESS(f'  ✓ {len(teachers)} teachers created'))

        # ── Salary records ─────────────────────────
        year = datetime.date.today().year
        count = 0
        for t in teachers:
            for m in range(1, datetime.date.today().month + 1):
                _, created = SalaryRecord.objects.get_or_create(
                    teacher=t, month=m, year=year,
                    defaults=dict(
                        amount=t.monthly_salary,
                        status='paid' if m < datetime.date.today().month else 'unpaid',
                        payment_date=datetime.date(year, m, 28) if m < datetime.date.today().month else None,
                    )
                )
                if created:
                    count += 1
        self.stdout.write(self.style.SUCCESS(f'  ✓ {count} salary records created'))

        # ── Students ───────────────────────────────
        students = []
        roll_counter = 1
        for cls in ['5', '6', '7', '8']:
            for section in ['A', 'B']:
                for _ in range(random.randint(4, 6)):
                    fn = random.choice(FIRST_NAMES)
                    ln = random.choice(LAST_NAMES)
                    pn = random.choice(PARENT_FIRST)
                    roll = f'{cls}{section}{roll_counter:03d}'
                    roll_counter += 1
                    s, created = Student.objects.get_or_create(
                        roll_number=roll,
                        defaults=dict(
                            first_name=fn, last_name=ln,
                            student_class=cls, section=section,
                            gender=random.choice(['male', 'female']),
                            parent_name=f'{pn} {ln}',
                            parent_phone=f'91234{roll_counter:05d}',
                            parent_email=f'{fn.lower()}.parent@gmail.com',
                            admission_date=datetime.date(year, 6, 1),
                            date_of_birth=datetime.date(year - int(cls) - 4, 1, random.randint(1, 28)),
                        )
                    )
                    if created:
                        students.append(s)
        self.stdout.write(self.style.SUCCESS(f'  ✓ {len(students)} students created'))

        # ── Fee structures + Payments ───────────────
        academic_year = f'{year}-{str(year + 1)[2:]}'
        fee_count = pay_count = 0
        for s in Student.objects.all():
            fs, created = FeeStructure.objects.get_or_create(
                student=s, academic_year=academic_year,
                defaults=dict(
                    admission_fee=5000,
                    term1_fee=8000, term2_fee=8000, term3_fee=8000,
                    snacks_fee=3000, book_fee=2500, uniform_fee=1500,
                )
            )
            if created:
                fee_count += 1
                # Random payment status
                scenario = random.choice(['full', 'partial', 'none'])
                if scenario in ('full', 'partial'):
                    amount = fs.total_fee if scenario == 'full' else random.randint(5000, int(fs.total_fee) - 1000)
                    p = Payment(
                        fee_structure=fs, student=s,
                        amount_paid=amount,
                        payment_date=datetime.date(year, random.randint(6, 9), random.randint(1, 28)),
                        payment_mode=random.choice(['cash', 'online', 'upi']),
                        status='paid' if scenario == 'full' else 'partial',
                    )
                    p.save()
                    pay_count += 1
        self.stdout.write(self.style.SUCCESS(f'  ✓ {fee_count} fee structures, {pay_count} payments created'))

        # ── Expenses ───────────────────────────────
        admin_user = User.objects.filter(username='admin').first()
        expense_data = [
            ('Stationery Purchase', 'stationary', 4500, 7),
            ('Annual Day Program', 'program', 25000, 8),
            ('Projector Purchase', 'fixed_asset', 35000, 6),
            ('Staff Gifts - Teachers Day', 'gift', 8000, 9),
            ('Field Trip Transportation', 'travelling', 12000, 10),
            ('Sports Equipment', 'stationary', 7500, 8),
            ('Office Printer', 'fixed_asset', 18000, 7),
            ('Science Exhibition', 'program', 15000, 9),
            ('Miscellaneous', 'other', 3200, 10),
            ('Parent Meeting Refreshments', 'program', 2800, 8),
        ]
        exp_count = 0
        for title, cat, amt, month in expense_data:
            e, created = Expense.objects.get_or_create(
                title=title,
                defaults=dict(
                    category=cat, amount=amt,
                    expense_date=datetime.date(year, month, random.randint(1, 25)),
                    created_by=admin_user,
                )
            )
            if created:
                exp_count += 1
        self.stdout.write(self.style.SUCCESS(f'  ✓ {exp_count} expenses created'))

        self.stdout.write(self.style.SUCCESS('\n✅ Database seeded successfully!'))
        self.stdout.write(self.style.WARNING('\nLogin credentials:'))
        self.stdout.write('  Admin:      admin / admin123')
        self.stdout.write('  Teacher:    teacher1 / teacher123')
        self.stdout.write('  Accountant: accountant1 / acc123')
