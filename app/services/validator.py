from app.models.schemas import CompanyProfile, ValidationIssues, PastPerformance

class FieldValidator:
    REQUIRED_FIELDS = ["company_name", "uei", "duns", "naics", "poc_email", "address", "sam_registered"]

    @staticmethod
    def validate_company(company: CompanyProfile) -> ValidationIssues:
        issues = ValidationIssues()
        # Check for missing fields
        issues.missing_uei = not company.uei
        issues.missing_naics = not (company.naics and any(company.naics))
        issues.missing_company_name = not company.company_name
        # print("DEBUG missing_company_name:", issues.missing_company_name, "company_name:", company.company_name)  # Add this line for debugging
        issues.missing_sam_status = company.sam_registered is None
        # Bad email
        issues.invalid_poc_email = not company.poc_email or "@" not in (company.poc_email or "")
        return issues

    @staticmethod
    def validate_past_performance(perf: PastPerformance) -> bool:
        # Example: requires at least a customer and contract description
        return bool(perf.customer and perf.contract_description)
