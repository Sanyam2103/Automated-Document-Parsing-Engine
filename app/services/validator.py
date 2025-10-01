from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re
import logging
import datetime
from app.models.schemas import CompanyProfile, PastPerformance, PricingSheet,ValidationIssues

logger = logging.getLogger(__name__)

@dataclass
class ComplianceIssue:
    issue_id: str
    description: str
    evidence: str
    severity: str  # "blocking", "critical", "minor"
    rule_category: str  # Used for RAG retrieval


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
    

class HybridValidator:
    """Production-grade validator for GSA compliance analysis"""
    
    @staticmethod
    def validate_all_data(parsed_data: Dict[str, Any]) -> List[ComplianceIssue]:
        """Master validation function - comprehensive compliance checking"""
        issues = []
        
        logger.info("🔍 Starting comprehensive GSA compliance validation")
        
        try:
            # Validate company data (R1 & R2)
            company = parsed_data.get("company")
            if company:
                issues.extend(HybridValidator._validate_company_compliance(company))
            else:
                issues.append(ComplianceIssue(
                    issue_id="missing_company_profile",
                    description="Company profile document not provided",
                    evidence="No company data found in submission",
                    severity="blocking",
                    rule_category="identity_requirements"
                ))
            
            # Validate past performance (R3)
            past_performance = parsed_data.get("past_performance", [])
            issues.extend(HybridValidator._validate_past_performance_compliance(past_performance))
            
            # Validate pricing (R4)
            pricing = parsed_data.get("pricing")
            issues.extend(HybridValidator._validate_pricing_compliance(pricing))
            
            logger.info(f"✅ Validation complete: {len(issues)} compliance issues found")
            
        except Exception as e:
            logger.error(f"Error during validation: {e}")
            issues.append(ComplianceIssue(
                issue_id="validation_error",
                description="Internal validation error occurred",
                evidence=f"System error during validation: {str(e)}",
                severity="critical",
                rule_category="system_error"
            ))
        
        return issues
    
    @staticmethod
    def _validate_company_compliance(company_data: Dict[str, Any]) -> List[ComplianceIssue]:
        """R1 & R2 - Identity and NAICS validation"""
        issues = []
        
        # R1 - Identity Requirements
        # UEI validation
        uei = company_data.get("uei")
        if not uei:
            issues.append(ComplianceIssue(
                issue_id="missing_uei",
                description="UEI identifier not provided",
                evidence="UEI field is empty or missing",
                severity="blocking",
                rule_category="identity_requirements"
            ))
        elif len(str(uei).strip()) != 12:
            issues.append(ComplianceIssue(
                issue_id="invalid_uei_format",
                description="UEI format validation failed",
                evidence=f"UEI '{uei}' has {len(str(uei).strip())} characters, requires exactly 12",
                severity="blocking",
                rule_category="identity_requirements"
            ))
        
        # DUNS validation
        duns = company_data.get("duns")
        if not duns:
            issues.append(ComplianceIssue(
                issue_id="missing_duns",
                description="DUNS number not provided",
                evidence="DUNS field is empty or missing",
                severity="blocking",
                rule_category="identity_requirements"
            ))
        elif not re.match(r'^\d{9}$', str(duns).strip()):
            issues.append(ComplianceIssue(
                issue_id="invalid_duns_format",
                description="DUNS format validation failed",
                evidence=f"DUNS '{duns}' should be exactly 9 digits",
                severity="blocking",
                rule_category="identity_requirements"
            ))
        
        # SAM registration validation
        sam_status = company_data.get("sam_registered")
        if sam_status is None:
            issues.append(ComplianceIssue(
                issue_id="sam_status_unknown",
                description="SAM.gov registration status not provided",
                evidence="SAM registration status missing",
                severity="critical",
                rule_category="identity_requirements"
            ))
        elif sam_status != True and str(sam_status).lower() != "registered":
            issues.append(ComplianceIssue(
                issue_id="sam_not_registered",
                description="SAM.gov registration not active",
                evidence=f"SAM status: '{sam_status}', required: 'registered'",
                severity="blocking",
                rule_category="identity_requirements"
            ))
        
        # Contact information validation
        if not company_data.get("poc_email"):
            issues.append(ComplianceIssue(
                issue_id="missing_poc_email",
                description="Primary contact email missing",
                evidence="Point of contact email not provided",
                severity="critical",
                rule_category="identity_requirements"
            ))
        
        if not company_data.get("poc_phone"):
            issues.append(ComplianceIssue(
                issue_id="missing_poc_phone", 
                description="Primary contact phone missing",
                evidence="Point of contact phone not provided",
                severity="critical",
                rule_category="identity_requirements"
            ))
        
        # Company name validation
        if not company_data.get("company_name"):
            issues.append(ComplianceIssue(
                issue_id="missing_company_name",
                description="Company name not provided",
                evidence="Legal company name missing",
                severity="blocking",
                rule_category="identity_requirements"
            ))
        
        # R2 - NAICS validation
        naics = company_data.get("naics", [])
        if not naics or len(naics) == 0:
            issues.append(ComplianceIssue(
                issue_id="missing_naics",
                description="NAICS codes not provided",
                evidence="No NAICS codes found",
                severity="critical",
                rule_category="naics_requirements"
            ))
        else:
            for i, naics_code in enumerate(naics):
                if not re.match(r'^\d{6}$', str(naics_code).strip()):
                    issues.append(ComplianceIssue(
                        issue_id="invalid_naics_format",
                        description="NAICS code format invalid",
                        evidence=f"NAICS code '{naics_code}' should be exactly 6 digits",
                        severity="critical",
                        rule_category="naics_requirements"
                    ))
        
        return issues
    
    @staticmethod
    def _period_within_last_36_months(period_str):
    # Example: "07/2023 - 03/2024" or "Jan 2022 - Jul 2024"

        now = datetime.datetime.now()
        # Attempt to extract end date
        matches = re.findall(r'(\d{2}/\d{4})|(\w{3,9} \d{4})', period_str)
        end_date = None
        for m in matches[::-1]:  # last found date has priority
            date_str = ''.join(m)
            try:
                end_date = datetime.datetime.strptime(date_str, "%m/%Y")
            except Exception:
                try:
                    end_date = datetime.datetime.strptime(date_str, "%b %Y")
                except Exception:
                    try:
                        end_date = datetime.datetime.strptime(date_str, "%B %Y")
                    except Exception:
                        continue
            if end_date:
                break
        if not end_date:
            return False  # can't parse end date, fail safe
        # 36 months ago from now
        threshold = now - datetime.timedelta(days=36*30)
        return end_date >= threshold

    @staticmethod
    def _validate_past_performance_compliance(past_performance: List[Dict]) -> List[ComplianceIssue]:
        """R3 - Past Performance validation"""
        issues = []
        
        if not past_performance or len(past_performance) == 0:
            issues.append(ComplianceIssue(
                issue_id="no_past_performance",
                description="No past performance records provided",
                evidence="Past performance section is empty",
                severity="blocking",
                rule_category="past_performance_requirements"
            ))
            return issues
        
        # Check for qualifying contracts ($25K+ threshold)
        qualifying_contracts = 0
        
        for i, pp in enumerate(past_performance):
            # Contract value validation
            contract_value = pp.get("contract_value", "0")
            numeric_value = HybridValidator._extract_numeric_value(contract_value)
            period = pp.get("period", "")
            is_recent = HybridValidator._period_within_last_36_months(period)
            if numeric_value >= 25000 and is_recent:
                qualifying_contracts += 1
            
            # Customer information validation
            if not pp.get("customer"):
                issues.append(ComplianceIssue(
                    issue_id="missing_customer_info",
                    description="Customer information missing from past performance",
                    evidence=f"Contract {i+1} missing customer name/organization",
                    severity="critical",
                    rule_category="past_performance_requirements"
                ))
            
            # Contract period validation
            if not pp.get("period"):
                issues.append(ComplianceIssue(
                    issue_id="missing_contract_period",
                    description="Contract period missing from past performance",
                    evidence=f"Contract {i+1} missing time period/duration",
                    severity="critical",
                    rule_category="past_performance_requirements"
                ))
            
            # Contact verification
            if not pp.get("contact_email") or not pp.get("contact_name"):
                issues.append(ComplianceIssue(
                    issue_id="missing_contact_verification",
                    description="Customer contact information missing",
                    evidence=f"Contract {i+1} missing customer contact for verification",
                    severity="minor",
                    rule_category="past_performance_requirements"
                ))
        
        # Overall qualification assessment
        if qualifying_contracts == 0:
            issues.append(ComplianceIssue(
                issue_id="no_qualifying_contracts",
                description="No contracts meet minimum value requirement",
                evidence=f"All {len(past_performance)} contracts below $25,000 threshold",
                severity="blocking",
                rule_category="past_performance_requirements"
            ))
        
        return issues
    
    @staticmethod
    def _validate_pricing_compliance(pricing_data: Optional[Dict]) -> List[ComplianceIssue]:
        """R4 - Pricing and catalog validation"""
        issues = []
        
        if not pricing_data:
            issues.append(ComplianceIssue(
                issue_id="missing_pricing_sheet",
                description="Pricing information not provided",
                evidence="No pricing sheet or catalog found",
                severity="blocking",
                rule_category="pricing_requirements"
            ))
            return issues
        
        labor_categories = pricing_data.get("labor_categories", [])
        if not labor_categories or len(labor_categories) == 0:
            issues.append(ComplianceIssue(
                issue_id="missing_labor_categories",
                description="Labor categories not defined",
                evidence="Pricing sheet contains no labor categories",
                severity="blocking",
                rule_category="pricing_requirements"
            ))
            return issues
        
        # Validate each labor category
        for i, category in enumerate(labor_categories):
            if not category.get("category"):
                issues.append(ComplianceIssue(
                    issue_id="missing_category_name",
                    description="Labor category name missing",
                    evidence=f"Labor category {i+1} has no name/description",
                    severity="critical",
                    rule_category="pricing_requirements"
                ))
            
            if not category.get("rate"):
                issues.append(ComplianceIssue(
                    issue_id="missing_hourly_rate",
                    description="Labor category hourly rate missing",
                    evidence=f"Category '{category.get('category', 'unnamed')}' missing rate",
                    severity="critical",
                    rule_category="pricing_requirements"
                ))
            
            if not category.get("unit"):
                issues.append(ComplianceIssue(
                    issue_id="missing_rate_unit",
                    description="Rate unit specification missing",
                    evidence=f"Category '{category.get('category', 'unnamed')}' missing unit (hour/day/etc.)",
                    severity="critical",
                    rule_category="pricing_requirements"
                ))
        
        return issues
    
    @staticmethod
    def _extract_numeric_value(value_str: str) -> int:
        """Extract numeric value from currency strings"""
        if not value_str:
            return 0
        
        # Remove currency symbols and commas
        cleaned = str(value_str).replace('$', '').replace(',', '').strip()
        
        # Find numeric sequences
        numbers = re.findall(r'\d+', cleaned)
        if numbers:
            try:
                return int(numbers[0])
            except (ValueError, IndexError):
                return 0
        return 0
