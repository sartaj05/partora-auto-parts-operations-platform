from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [("api", "0002_product_barcode")]
    operations = [
        migrations.CreateModel(
            name="VehicleFitment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("make", models.CharField(max_length=80)),
                ("model", models.CharField(max_length=80)),
                ("year_from", models.PositiveIntegerField()),
                ("year_to", models.PositiveIntegerField()),
                ("variant", models.CharField(blank=True, max_length=100)),
                ("engine", models.CharField(blank=True, max_length=80)),
                ("oem_number", models.CharField(blank=True, max_length=80)),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="fitments", to="api.product")),
            ],
        ),
    ]
