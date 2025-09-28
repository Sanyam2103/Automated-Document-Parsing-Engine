# app/models/schemas.py
from typing import List, Optional
from pydantic import BaseModel, EmailStr, field_validator
import re
import uuid

class CompanyProfile(BaseModel):
    company_name: Optional[str] = None
    uei: Optional[str] = None
    duns: Optional[str] = None
    naics: List[str] = []
    poc_name: Optional[str] = None
    poc_email: Optional[str] = None
    poc_phone: Optional[str] = None
    address: Optional[str] = None
    sam_registered: Optional[bool] = None


class PastPerformance(BaseModel):
    customer: Optional[str] = None
    contract_description: Optional[str] = None
    contract_value: Optional[str] = None
    period: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None

class ValidationIssues(BaseModel):
    missing_uei: bool = False
    invalid_poc_email: bool = False
    missing_naics: bool = False
    missing_company_name: bool = False
    missing_sam_status: bool = False

class Checklist(BaseModel):
    required_fields_complete: bool = False
    valid_contact_info: bool = False
    sam_registered: bool = False
    has_past_performance: bool = False

class IngestResponse(BaseModel):
    request_id: str
    parsed: dict
    issues: ValidationIssues
    recommended_sins: List[str]
    checklist: Checklist
    doc_summaries: Optional[List[dict]] = None

class DocumentInput(BaseModel):
    name: Optional[str]= None
    type_hint: Optional[str] = None
    text:str

class IngestRequestV2(BaseModel):
    documents: List[DocumentInput]    

class PricingSheet(BaseModel):
    labor_categories: List[dict] = []  
    # [{"category": "Senior Developer", "rate": 185, "unit": "Hour"}]    

class IngestResponseV2(BaseModel):
    request_id: str
    doc_summaries: List[dict]    