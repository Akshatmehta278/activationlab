from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from .models import Customer, OnboardingSession, OnboardingStep, ProductEvent
from .services import assign_variant, sample_ratio_mismatch, two_proportion_test


@override_settings(USE_CELERY=False, OPENAI_API_KEY="")
class ActivationLabTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.visitor_id = "test-visitor-123"
        self.client.post("/api/sessions/", {"visitor_id": self.visitor_id}, format="json")

    def test_variant_assignment_is_deterministic(self):
        self.assertEqual(assign_variant(self.visitor_id), assign_variant(self.visitor_id))

    def test_session_creation_tracks_signup_event(self):
        self.assertEqual(OnboardingSession.objects.count(), 1)
        self.assertEqual(ProductEvent.objects.filter(name="signup_completed").count(), 1)

    def test_specialized_onboarding_flow_activates(self):
        self.client.patch(
            f"/api/sessions/{self.visitor_id}/profile/",
            {"company_name": "Acme", "business_type": "Ecommerce"},
            format="json",
        )
        self.client.post(
            f"/api/sessions/{self.visitor_id}/integration/",
            {"provider": "shopify-demo"},
            format="json",
        )
        csv_file = SimpleUploadedFile(
            "customers.csv",
            b"customer_id,email,first_name,last_name,lifetime_value,subscribed,tags\n1,a@example.com,A,One,120.50,true,vip;repeat\n2,b@example.com,B,Two,25,false,new\n",
            content_type="text/csv",
        )
        response = self.client.post(
            f"/api/sessions/{self.visitor_id}/imports/",
            {"file": csv_file},
            format="multipart",
        )
        self.assertEqual(response.status_code, 202)
        self.assertEqual(Customer.objects.filter(session__visitor_id=self.visitor_id).count(), 2)

        self.client.post(
            f"/api/sessions/{self.visitor_id}/campaigns/",
            {"name": "Welcome Series", "channel": "email"},
            format="json",
        )
        session = OnboardingSession.objects.get(visitor_id=self.visitor_id)
        self.assertIsNotNone(session.activated_at)
        self.assertEqual(session.steps.count(), 4)
        self.assertEqual(ProductEvent.objects.filter(name="onboarding_completed").count(), 1)

    def test_duplicate_generic_step_is_idempotent(self):
        url = f"/api/sessions/{self.visitor_id}/steps/"
        payload = {"step": OnboardingStep.STEP_INTEGRATION, "metadata": {}}
        first = self.client.post(url, payload, format="json")
        second = self.client.post(url, payload, format="json")
        self.assertTrue(first.data["created"])
        self.assertFalse(second.data["created"])
        self.assertEqual(OnboardingStep.objects.filter(key=OnboardingStep.STEP_INTEGRATION).count(), 1)

    def test_metrics_include_experiment_statistics(self):
        response = self.client.get("/api/metrics/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("experiment", response.data)
        self.assertIn("p_value", response.data["experiment"])
        self.assertIn("sample_ratio_mismatch", response.data["experiment"])

    def test_copilot_works_without_external_ai_key(self):
        response = self.client.post(
            f"/api/sessions/{self.visitor_id}/copilot/",
            {"goal": "Get new merchants to first value quickly"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["provider"], "rules")
        self.assertTrue(response.data["recommendations"])

    def test_statistics_helpers(self):
        result = two_proportion_test(100, 40, 100, 55)
        self.assertGreater(result["difference_pp"], 0)
        srm = sample_ratio_mismatch(50, 50)
        self.assertFalse(srm["flagged"])

    def test_import_with_no_valid_identity_fails_without_completing_step(self):
        csv_file = SimpleUploadedFile(
            "invalid.csv",
            b"customer_id,email,first_name\n,,Nobody\n",
            content_type="text/csv",
        )
        response = self.client.post(
            f"/api/sessions/{self.visitor_id}/imports/",
            {"file": csv_file},
            format="multipart",
        )
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data["status"], "failed")
        self.assertFalse(
            OnboardingStep.objects.filter(
                session__visitor_id=self.visitor_id,
                key=OnboardingStep.STEP_IMPORT,
            ).exists()
        )
