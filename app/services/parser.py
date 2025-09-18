import re
from typing import List
from app.models.schemas import CompanyProfile, PastPerformance

class DocumentParser:
    @staticmethod
    def parse_company_profile(text: str) -> CompanyProfile:
        # Collapse all whitespace into space
        squeezed = " ".join(text.split())

        # Extract company name before "UEI:" if present, else None
        uei_index = squeezed.find("UEI:")
        if uei_index > 0:
            name = squeezed[:uei_index].strip()
        else:
            name = None

        uei = DocumentParser._search_between(squeezed, "UEI:", "DUNS:")
        duns = DocumentParser._search_between(squeezed, "DUNS:", "NAICS:")
        naics_str = DocumentParser._search_between(squeezed, "NAICS:", "POC:")
        naics = [x.strip() for x in naics_str.split(",")] if naics_str else []

        poc_name = DocumentParser._search_between(squeezed, "POC:", ",")
        poc_email = DocumentParser._search_between(squeezed, f"POC: {poc_name},", ",") if poc_name else None
        poc_phone = DocumentParser._search_between(squeezed, f"POC: {poc_name}, {poc_email},", "Address:") if poc_name and poc_email else None

        address = DocumentParser._search_between(squeezed, "Address:", "SAM.gov:")
        sam_status = DocumentParser._search_between(squeezed, "SAM.gov:", None)
        sam_registered = sam_status.lower() == "registered" if sam_status else None

        return CompanyProfile(
            company_name=name,
            uei=uei,
            duns=duns,
            naics=naics,
            poc_name=poc_name,
            poc_email=poc_email,
            poc_phone=poc_phone,
            address=address,
            sam_registered=sam_registered,
        )
    
    @staticmethod
    def parse_past_performance(text: str) -> List[PastPerformance]:
        # Collapse all whitespace into a single space
        squeezed = " ".join(text.split())

        customer = DocumentParser._search_between(squeezed, "Customer:", "Contract:")
        contract = DocumentParser._search_between(squeezed, "Contract:", "Value:")
        value = DocumentParser._search_between(squeezed, "Value:", "Period:")
        period = DocumentParser._search_between(squeezed, "Period:", "Contact:")
        # Now parse contact name/email after "Contact:"
        contact_match = re.search(r'Contact:\s*([^,]+),\s*([^\s]+)', squeezed)
        contact_name = contact_match.group(1).strip() if contact_match else None
        contact_email = contact_match.group(2).strip() if contact_match else None

        return [
            PastPerformance(
                customer=customer,
                contract_description=contract,
                contract_value=value,
                period=period,
                contact_name=contact_name,
                contact_email=contact_email,
            )
        ]

    @staticmethod
    def _search_between(text, start, end):
        if end:
            pattern = re.escape(start) + r'\s*(.*?)\s*' + re.escape(end)
        else:
            pattern = re.escape(start) + r'\s*(.*)'
        m = re.search(pattern, text, re.IGNORECASE)
        return m.group(1).strip() if m else None
    
    @staticmethod
    def _search_field(text, pattern):
        m = re.search(pattern, text)
        return m.group(1).strip() if m else None
