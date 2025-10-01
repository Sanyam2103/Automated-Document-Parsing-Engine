import re

import hashlib
import secrets
from app.models.schemas import CompanyProfile,PastPerformance
from typing import Dict, List, Tuple,Any
from hashlib import sha256

class PIIRedactor:
    # Same patterns as before
    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    PHONE_PATTERN = r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})'
    
    # Salt for hashing (in production, this would be from secure config)
    SALT = "getgsa_secure_salt_2024"
    
    @staticmethod
    def _hash_pii(pii_value: str) -> str:
        """Hash PII with salt for secure storage"""
        # Normalize the value (remove spaces, convert to lowercase for emails)
        normalized = pii_value.lower().strip()
        
        # Add salt and hash with SHA-256
        salted_value = f"{PIIRedactor.SALT}{normalized}"
        hash_object = hashlib.sha256(salted_value.encode())
        return hash_object.hexdigest()[:16]  # Use first 16 chars for readability
    
    @staticmethod
    def redact_and_hash_pii(text: str) -> Tuple[str, Dict[str, List[str]]]:
        """
        Redact PII from text but store hashed versions for later verification
        
        Returns:
        - redacted_text: Text with PII replaced by hashed tokens
        - pii_hashes: Dictionary mapping hash tokens to original PII for verification
        """
        pii_hashes = {"emails": [], "phones": []}
        redacted_text = text
        
        # Find and hash emails
        emails = re.findall(PIIRedactor.EMAIL_PATTERN, text)
        for email in emails:
            email_hash = PIIRedactor._hash_pii(email)
            hash_token = f"[EMAIL_HASH_{email_hash}]"
            
            # Replace in text and store mapping
            redacted_text = redacted_text.replace(email, hash_token)
            pii_hashes["emails"].append({
                "original": email,
                "hash": email_hash,
                "token": hash_token
            })
        
        # Find and hash phone numbers
        phones = re.findall(PIIRedactor.PHONE_PATTERN, text)
        for phone in phones:
            # Normalize phone (remove formatting for consistent hashing)
            normalized_phone = re.sub(r'[^\d]', '', phone)
            phone_hash = PIIRedactor._hash_pii(normalized_phone)
            hash_token = f"[PHONE_HASH_{phone_hash}]"
            
            # Replace in text and store mapping
            redacted_text = redacted_text.replace(phone, hash_token)
            pii_hashes["phones"].append({
                "original": phone,
                "normalized": normalized_phone,
                "hash": phone_hash,
                "token": hash_token
            })
        
        return redacted_text, pii_hashes
    
    @staticmethod
    def _hash_pii_V2(val: str) -> str:
        return sha256(val.encode()).hexdigest()[:10]

    @staticmethod
    def redact_and_hash_companyprofile(profile: CompanyProfile) -> Tuple[CompanyProfile, Dict[str, List[Dict[str, str]]]]:
        """
        Redact and hash PII (email, phone) in CompanyProfile.
        Returns (redacted_companyprofile_dict, pii_hashes_dict)
        """
        pii_hashes = {"emails": [], "phones": []}
        # Get a dict for copying, as pydantic models are immutable by default unless you set allow_mutation
        data = profile.dict()
        
        if data.get("poc_email"):
            email = data["poc_email"]
            email_hash = PIIRedactor._hash_pii_V2(email)
            data["poc_email"] = f"[EMAIL_HASH_{email_hash}]"
            pii_hashes["emails"].append({ "hash": email_hash, "token": data["poc_email"]})
        
        if data.get("poc_phone"):
            phone = data["poc_phone"]
            phone_hash = PIIRedactor._hash_pii_V2(phone)
            data["poc_phone"] = f"[PHONE_HASH_{phone_hash}]"
            pii_hashes["phones"].append({ "hash": phone_hash, "token": data["poc_phone"]})
        
        # Return a new CompanyProfile instance (does not mutate input)
        redacted_profile = CompanyProfile(**data)
        return redacted_profile, pii_hashes

    @staticmethod
    def redact_and_hash_pastperformance(pp:PastPerformance) -> Tuple[PastPerformance, Dict[str, List[Dict[str, str]]]]:
        """
        Redact and hash PII (email, phone) in PastPerformance.
        Returns (redacted_pastperformance_dict, pii_hashes_dict)
        """
        pii_hashes = {"emails": [], "phones": []}
        data = pp.dict()
        if data.get("contact_email"):
            email = data["contact_email"]
            email_hash = PIIRedactor._hash_pii_V2(email)
            data["contact_email"] = f"[EMAIL_HASH_{email_hash}]"
            pii_hashes["emails"].append({ "hash": email_hash, "token": data["contact_email"]})

        if data.get("contact_phone"):
            phone = data["contact_phone"]
            phone_hash = PIIRedactor._hash_pii_V2(phone)
            data["contact_phone"] = f"[PHONE_HASH_{phone_hash}]"
            pii_hashes["phones"].append({"hash": phone_hash, "token": data["contact_phone"]})

        redacted_pp = PastPerformance(**data)
        return redacted_pp, pii_hashes
    
    @staticmethod
    def verify_email(email_to_verify: str, stored_hash: str) -> bool:
        """Verify if an email matches a stored hash"""
        computed_hash = PIIRedactor._hash_pii(email_to_verify)
        return computed_hash == stored_hash
    
    @staticmethod
    def verify_phone(phone_to_verify: str, stored_hash: str) -> bool:
        """Verify if a phone number matches a stored hash"""
        normalized_phone = re.sub(r'[^\d]', '', phone_to_verify)
        computed_hash = PIIRedactor._hash_pii(normalized_phone)
        return computed_hash == stored_hash

    # @staticmethod
    # def test_hashing():
    #     """Test the hashing logic"""
    #     test_text = "POC: Jane Smith, jane@acme.co, (415) 555-0100 and backup email: support@acme.co"
    #     redacted, hashes = PIIRedactor.redact_and_hash_pii(test_text)
        
    #     print(f"Original: {test_text}")
    #     print(f"Redacted: {redacted}")
    #     print(f"PII Hashes: {hashes}")
        
    #     # Test verification
    #     print(f"Verify jane@acme.co: {PIIRedactor.verify_email('jane@acme.co', hashes['emails'][0]['hash'])}")
    #     print(f"Verify wrong email: {PIIRedactor.verify_email('wrong@email.com', hashes['emails'][0]['hash'])}")
