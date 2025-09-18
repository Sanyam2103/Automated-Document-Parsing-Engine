from fastapi import APIRouter, Form
from app.models.schemas import IngestResponse, ValidationIssues
from app.services.parser import DocumentParser
from app.services.validator import FieldValidator
from app.services.mapper import NaicsSinMapper
from app.services.checklist import build_checklist   # Import if you put it as a separate module
import uuid
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/ingest", response_model=IngestResponse)
async def ingest_documents( company_profile: str = Form(...),past_performance: str = Form(...)):
    """Process company profile and past performance documents"""
    
    request_id = str(uuid.uuid4())
    logger.info(f"Processing request {request_id}")
    
    parser = DocumentParser()
    
    # Parse documents
    company_data = parser.parse_company_profile(company_profile)
    performance_data = parser.parse_past_performance(past_performance)
    
    issues = FieldValidator.validate_company(company_data)
    sins = NaicsSinMapper.get_recommended_sins(company_data.naics)
    checklist = build_checklist(company_data, performance_data, issues)

    logger.info(f"Request {request_id}: Validations run: {issues.dict()}")
    logger.info(f"Request {request_id}: Outcome - issues: {issues.dict()}, sins: {sins}, checklist: {checklist.dict()}")

    # Basic response for now
    return IngestResponse(
        request_id=request_id,
        parsed={
            "company": company_data.dict(),
            "past_performance": [p.dict() for p in performance_data]
        },
        issues=issues,
        recommended_sins=sins,
        checklist=checklist
    )
