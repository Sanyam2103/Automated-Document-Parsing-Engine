from app.models.schemas import Checklist, CompanyProfile, PastPerformance, ValidationIssues

def build_checklist(company: CompanyProfile, past_perf: list, issues: ValidationIssues) -> Checklist:
    return Checklist(
        required_fields_complete=not (issues.missing_company_name or issues.missing_uei or issues.missing_naics or issues.missing_sam_status),
        valid_contact_info=not issues.invalid_poc_email,
        sam_registered=company.sam_registered is True,
        has_past_performance=any((p.customer or p.contract_description) for p in past_perf),
    )
