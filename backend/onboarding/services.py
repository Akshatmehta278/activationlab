import csv
import hashlib
import io
import json
import math
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import (
    Campaign,
    CopilotInteraction,
    Customer,
    CustomerImport,
    Integration,
    OnboardingSession,
    OnboardingStep,
    ProductEvent,
)


def assign_variant(visitor_id: str) -> str:
    """Deterministic 50/50 assignment keeps a visitor in one experiment variant."""
    digest = hashlib.sha256(visitor_id.encode("utf-8")).hexdigest()
    bucket = int(digest[:8], 16) % 2
    return OnboardingSession.VARIANT_CONTROL if bucket == 0 else OnboardingSession.VARIANT_GUIDED


def track_event(session: OnboardingSession, name: str, metadata=None):
    return ProductEvent.objects.create(session=session, name=name, metadata=metadata or {})


@transaction.atomic
def complete_step(session: OnboardingSession, step_key: str, metadata=None):
    step, created = OnboardingStep.objects.get_or_create(session=session, key=step_key)
    if created:
        track_event(session, step_key, metadata)

    required = {key for key, _ in OnboardingStep.STEP_CHOICES}
    completed = set(session.steps.values_list("key", flat=True))
    if required.issubset(completed) and session.activated_at is None:
        session.activated_at = timezone.now()
        session.save(update_fields=["activated_at"])
        track_event(
            session,
            "onboarding_completed",
            {
                "variant": session.variant,
                "time_to_activation_seconds": round((session.activated_at - session.created_at).total_seconds()),
            },
        )
    return step, created


def connect_integration(session: OnboardingSession, provider: str, external_store_id: str = ""):
    integration, _ = Integration.objects.update_or_create(
        session=session,
        defaults={"provider": provider, "external_store_id": external_store_id},
    )
    complete_step(session, OnboardingStep.STEP_INTEGRATION, {"provider": provider})
    return integration


def create_campaign(session: OnboardingSession, name: str, channel: str = "email"):
    campaign = Campaign.objects.create(session=session, name=name, channel=channel, status=Campaign.STATUS_DRAFT)
    complete_step(session, OnboardingStep.STEP_CAMPAIGN, {"campaign_id": campaign.id, "channel": channel})
    return campaign


def _as_decimal(value):
    try:
        return Decimal(str(value or "0").strip() or "0")
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _as_bool(value):
    return str(value).strip().lower() not in {"0", "false", "no", "n", "unsubscribed"}


def process_customer_import(import_id: int):
    job = CustomerImport.objects.select_related("session").get(id=import_id)
    job.status = CustomerImport.STATUS_PROCESSING
    job.error_message = ""
    job.save(update_fields=["status", "error_message"])

    total = imported = failed = 0
    try:
        job.file.open("rb")
        raw = job.file.read()
        text = raw.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        if not reader.fieldnames:
            raise ValueError("CSV requires a header row.")

        for row_number, row in enumerate(reader, start=2):
            total += 1
            external_id = (row.get("customer_id") or row.get("external_id") or row.get("email") or "").strip()
            if not external_id:
                failed += 1
                continue
            email = (row.get("email") or "").strip()
            tags = [tag.strip() for tag in (row.get("tags") or "").split(";") if tag.strip()]
            try:
                Customer.objects.update_or_create(
                    session=job.session,
                    external_id=external_id,
                    defaults={
                        "email": email,
                        "first_name": (row.get("first_name") or "").strip(),
                        "last_name": (row.get("last_name") or "").strip(),
                        "lifetime_value": _as_decimal(row.get("lifetime_value")),
                        "subscribed": _as_bool(row.get("subscribed", "true")),
                        "tags": tags,
                    },
                )
                imported += 1
            except Exception:
                failed += 1

        if imported == 0:
            raise ValueError("No valid customer rows were imported.")

        job.total_rows = total
        job.imported_rows = imported
        job.failed_rows = failed
        job.status = CustomerImport.STATUS_COMPLETED
        job.finished_at = timezone.now()
        job.save(update_fields=["total_rows", "imported_rows", "failed_rows", "status", "finished_at"])
        complete_step(
            job.session,
            OnboardingStep.STEP_IMPORT,
            {"import_id": job.id, "imported_rows": imported, "failed_rows": failed},
        )
        track_event(job.session, "customer_import_completed", {"import_id": job.id, "rows": imported})
    except Exception as exc:
        job.total_rows = total
        job.imported_rows = imported
        job.failed_rows = failed
        job.status = CustomerImport.STATUS_FAILED
        job.error_message = str(exc)[:2000]
        job.finished_at = timezone.now()
        job.save(update_fields=["total_rows", "imported_rows", "failed_rows", "status", "error_message", "finished_at"])
        track_event(job.session, "customer_import_failed", {"import_id": job.id, "error": str(exc)[:250]})
    finally:
        try:
            job.file.close()
        except Exception:
            pass
    return job


def two_proportion_test(control_total, control_converted, guided_total, guided_converted):
    if not control_total or not guided_total:
        return {
            "difference_pp": 0.0,
            "relative_uplift_percent": 0.0,
            "z_score": 0.0,
            "p_value": 1.0,
            "significant_at_95": False,
            "ci_95_difference_pp": [0.0, 0.0],
        }

    p1 = control_converted / control_total
    p2 = guided_converted / guided_total
    difference = p2 - p1
    pooled = (control_converted + guided_converted) / (control_total + guided_total)
    se_pooled = math.sqrt(max(pooled * (1 - pooled) * (1 / control_total + 1 / guided_total), 0))
    z = difference / se_pooled if se_pooled else 0.0
    p_value = math.erfc(abs(z) / math.sqrt(2)) if se_pooled else 1.0

    se_unpooled = math.sqrt(
        max((p1 * (1 - p1) / control_total) + (p2 * (1 - p2) / guided_total), 0)
    )
    lower = difference - 1.96 * se_unpooled
    upper = difference + 1.96 * se_unpooled
    relative = (difference / p1 * 100) if p1 else 0.0
    return {
        "difference_pp": round(difference * 100, 2),
        "relative_uplift_percent": round(relative, 2),
        "z_score": round(z, 3),
        "p_value": round(p_value, 5),
        "significant_at_95": p_value < 0.05,
        "ci_95_difference_pp": [round(lower * 100, 2), round(upper * 100, 2)],
    }


def sample_ratio_mismatch(control_total: int, guided_total: int):
    total = control_total + guided_total
    if total == 0:
        return {"chi_square": 0.0, "p_value": 1.0, "flagged": False}
    expected = total / 2
    chi_square = ((control_total - expected) ** 2 / expected) + ((guided_total - expected) ** 2 / expected)
    p_value = math.erfc(math.sqrt(chi_square / 2))
    return {
        "chi_square": round(chi_square, 3),
        "p_value": round(p_value, 5),
        "flagged": p_value < 0.01,
    }


def _rule_recommendations(session: OnboardingSession, user_goal: str = ""):
    completed = set(session.steps.values_list("key", flat=True))
    recs = []
    if OnboardingStep.STEP_WORKSPACE not in completed:
        recs.append({"title": "Create your workspace", "reason": "The system needs business context before it can personalize setup.", "action": "workspace_created", "risk": "low"})
    elif OnboardingStep.STEP_INTEGRATION not in completed:
        recs.append({"title": "Connect your customer-data source", "reason": "An integration unlocks behavioral events and customer profiles.", "action": "integration_connected", "risk": "low"})
    elif OnboardingStep.STEP_IMPORT not in completed:
        recs.append({"title": "Import a customer sample", "reason": "A small verified import is safer than starting with the full production dataset.", "action": "data_imported", "risk": "medium"})
    elif OnboardingStep.STEP_CAMPAIGN not in completed:
        recs.append({"title": "Create a welcome campaign draft", "reason": "A draft proves the end-to-end value path without sending customer messages.", "action": "campaign_created", "risk": "medium"})
    else:
        recs.append({"title": "Review experiment performance", "reason": "Your activation path is complete; compare conversion and guardrails before changing the experience.", "action": "view_metrics", "risk": "low"})

    if session.business_type.lower() == "ecommerce":
        recs.append({"title": "Prioritize purchase and cart events", "reason": "Commerce journeys benefit from purchase, cart, and product-view signals.", "action": "event_plan", "risk": "low"})
    if user_goal:
        recs.append({"title": "Keep the goal measurable", "reason": f"Translate your goal into one observable activation metric before shipping: {user_goal[:120]}", "action": "define_metric", "risk": "low"})
    return recs[:3]


def get_copilot_recommendations(session: OnboardingSession, user_goal: str = ""):
    """Uses OpenAI only when a server-side API key exists; otherwise falls back to explainable local rules."""
    provider = "rules"
    recommendations = _rule_recommendations(session, user_goal)

    if getattr(settings, "OPENAI_API_KEY", "") and getattr(settings, "OPENAI_MODEL", ""):
        try:
            from openai import OpenAI

            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            state = {
                "business_type": session.business_type or "unknown",
                "variant": session.variant,
                "completed_steps": list(session.steps.values_list("key", flat=True)),
                "user_goal": user_goal[:500],
            }
            response = client.responses.create(
                model=settings.OPENAI_MODEL,
                store=False,
                instructions=(
                    "You are a SaaS onboarding copilot. Return ONLY a JSON array of 1-3 objects. "
                    "Each object must have title, reason, action, and risk. Do not request secrets, "
                    "do not recommend destructive actions, and never claim an action was performed."
                ),
                input=json.dumps(state),
            )
            parsed = json.loads(response.output_text)
            if isinstance(parsed, list) and parsed:
                recommendations = parsed[:3]
                provider = "openai"
        except Exception:
            provider = "rules_fallback"

    payload = {"provider": provider, "recommendations": recommendations}
    CopilotInteraction.objects.create(
        session=session,
        provider=provider,
        user_goal=user_goal[:1000],
        response=payload,
    )
    return payload
