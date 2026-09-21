from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies=[("api","0007_sales_flow")]
    operations=[migrations.CreateModel(name="Customer",fields=[
        ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),("name",models.CharField(max_length=140)),("company",models.CharField(blank=True,max_length=160)),("email",models.EmailField(blank=True,max_length=254)),("phone",models.CharField(blank=True,max_length=30)),("customer_type",models.CharField(choices=[("retail","Retail"),("dealer","Dealer"),("fleet","Fleet"),("workshop","Workshop")],default="retail",max_length=20)),("credit_limit",models.DecimalField(decimal_places=2,default=0,max_digits=14)),("payment_terms_days",models.PositiveIntegerField(default=0)),("outstanding_balance",models.DecimalField(decimal_places=2,default=0,max_digits=14)),("notes",models.TextField(blank=True)),("active",models.BooleanField(default=True)),("created_at",models.DateTimeField(auto_now_add=True))])]
