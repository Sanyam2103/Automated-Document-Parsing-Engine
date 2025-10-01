# import re
# from typing import List,Optional
# from app.models.schemas import CompanyProfile, PastPerformance,PricingSheet

# class DocumentParser:
#     @staticmethod
#     def parse_company_profile(text: str) -> CompanyProfile:
#         # Collapse all whitespace into space
#         squeezed = " ".join(text.split())

#         # Extract company name before "UEI:" if present, else None
#         uei_index = squeezed.find("UEI:")
#         if uei_index > 0:
#             name = squeezed[:uei_index].strip()
#         else:
#             name = None

#         uei = DocumentParser._search_between(squeezed, "UEI:", "DUNS:")
#         duns = DocumentParser._search_between(squeezed, "DUNS:", "NAICS:")
#         naics_str = DocumentParser._search_between(squeezed, "NAICS:", "POC:")
#         naics = [x.strip() for x in naics_str.split(",")] if naics_str else []

#         poc_name = DocumentParser._search_between(squeezed, "POC:", ",")
#         poc_email = DocumentParser._search_between(squeezed, f"POC: {poc_name},", ",") if poc_name else None
#         poc_phone = DocumentParser._search_between(squeezed, f"POC: {poc_name}, {poc_email},", "Address:") if poc_name and poc_email else None

#         address = DocumentParser._search_between(squeezed, "Address:", "SAM.gov:")
#         sam_status = DocumentParser._search_between(squeezed, "SAM.gov:", None)
#         sam_registered = sam_status.lower() == "registered" if sam_status else None

#         return CompanyProfile(
#             company_name=name,
#             uei=uei,
#             duns=duns,
#             naics=naics,
#             poc_name=poc_name,
#             poc_email=poc_email,
#             poc_phone=poc_phone,
#             address=address,
#             sam_registered=sam_registered,
#         )
    
#     @staticmethod
#     def parse_past_performance(text: str) -> List[PastPerformance]:
#         # Collapse all whitespace into a single space
#         squeezed = " ".join(text.split())

#         customer = DocumentParser._search_between(squeezed, "Customer:", "Contract:")
#         contract = DocumentParser._search_between(squeezed, "Contract:", "Value:")
#         value = DocumentParser._search_between(squeezed, "Value:", "Period:")
#         period = DocumentParser._search_between(squeezed, "Period:", "Contact:")
#         # Now parse contact name/email after "Contact:"
#         contact_match = re.search(r'Contact:\s*([^,]+),\s*([^\s]+)', squeezed)
#         contact_name = contact_match.group(1).strip() if contact_match else None
#         contact_email = contact_match.group(2).strip() if contact_match else None

#         return [
#             PastPerformance(
#                 customer=customer,
#                 contract_description=contract,
#                 contract_value=value,
#                 period=period,
#                 contact_name=contact_name,
#                 contact_email=contact_email,
#             )
#         ]

#     @staticmethod
#     def _search_between(text, start, end):
#         if end:
#             pattern = re.escape(start) + r'\s*(.*?)\s*' + re.escape(end)
#         else:
#             pattern = re.escape(start) + r'\s*(.*)'
#         m = re.search(pattern, text, re.IGNORECASE)
#         return m.group(1).strip() if m else None
    
#     @staticmethod
#     def _search_field(text, pattern):
#         m = re.search(pattern, text)
#         return m.group(1).strip() if m else None
    
#         # ADD this to your existing DocumentParser class
#     @staticmethod
#     def parse_pricing_sheet(text: str) -> PricingSheet:
#         """Parse pricing sheet text into structured data"""
#         labor_categories = []
        
#         lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
#         for line in lines:
#             # Skip header line
#             if "Labor Category" in line or "Rate" in line:
#                 continue
                
#             # Parse: "Senior Developer, 185, Hour"
#             parts = [p.strip() for p in line.split(",")]
#             if len(parts) >= 3:
#                 try:
#                     rate = float(parts[1]) if parts[1].replace('.','').isdigit() else None
#                     labor_categories.append({
#                         "category": parts[0],
#                         "rate": rate,
#                         "unit": parts[2]
#                     })
#                 except (ValueError, IndexError):
#                     continue
        
#         return PricingSheet(labor_categories=labor_categories)

#     @staticmethod
#     def classify_document(text: str, type_hint: Optional[str] = None) -> str:
#         """Simple document classification"""
#         if type_hint in ["profile", "past_performance", "pricing"]:
#             return type_hint
        
#         text_lower = text.lower()
#         if any(term in text_lower for term in ["labor category", "rate", "hour", "pricing"]):
#             return "pricing"
#         elif any(term in text_lower for term in ["customer:", "contract:", "value:", "period:"]):
#             return "past_performance"  
#         elif any(term in text_lower for term in ["uei:", "duns:", "naics:", "sam.gov"]):
#             return "profile"
#         else:
#             return "unknown"

import re
import logging
from typing import List, Optional, Dict, Any
from app.models.schemas import CompanyProfile, PastPerformance, PricingSheet

logger = logging.getLogger(__name__)

class DocumentParser:
    
    @staticmethod
    def parse_company_profile(text: str) -> CompanyProfile:
        """Enhanced parser with better error handling and logging"""
        logger.info(f"Parsing company profile from: {text[:100]}...")
        
        # Collapse all whitespace into space
        squeezed = " ".join(text.split())
        logger.debug(f"Squeezed text: {squeezed}")

        # Extract company name - improved logic
        name = DocumentParser._extract_company_name(squeezed)
        
        # Extract fields using improved search
        uei = DocumentParser._search_between(squeezed, "UEI:", ["DUNS:", "NAICS:", "POC:"])
        duns = DocumentParser._search_between(squeezed, "DUNS:", ["NAICS:", "POC:", "Address:"])
        naics_str = DocumentParser._search_between(squeezed, "NAICS:", ["POC:", "Address:", "SAM.gov:"])
        naics = [x.strip() for x in naics_str.split(",")] if naics_str else []

        # Enhanced POC extraction
        poc_info = DocumentParser._extract_poc_info(squeezed)
        
        # Extract address and SAM status
        address = DocumentParser._search_between(squeezed, "Address:", ["SAM.gov:"])
        sam_status = DocumentParser._search_between(squeezed, "SAM.gov:", [])

        sam_registered = sam_status.lower() == "registered" if sam_status else None

        # Log extracted values for debugging
        logger.info(f"Extracted: name={name}, uei={uei}, duns={duns}, naics={naics}")
        logger.info(f"POC: {poc_info.get('name')}, {poc_info.get('email')}, {poc_info.get('phone')}")

        return CompanyProfile(
            company_name=name,
            uei=uei,
            duns=duns,
            naics=naics,
            poc_name=poc_info.get('name'),
            poc_email=poc_info.get('email'),
            poc_phone=poc_info.get('phone'),
            address=address,
            sam_registered=sam_registered,
        )
    
    @staticmethod
    def _extract_company_name(text: str) -> Optional[str]:
        """Extract company name with multiple strategies"""
        # Strategy 1: Everything before "UEI:"
        uei_index = text.find("UEI:")
        if uei_index > 0:
            name = text[:uei_index].strip()
            if name and len(name) > 2:  # Valid name
                return name
        
        # Strategy 2: Look for common company patterns
        company_patterns = [
            r'^([A-Z][A-Za-z\s&,-]+(?:LLC|Inc|Corp|Corporation|Co\.?|Company))',
            r'([A-Z][A-Za-z\s]+(?:LLC|Inc|Corp|Corporation))',
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        # Strategy 3: First meaningful sequence before known keywords
        words = text.split()
        name_words = []
        for word in words:
            if word.upper() in ['UEI:', 'DUNS:', 'NAICS:', 'POC:', 'ADDRESS:', 'SAM.GOV:']:
                break
            name_words.append(word)
        
        if name_words:
            return " ".join(name_words).strip()
        
        return None
    
    @staticmethod
    def _extract_poc_info(text: str) -> Dict[str, Optional[str]]:
        """Extract POC name, email, and phone with improved regex"""
        poc_info: Dict[str, Optional[str]] = {'name': None, 'email': None, 'phone': None}
        
        # Find POC section
        poc_match = re.search(r'POC:\s*([^,]+),\s*([^,\s]+),\s*([^,\s]+)', text)
        if poc_match:
            poc_info['name'] = poc_match.group(1).strip()
            
            # Determine which is email and which is phone
            item2 = poc_match.group(2).strip()
            item3 = poc_match.group(3).strip()
            
            # Check if item2 is email
            if '@' in item2:
                poc_info['email'] = item2
                poc_info['phone'] = item3
            elif '@' in item3:
                poc_info['email'] = item3
                poc_info['phone'] = item2
            else:
                # Try to determine by pattern
                if re.match(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', item2):
                    poc_info['phone'] = item2
                    poc_info['email'] = item3
                else:
                    poc_info['email'] = item2
                    poc_info['phone'] = item3
        
        # Fallback: search for email and phone separately
        if not poc_info['email']:
            email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text)
            if email_match:
                poc_info['email'] = email_match.group(1)
        
        if not poc_info['phone']:
            phone_match = re.search(r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})', text)
            if phone_match:
                poc_info['phone'] = phone_match.group(1)
        
        return poc_info
    
    @staticmethod
    def parse_past_performance(text: str) -> List[PastPerformance]:
        """Enhanced past performance parser"""
        logger.info(f"Parsing past performance from: {text[:100]}...")
        
        # Collapse all whitespace into a single space
        squeezed = " ".join(text.split())
        logger.debug(f"Squeezed PP text: {squeezed}")

        customer = DocumentParser._search_between(squeezed, "Customer:", ["Contract:", "Value:", "Period:"])
        contract = DocumentParser._search_between(squeezed, "Contract:", ["Value:", "Period:", "Contact:"])
        value = DocumentParser._search_between(squeezed, "Value:", ["Period:", "Contact:"])
        period = DocumentParser._search_between(squeezed, "Period:", ["Contact:"])
        
        # Enhanced contact extraction
        contact_info = DocumentParser._extract_contact_info(squeezed)
        
        logger.info(f"PP Extracted: customer={customer}, value={value}, contact={contact_info.get('name')}")

        return [
            PastPerformance(
                customer=customer,
                contract_description=contract,
                contract_value=value,
                period=period,
                contact_name=contact_info.get('name'),
                contact_email=contact_info.get('email'),
            )
        ]
    
    @staticmethod
    def _extract_contact_info(text: str) -> Dict[str, Optional[str]]:
        """Extract contact name and email from past performance"""
        contact_info: Dict[str, Optional[str]] = {'name': None, 'email': None}
        
        # Pattern 1: "Contact: Name, email"
        contact_match = re.search(r'Contact:\s*([^,]+),\s*([^\s,]+)', text)
        if contact_match:
            contact_info['name'] = contact_match.group(1).strip()
            potential_email = contact_match.group(2).strip()
            if '@' in potential_email:
                contact_info['email'] = potential_email
        
        # Pattern 2: "Contact: email" (just email)
        elif re.search(r'Contact:\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text):
            email_match = re.search(r'Contact:\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text)
            if email_match:
                contact_info['email'] = email_match.group(1)
        
        return contact_info

    @staticmethod
    def _search_between(text: str, start: str, end_options: List[str]) -> Optional[str]:
        """Enhanced search with multiple possible end markers"""
        # Handle empty list - search to end of string
        if not end_options:
            pattern = re.escape(start) + r'\s*(.*?)$'
            match = re.search(pattern, text, re.IGNORECASE)
            if match and match.group(1).strip():
                result = match.group(1).strip()
                logger.debug(f"Found between '{start}' and end: {result}")
                return result
            return None
        
        # Try each end option
        for end in end_options:
            pattern = re.escape(start) + r'\s*(.*?)\s*' + re.escape(end)
            match = re.search(pattern, text, re.IGNORECASE)
            if match and match.group(1).strip():
                result = match.group(1).strip()
                logger.debug(f"Found between '{start}' and '{end}': {result}")
                return result
        
        # Fallback: search to end of string
        pattern = re.escape(start) + r'\s*(.*?)$'
        match = re.search(pattern, text, re.IGNORECASE)
        if match and match.group(1).strip():
            result = match.group(1).strip()
            logger.debug(f"Found between '{start}' and end (fallback): {result}")
            return result
        
        return None
    
    @staticmethod
    def parse_pricing_sheet(text: str) -> PricingSheet:
        """
        Enhanced pricing sheet parser - works for any unit (e.g., 'Hour', 'Day', 'Month', etc.)
        """
        import re
        labor_categories = []

        # Remove common header if present
        text_clean = re.sub(r"(?i)labor category, rate, unit", "", text).strip()

        # Split always by line (newline) first; fallback to "double space" or comma-row
        raw_rows = re.split(r'(?:\r?\n)+|\s{2,}', text_clean)
        for row in raw_rows:
            # Accept both "Position, Rate, Unit" and "Position, Rate"
            parts = [p.strip() for p in row.split(",") if p.strip()]
            # Pad up to three to always allow for incomplete entries for validation
            while len(parts) < 3:
                parts.append(None)
            category, rate, unit = parts[:3]
            try:
                rate_val = float(rate) if (rate and re.match(r'^\d+(\.\d+)?$', rate.replace('$', '').replace(',', ''))) else None
            except Exception:
                rate_val = None
            labor_categories.append({
                "category": category if category else None,
                "rate": rate_val,
                "unit": unit if unit and len(unit) < 32 else None   # Some basic sanity on length
            })

        return PricingSheet(labor_categories=labor_categories)

    
    @staticmethod
    def _parse_pricing_line(line: str) -> Optional[Dict[str, Any]]:
        """Parse individual pricing line with multiple formats"""
        # Pattern 1: "Senior Developer, 185, Hour"
        if ',' in line:
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 3:
                try:
                    rate_str = parts[1].replace('$', '').replace(',', '')
                    rate = float(rate_str) if rate_str.replace('.', '').isdigit() else None
                    return {
                        "category": parts[0],
                        "rate": rate,
                        "unit": parts[2]
                    }
                except (ValueError, IndexError):
                    pass
        
        # Pattern 2: "Lead Developer $200 per hour"
        pattern2 = re.search(r'([^$]+)\$(\d+(?:\.\d{2})?)\s*per\s*(\w+)', line, re.IGNORECASE)
        if pattern2:
            return {
                "category": pattern2.group(1).strip(),
                "rate": float(pattern2.group(2)),
                "unit": pattern2.group(3)
            }
        
        # Pattern 3: "Position: Rate Unit" (space separated)
        parts = line.split()
        if len(parts) >= 3:
            try:
                rate_str = parts[-2].replace('$', '').replace(',', '')
                if rate_str.replace('.', '').isdigit():
                    return {
                        "category": " ".join(parts[:-2]),
                        "rate": float(rate_str),
                        "unit": parts[-1]
                    }
            except (ValueError, IndexError):
                pass
        
        return None

    @staticmethod
    def classify_document(text: str, type_hint: Optional[str] = None) -> str:
        """Enhanced document classification with logging"""
        if type_hint in ["profile", "past_performance", "pricing"]:
            logger.info(f"Using provided type hint: {type_hint}")
            return type_hint
        
        text_lower = text.lower()
        
        # Score-based classification
        scores: Dict[str, int] = {"profile": 0, "past_performance": 0, "pricing": 0}
        
        # Profile indicators
        profile_keywords = ["uei:", "duns:", "naics:", "sam.gov", "company", "llc", "inc", "corp"]
        scores["profile"] = sum(1 for kw in profile_keywords if kw in text_lower)
        
        # Past performance indicators
        pp_keywords = ["customer:", "contract:", "value:", "period:", "contact:"]
        scores["past_performance"] = sum(1 for kw in pp_keywords if kw in text_lower)
        
        # Pricing indicators
        pricing_keywords = ["labor category", "rate", "hour", "developer", "manager", "$", "per hour"]
        scores["pricing"] = sum(1 for kw in pricing_keywords if kw in text_lower)
        
        # Determine classification
        if max(scores.values()) == 0:
            logger.info("No clear classification indicators found - returning 'unknown'")
            return "unknown"
        
        classification = max(scores, key=lambda k: scores[k])
        logger.info(f"Classified as '{classification}' with scores: {scores}")
        return classification
