from django.db import models


class OnboardingSession(models.Model):
    VARIANT_CONTROL = "control"
    VARIANT_GUIDED = "guided"
    VARIANT_CHOICES = [
        (VARIANT_CONTROL, "Control"),
        (VARIANT_GUIDED, "Guided"),
    ]

    visitor_id = models.CharField(max_length=100, unique=True, db_index=True)
    company_name = models.CharField(max_length=120, blank=True)
    business_type = models.CharField(max_length=80, blank=True)
    variant = models.CharField(max_length=20, choices=VARIANT_CHOICES, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    activated_at = models.DateTimeField(null=True, blank=True, db_index=True)

    def __str__(self):
        return f"{self.visitor_id} ({self.variant})"


class OnboardingStep(models.Model):
    STEP_WORKSPACE = "workspace_created"
    STEP_INTEGRATION = "integration_connected"
    STEP_IMPORT = "data_imported"
    STEP_CAMPAIGN = "campaign_created"

    STEP_CHOICES = [
        (STEP_WORKSPACE, "Workspace created"),
        (STEP_INTEGRATION, "Integration connected"),
        (STEP_IMPORT, "Data imported"),
        (STEP_CAMPAIGN, "Campaign created"),
    ]

    session = models.ForeignKey(OnboardingSession, related_name="steps", on_delete=models.CASCADE)
    key = models.CharField(max_length=40, choices=STEP_CHOICES, db_index=True)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["session", "key"], name="unique_completed_step_per_session")
        ]
        ordering = ["completed_at"]

    def __str__(self):
        return f"{self.session.visitor_id}: {self.key}"


class ProductEvent(models.Model):
    session = models.ForeignKey(OnboardingSession, related_name="events", on_delete=models.CASCADE)
    name = models.CharField(max_length=60, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.session.visitor_id}: {self.name}"


class Integration(models.Model):
    session = models.OneToOneField(OnboardingSession, related_name="integration", on_delete=models.CASCADE)
    provider = models.CharField(max_length=80, default="demo-commerce")
    external_store_id = models.CharField(max_length=120, blank=True)
    connected_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.session.visitor_id}: {self.provider}"


class Campaign(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_ACTIVE = "active"
    STATUS_CHOICES = [(STATUS_DRAFT, "Draft"), (STATUS_ACTIVE, "Active")]

    session = models.ForeignKey(OnboardingSession, related_name="campaigns", on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    channel = models.CharField(max_length=30, default="email")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.session.visitor_id}: {self.name}"


class Customer(models.Model):
    session = models.ForeignKey(OnboardingSession, related_name="customers", on_delete=models.CASCADE)
    external_id = models.CharField(max_length=120)
    email = models.EmailField(blank=True)
    first_name = models.CharField(max_length=80, blank=True)
    last_name = models.CharField(max_length=80, blank=True)
    lifetime_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    subscribed = models.BooleanField(default=True)
    tags = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["session", "external_id"], name="unique_customer_per_session")
        ]
        indexes = [models.Index(fields=["session", "email"], name="cust_session_email_idx")]

    def __str__(self):
        return self.email or self.external_id


class CustomerImport(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
    ]

    session = models.ForeignKey(OnboardingSession, related_name="imports", on_delete=models.CASCADE)
    source_filename = models.CharField(max_length=255)
    file = models.FileField(upload_to="imports/")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)
    total_rows = models.PositiveIntegerField(default=0)
    imported_rows = models.PositiveIntegerField(default=0)
    failed_rows = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.source_filename} ({self.status})"


class CopilotInteraction(models.Model):
    session = models.ForeignKey(OnboardingSession, related_name="copilot_interactions", on_delete=models.CASCADE)
    provider = models.CharField(max_length=40)
    user_goal = models.TextField(blank=True)
    response = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.session.visitor_id}: {self.provider}"
