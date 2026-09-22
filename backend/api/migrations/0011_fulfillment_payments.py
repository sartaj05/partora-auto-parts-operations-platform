from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [("api", "0010_governance")]

    operations = [
        migrations.AddField(
            model_name="product",
            name="reserved_qty",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="salesorder",
            name="fulfillment_status",
            field=models.CharField(
                choices=[
                    ("confirmed", "Confirmed"),
                    ("picking", "Picking"),
                    ("packed", "Packed"),
                    ("dispatched", "Dispatched"),
                    ("delivered", "Delivered"),
                    ("cancelled", "Cancelled"),
                ],
                default="confirmed",
                max_length=20,
            ),
        ),
        migrations.AddField(model_name="salesorder", name="shipping_address", field=models.CharField(blank=True, max_length=240)),
        migrations.AddField(model_name="salesorder", name="reserved_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="salesorder", name="dispatched_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="salesorder", name="delivered_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.CreateModel(
            name="SalesOrderItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity", models.PositiveIntegerField()),
                ("unit_price", models.DecimalField(decimal_places=2, max_digits=12)),
                ("line_total", models.DecimalField(decimal_places=2, max_digits=14)),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="sales_order_items", to="api.product")),
                ("sales_order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="api.salesorder")),
            ],
        ),
        migrations.CreateModel(
            name="Payment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=14)),
                ("method", models.CharField(choices=[("cash", "Cash"), ("bank", "Bank transfer"), ("upi", "UPI"), ("card", "Card"), ("credit", "Credit terms")], default="bank", max_length=20)),
                ("reference", models.CharField(blank=True, max_length=80)),
                ("paid_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="partora_payments", to=settings.AUTH_USER_MODEL)),
                ("invoice", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="payments", to="api.invoice")),
            ],
        ),
    ]
