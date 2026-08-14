# Generated for ActivationLab complete project.
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="OnboardingSession",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("visitor_id", models.CharField(db_index=True, max_length=100, unique=True)),
                ("company_name", models.CharField(blank=True, max_length=120)),
                ("business_type", models.CharField(blank=True, max_length=80)),
                ("variant", models.CharField(choices=[("control", "Control"), ("guided", "Guided")], db_index=True, max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("activated_at", models.DateTimeField(blank=True, db_index=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="Campaign",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("channel", models.CharField(default="email", max_length=30)),
                ("status", models.CharField(choices=[("draft", "Draft"), ("active", "Active")], default="draft", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("session", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="campaigns", to="onboarding.onboardingsession")),
            ],
        ),
        migrations.CreateModel(
            name="CopilotInteraction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("provider", models.CharField(max_length=40)),
                ("user_goal", models.TextField(blank=True)),
                ("response", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("session", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="copilot_interactions", to="onboarding.onboardingsession")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Customer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("external_id", models.CharField(max_length=120)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("first_name", models.CharField(blank=True, max_length=80)),
                ("last_name", models.CharField(blank=True, max_length=80)),
                ("lifetime_value", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("subscribed", models.BooleanField(default=True)),
                ("tags", models.JSONField(blank=True, default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("session", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="customers", to="onboarding.onboardingsession")),
            ],
        ),
        migrations.CreateModel(
            name="CustomerImport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_filename", models.CharField(max_length=255)),
                ("file", models.FileField(upload_to="imports/")),
                ("status", models.CharField(choices=[("pending", "Pending"), ("processing", "Processing"), ("completed", "Completed"), ("failed", "Failed")], db_index=True, default="pending", max_length=20)),
                ("total_rows", models.PositiveIntegerField(default=0)),
                ("imported_rows", models.PositiveIntegerField(default=0)),
                ("failed_rows", models.PositiveIntegerField(default=0)),
                ("error_message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("session", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="imports", to="onboarding.onboardingsession")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Integration",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("provider", models.CharField(default="demo-commerce", max_length=80)),
                ("external_store_id", models.CharField(blank=True, max_length=120)),
                ("connected_at", models.DateTimeField(auto_now_add=True)),
                ("session", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="integration", to="onboarding.onboardingsession")),
            ],
        ),
        migrations.CreateModel(
            name="OnboardingStep",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key", models.CharField(choices=[("workspace_created", "Workspace created"), ("integration_connected", "Integration connected"), ("data_imported", "Data imported"), ("campaign_created", "Campaign created")], db_index=True, max_length=40)),
                ("completed_at", models.DateTimeField(auto_now_add=True)),
                ("session", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="steps", to="onboarding.onboardingsession")),
            ],
            options={"ordering": ["completed_at"]},
        ),
        migrations.CreateModel(
            name="ProductEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(db_index=True, max_length=60)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("session", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="events", to="onboarding.onboardingsession")),
            ],
            options={"ordering": ["created_at"]},
        ),
        migrations.AddConstraint(
            model_name="onboardingstep",
            constraint=models.UniqueConstraint(fields=("session", "key"), name="unique_completed_step_per_session"),
        ),
        migrations.AddConstraint(
            model_name="customer",
            constraint=models.UniqueConstraint(fields=("session", "external_id"), name="unique_customer_per_session"),
        ),
        migrations.AddIndex(
            model_name="customer",
            index=models.Index(fields=["session", "email"], name="cust_session_email_idx"),
        ),
    ]
