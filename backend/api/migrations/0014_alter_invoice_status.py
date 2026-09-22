from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("api", "0013_inventory_control")]

    operations = [
        migrations.AlterField(
            model_name="invoice",
            name="status",
            field=models.CharField(
                choices=[("issued", "Issued"), ("partial", "Partially paid"), ("paid", "Paid"), ("overdue", "Overdue"), ("cancelled", "Cancelled")],
                default="issued",
                max_length=20,
            ),
        ),
    ]
