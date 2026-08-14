from rest_framework import serializers
from .models import CustomerImport, OnboardingSession, OnboardingStep


class SessionCreateSerializer(serializers.Serializer):
    visitor_id = serializers.CharField(max_length=100)


class ProfileSerializer(serializers.Serializer):
    company_name = serializers.CharField(max_length=120)
    business_type = serializers.CharField(max_length=80)


class CompleteStepSerializer(serializers.Serializer):
    step = serializers.ChoiceField(choices=[key for key, _ in OnboardingStep.STEP_CHOICES])
    metadata = serializers.JSONField(required=False, default=dict)


class IntegrationSerializer(serializers.Serializer):
    provider = serializers.CharField(max_length=80, default="demo-commerce")
    external_store_id = serializers.CharField(max_length=120, required=False, allow_blank=True)


class CampaignCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120)
    channel = serializers.ChoiceField(choices=["email", "sms", "push"], default="email")


class CustomerImportSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, value):
        if not value.name.lower().endswith(".csv"):
            raise serializers.ValidationError("Upload a .csv file.")
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("CSV must be 10 MB or smaller.")
        return value


class CopilotRequestSerializer(serializers.Serializer):
    goal = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")


class ImportStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerImport
        fields = [
            "id", "source_filename", "status", "total_rows", "imported_rows", "failed_rows",
            "error_message", "created_at", "finished_at",
        ]


class SessionSerializer(serializers.ModelSerializer):
    completed_steps = serializers.SerializerMethodField()
    progress_percent = serializers.SerializerMethodField()
    is_activated = serializers.SerializerMethodField()
    customer_count = serializers.SerializerMethodField()
    integration = serializers.SerializerMethodField()
    campaign_count = serializers.SerializerMethodField()

    class Meta:
        model = OnboardingSession
        fields = [
            "visitor_id", "company_name", "business_type", "variant", "completed_steps",
            "progress_percent", "is_activated", "customer_count", "integration",
            "campaign_count", "created_at", "activated_at",
        ]

    def get_completed_steps(self, obj):
        return list(obj.steps.order_by("completed_at").values_list("key", flat=True))

    def get_progress_percent(self, obj):
        completed = obj.steps.count()
        return round((completed / len(OnboardingStep.STEP_CHOICES)) * 100)

    def get_is_activated(self, obj):
        return obj.activated_at is not None

    def get_customer_count(self, obj):
        return obj.customers.count()

    def get_integration(self, obj):
        try:
            return {"provider": obj.integration.provider, "external_store_id": obj.integration.external_store_id}
        except Exception:
            return None

    def get_campaign_count(self, obj):
        return obj.campaigns.count()
