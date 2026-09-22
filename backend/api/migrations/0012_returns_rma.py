from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("api", "0011_fulfillment_payments")]

    operations = [
        migrations.CreateModel(
            name="ReturnRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("return_no", models.CharField(max_length=30, unique=True)),
                ("customer_name", models.CharField(max_length=140)),
                ("quantity", models.PositiveIntegerField(default=1)),
                ("reason", models.CharField(max_length=240)),
                ("warranty_expires", models.DateField(blank=True, null=True)),
                ("status", models.CharField(choices=[("requested", "Requested"), ("approved", "Approved"), ("received", "Received"), ("inspected", "Inspected"), ("resolved", "Resolved"), ("rejected", "Rejected")], default="requested", max_length=20)),
                ("resolution", models.CharField(blank=True, choices=[("refund", "Refund"), ("replacement", "Replacement"), ("credit", "Account credit"), ("restock", "Restock")], max_length=20)),
                ("inspection_notes", models.CharField(blank=True, max_length=300)),
                ("refund_amount", models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ("stock_restocked", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="return_requests", to=settings.AUTH_USER_MODEL)),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="return_requests", to="api.product")),
                ("sales_order", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="returns", to="api.salesorder")),
            ],
        ),
    ]
