import pytest
from app.services.validator import HybridValidator
from app.services.redactor import PIIRedactor
from app.services.rag import GSARulesRAG
from app.services.mapper import NaicsSinMapper
from app.models.schemas import CompanyProfile, PastPerformance, PricingSheet

def test_missing_uei_flagged():
    company = {
        "company_name": "TestCo",
        "uei": None,
        "duns": "123456789",
        "naics": ["541511"],
        "poc_email": "test@example.com",
        "poc_phone": "555-123-4567",
        "address": "123 Main St",
        "sam_registered": True
    }
    parsed = {"company": company, "past_performance": [], "pricing": None}
    issues = HybridValidator.validate_all_data(parsed)
    assert any(i.issue_id == "missing_uei" for i in issues)

def test_past_performance_min_value():
    pp = {
        "customer": "Agency",
        "contract_description": "Dev",
        "contract_value": "$18,000",
        "period": "01/2023 - 12/2023",
        "contact_name": "John",
        "contact_email": "john@agency.com"
    }
    company = {
        "company_name": "TestCo",
        "uei": "A" * 12,
        "duns": "123456789",
        "naics": ["541511"],
        "poc_email": "test@example.com",
        "poc_phone": "555-123-4567",
        "address": "123 Main St",
        "sam_registered": True
    }
    parsed = {"company": company, "past_performance": [pp], "pricing": None}
    issues = HybridValidator.validate_all_data(parsed)
    assert any("no_qualifying_contracts" in i.issue_id or "min_value" in i.issue_id for i in issues)

def test_naics_sin_mapping_dedupe():
    naics = ["541511", "541512", "541611", "518210", "541511"]
    sins = NaicsSinMapper.get_recommended_sins(naics)
    assert set(sins) == {"54151S", "541611", "518210C"}

def test_pii_redaction_masks():
    profile = CompanyProfile(
        company_name="TestCo",
        uei="A"*12,
        duns="123456789",
        naics=["541511"],
        poc_name="Jane",
        poc_email="jane@acme.com",
        poc_phone="555-123-4567",
        address="123 Main St",
        sam_registered=True
    )
    redacted, pii_hashes = PIIRedactor.redact_and_hash_companyprofile(profile)
    assert redacted.poc_email is not None and "[EMAIL_HASH_" in redacted.poc_email
    assert redacted.poc_phone is not None and "[PHONE_HASH_" in redacted.poc_phone
    assert len(pii_hashes["emails"]) == 1
    assert len(pii_hashes["phones"]) == 1

def test_rag_rule_citation_abstain(monkeypatch):
    # Remove R1 from the rules index and check that R1 is not cited
    rag = GSARulesRAG(1)
    # Remove R1
    rag.rules_documents = [doc for doc in rag.rules_documents if doc.metadata.get("rule_id") != "R1"]
    rag._initialize_vectorstore()
    parsed = {
        "company": {
            "company_name": "TestCo",
            "uei": None,
            "duns": "123456789",
            "naics": ["541511"],
            "poc_email": "test@example.com",
            "poc_phone": "555-123-4567",
            "address": "123 Main St",
            "sam_registered": True
        },
        "past_performance": [],
        "pricing": None
    }
    checklist = rag.build_policy_checklist(parsed)
    # Should not cite R1
    assert all(c.get("rule_id") != "R1" for c in checklist.get("citations", []))
