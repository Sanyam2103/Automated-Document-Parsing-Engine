import pytest
from app.services.parser import DocumentParser
from app.services.validator import FieldValidator
from app.models.schemas import CompanyProfile
from app.services.mapper import NaicsSinMapper

def test_missing_uei():
    sample = """TestCorp
    DUNS: 123456789
    NAICS: 541511
    POC: John Test, john@example.com, 123-4567
    Address: 1 Road
    SAM.gov: registered
    """
    company = DocumentParser.parse_company_profile(sample)
    issues = FieldValidator.validate_company(company)
    assert issues.missing_uei is True

def test_invalid_email():
    sample = """TestCorp
    UEI: 123ABC
    DUNS: 123456789
    NAICS: 541511
    POC: John Test, _email, 123-4567
    Address: 1 Road
    SAM.gov: registered
    """
    company = DocumentParser.parse_company_profile(sample)
    issues = FieldValidator.validate_company(company)
    assert issues.invalid_poc_email is True

def test_naics_to_sin_mapping():
    naics_list = ["541511", "541512", "541611", "000000"]
    sins = NaicsSinMapper.get_recommended_sins(naics_list)
    assert "54151S" in sins
    assert "541611" in sins
    # unmapped NAICS should not yield a SIN
    assert "000000" not in sins
