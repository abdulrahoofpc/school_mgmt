from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0002_alter_student_student_class'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # 1. Remove the old global unique constraint on roll_number.
        migrations.AlterField(
            model_name='student',
            name='roll_number',
            field=models.CharField(max_length=20),
        ),
        # 2. Add academic_year field to Student.
        migrations.AddField(
            model_name='student',
            name='academic_year',
            field=models.CharField(blank=True, max_length=10),
        ),
        # 3. Add the new unique_together constraint: roll unique per class+section.
        migrations.AddConstraint(
            model_name='student',
            constraint=models.UniqueConstraint(
                fields=['student_class', 'section', 'roll_number'],
                name='unique_roll_per_class_section',
            ),
        ),
        # 4. Create the AcademicRecord model.
        migrations.CreateModel(
            name='AcademicRecord',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID'
                )),
                ('academic_year',    models.CharField(max_length=10)),
                ('from_class',       models.CharField(
                    choices=[
                        ('IPS1','IPS 1'),('IPS2','IPS 2'),
                        ('1','Class 1'),('2','Class 2'),('3','Class 3'),
                        ('4','Class 4'),('5','Class 5'),('6','Class 6'),
                        ('7','Class 7'),('8','Class 8'),('9','Class 9'),
                        ('10','Class 10'),('11','Class 11'),('12','Class 12'),
                    ],
                    max_length=5
                )),
                ('from_section',     models.CharField(
                    choices=[('A','A'),('B','B'),('C','C'),('D','D')],
                    max_length=5
                )),
                ('from_roll_number', models.CharField(max_length=20)),
                ('to_class',         models.CharField(
                    blank=True,
                    choices=[
                        ('IPS1','IPS 1'),('IPS2','IPS 2'),
                        ('1','Class 1'),('2','Class 2'),('3','Class 3'),
                        ('4','Class 4'),('5','Class 5'),('6','Class 6'),
                        ('7','Class 7'),('8','Class 8'),('9','Class 9'),
                        ('10','Class 10'),('11','Class 11'),('12','Class 12'),
                    ],
                    max_length=5
                )),
                ('to_section',       models.CharField(
                    blank=True,
                    choices=[('A','A'),('B','B'),('C','C'),('D','D')],
                    max_length=5
                )),
                ('to_roll_number',   models.CharField(blank=True, max_length=20)),
                ('status',           models.CharField(
                    choices=[
                        ('promoted','Promoted'),
                        ('failed','Failed / Detained'),
                        ('transferred','Transferred Out'),
                        ('graduated','Graduated'),
                        ('withdrawn','Withdrawn'),
                    ],
                    max_length=20
                )),
                ('remarks',   models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('promoted_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='promotions_made',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='academic_records',
                    to='students.student',
                )),
            ],
            options={
                'verbose_name': 'Academic Record',
                'verbose_name_plural': 'Academic Records',
                'ordering': ['-created_at'],
            },
        ),
        # 5. Unique constraint: one record per student per academic year.
        migrations.AddConstraint(
            model_name='academicrecord',
            constraint=models.UniqueConstraint(
                fields=['student', 'academic_year'],
                name='unique_record_per_student_year',
            ),
        ),
    ]
