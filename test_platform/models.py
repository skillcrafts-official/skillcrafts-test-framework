from django.db import models
import uuid


class TestRun(models.Model):
    RUN_TYPES = (
        ('full', 'Full Regression'),
        ('partial', 'Partial (selected endpoints)'),
    )
    STATUSES = (
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    run_type = models.CharField(max_length=10, choices=RUN_TYPES)
    status = models.CharField(max_length=10, choices=STATUSES, default='pending')
    selected_endpoints = models.JSONField(default=list, blank=True)  # для частичного запуска
    csv_file = models.FileField(upload_to='test_results/', null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    result_summary = models.JSONField(default=dict, blank=True)  # кол-во passed/failed

    def __str__(self):
        return f"{self.run_type} run [{self.status}]"


class WikiVisitCounter(models.Model):
    """Синглтон-модель для хранения общего и уникального числа посещений wiki."""
    total_visits = models.PositiveIntegerField(default=0)
    unique_visits = models.PositiveIntegerField(default=0)

    @classmethod
    def get_counter(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def save(self, *args, **kwargs):
        # Гарантируем, что всегда будет только одна запись с pk=1
        self.pk = 1
        super().save(*args, **kwargs)
