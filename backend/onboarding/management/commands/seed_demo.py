import random
from datetime import timedelta
from django.core.management.base import BaseCommand

from onboarding.models import Customer, OnboardingSession, OnboardingStep
from onboarding.services import assign_variant, complete_step, connect_integration, create_campaign, track_event


class Command(BaseCommand):
    help = "Seed deterministic demo experiment sessions for the analytics dashboard."

    def add_arguments(self, parser):
        parser.add_argument("--sessions", type=int, default=120)
        parser.add_argument("--reset", action="store_true")

    def handle(self, *args, **options):
        random.seed(42)
        count = max(10, options["sessions"])
        if options["reset"]:
            OnboardingSession.objects.filter(visitor_id__startswith="demo-").delete()

        created_count = 0
        for i in range(count):
            visitor_id = f"demo-{i:04d}"
            variant = assign_variant(visitor_id)
            session, created = OnboardingSession.objects.get_or_create(
                visitor_id=visitor_id,
                defaults={
                    "variant": variant,
                    "company_name": f"Demo Store {i + 1}",
                    "business_type": "Ecommerce",
                },
            )
            if not created:
                continue
            created_count += 1
            track_event(session, "signup_completed", {"variant": variant, "seeded": True})
            complete_step(session, OnboardingStep.STEP_WORKSPACE, {"seeded": True})

            # Guided users intentionally have a somewhat healthier demo funnel.
            rates = (
                {"integration": 0.90, "import": 0.77, "campaign": 0.64}
                if variant == OnboardingSession.VARIANT_GUIDED
                else {"integration": 0.84, "import": 0.67, "campaign": 0.50}
            )
            if random.random() < rates["integration"]:
                connect_integration(session, "shopify-demo", f"store-{i}")
            else:
                continue

            if random.random() < rates["import"]:
                for j in range(random.randint(3, 8)):
                    Customer.objects.create(
                        session=session,
                        external_id=f"{visitor_id}-c{j}",
                        email=f"customer{j}@demo{i}.example",
                        first_name=f"Customer{j}",
                        lifetime_value=random.randint(10, 600),
                        subscribed=random.random() > 0.1,
                        tags=["seeded", "demo"],
                    )
                complete_step(session, OnboardingStep.STEP_IMPORT, {"seeded": True, "rows": session.customers.count()})
            else:
                continue

            if random.random() < rates["campaign"]:
                create_campaign(session, "Welcome Series", "email")
                # Spread seeded activation timestamps for a realistic dashboard.
                session.refresh_from_db()
                if session.activated_at:
                    session.activated_at = session.created_at + timedelta(minutes=random.randint(2, 35))
                    session.save(update_fields=["activated_at"])

        self.stdout.write(self.style.SUCCESS(f"Seeded {created_count} new demo sessions."))
