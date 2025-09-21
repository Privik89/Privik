from fastapi import APIRouter

from .routers import ingest, click, soc, zero_trust, email_gateway, integrations, sandbox, ui_sandbox, ui_integrations, ui_artifacts, ui_policies, ui_soc, domain_lists, ui_domain_lists, domain_reputation, ui_domain_reputation, bulk_domains, ui_bulk_domains, threat_feeds, ui_threat_feeds, quarantine, ui_quarantine, incident_correlation, ui_incident_correlation, performance, ui_performance, ai_ml, ui_ai_ml, dashboard, test_api


api_router = APIRouter()
api_router.include_router(ingest.router)
api_router.include_router(click.router)
api_router.include_router(soc.router)
api_router.include_router(zero_trust.router)
api_router.include_router(email_gateway.router)
api_router.include_router(integrations.router)
api_router.include_router(sandbox.router)
api_router.include_router(ui_sandbox.router)
api_router.include_router(ui_integrations.router)
api_router.include_router(ui_artifacts.router)
api_router.include_router(ui_policies.router)
api_router.include_router(ui_soc.router)
api_router.include_router(domain_lists.router)
api_router.include_router(ui_domain_lists.router)
api_router.include_router(domain_reputation.router)
api_router.include_router(ui_domain_reputation.router)
api_router.include_router(bulk_domains.router)
api_router.include_router(ui_bulk_domains.router)
api_router.include_router(threat_feeds.router)
api_router.include_router(ui_threat_feeds.router)
api_router.include_router(quarantine.router)
api_router.include_router(ui_quarantine.router)
api_router.include_router(incident_correlation.router)
api_router.include_router(ui_incident_correlation.router)
api_router.include_router(performance.router)
api_router.include_router(ui_performance.router)
api_router.include_router(ai_ml.router)
api_router.include_router(ui_ai_ml.router)
api_router.include_router(dashboard.router)
api_router.include_router(test_api.router)


