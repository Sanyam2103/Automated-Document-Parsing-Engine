from fastapi import APIRouter, Form
from app.models.schemas import IngestResponse, IngestRequestV2, PricingSheet, DocumentInput, ValidationIssues, IngestResponseV2
from app.services.parser import DocumentParser
from app.services.mapper import NaicsSinMapper
from app.services.checklist import build_checklist
from app.services.redactor import PIIRedactor
from typing import List, Optional
import uuid
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Global storage
document_store = {}
current_request_id = None

# Lazy initialization - services created only when needed
_rag_service = None
_llm_service = None

def get_rag_service():
    """Lazy initialize RAG service"""
    global _rag_service
    if _rag_service is None:
        try:
            from app.services.rag import GSARulesRAG
            _rag_service = GSARulesRAG()
            logger.info("RAG service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {e}")
            _rag_service = None
    return _rag_service

def get_llm_service():
    """Lazy initialize LLM service"""
    global _llm_service
    if _llm_service is None:
        try:
            from app.services.llm import LLMService
            _llm_service = LLMService()
            logger.info("LLM service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LLM service: {e}")
            _llm_service = None
    return _llm_service

@router.post("/ingest", response_model=IngestResponse)
# async def ingest_documents(company_profile: str = Form(...), past_performance: str = Form(...)):
    # """Process company profile and past performance documents"""
    
    # request_id = str(uuid.uuid4())
    # logger.info(f"Processing request {request_id}")
    
    # parser = DocumentParser()
    
    # # Parse documents
    # company_data = parser.parse_company_profile(company_profile)
    # performance_data = parser.parse_past_performance(past_performance)
    
    # issues = FieldValidator.validate_company(company_data)
    # sins = NaicsSinMapper.get_recommended_sins(company_data.naics)
    # checklist = build_checklist(company_data, performance_data, issues)

    # logger.info(f"Request {request_id}: Validations run: {issues.dict()}")
    # logger.info(f"Request {request_id}: Outcome - issues: {issues.dict()}, sins: {sins}, checklist: {checklist.dict()}")

    # return IngestResponse(
    #     request_id=request_id,
    #     parsed={
    #         "company": company_data.dict(),
    #         "past_performance": [p.dict() for p in performance_data]
    #     },
    #     issues=issues,
    #     recommended_sins=sins,
    #     checklist=checklist
    # )

@router.post("/ingest_v2", response_model=IngestResponseV2)
async def ingest_documents_v2(request: IngestRequestV2):
    """New ingest endpoint supporting multiple document types with PII redaction"""
    global current_request_id
    
    request_id = str(uuid.uuid4())
    current_request_id = request_id
    logger.info(f"Processing request {request_id} with {len(request.documents)} documents")
    
    parser = DocumentParser()
    
    # Store redacted documents and parse fields
    redacted_docs = { "company": None, "past_performance": [], "pricing": None}
    parsed_data = {"company": None, "past_performance": [], "pricing": None}
    temp=[]
    for doc in request.documents:
        # Classify document
        doc_type = parser.classify_document(doc.text, doc.type_hint)
        temp.append({"name": doc.name,"type": doc_type,"redacted":True})
        
        # Parse based on type
        if doc_type == "profile":
            parsed_data["company"] = parser.parse_company_profile(doc.text)
        elif doc_type == "past_performance":
            parsed_data["past_performance"].extend(parser.parse_past_performance(doc.text))
        elif doc_type == "pricing":
            parsed_data["pricing"] = parser.parse_pricing_sheet(doc.text)
    

    redacted_text, pii_hashes = PIIRedactor.redact_and_hash_companyprofile(parsed_data["company"])

        # Store both redacted text AND hashes for verification
    redacted_docs["company"] = ({
        "redacted_text": redacted_text,
        "pii_hashes": pii_hashes
    })    


    for pp in parsed_data["past_performance"]:
        redacted_text2, pii_hashes2 = PIIRedactor.redact_and_hash_pastperformance(pp)
        redacted_docs["past_performance"].append({
            "redacted_text": redacted_text2,
            "pii_hashes": pii_hashes2
        })

    redacted_docs["pricing"]={"pricing": parsed_data["pricing"]}


    # Store redacted documents for analysis step
    document_store[request_id] = {
        "redacted_docs": redacted_docs,
        "parsed_data": parsed_data
    }

    logger.info(f"Request {request_id}: Stored {len(redacted_docs)} redacted documents")
    logger.info(f"Request {request_id}: Parsed data types: {list(parsed_data.keys())}")

    return IngestResponseV2(
        request_id=request_id,
        doc_summaries=temp
    )

@router.get("/healthz")
async def health_check():
    """Health check endpoint"""
    return {"ok": True}


@router.post("/analyze")
async def analyze_documents(request_id: Optional[str]):
    """Analyze stored documents using RAG and LLM"""
    global current_request_id
    
    # Use provided request_id or fall back to last ingested
    target_id = request_id or current_request_id
    
    if not target_id or target_id not in document_store:
        logger.warning(f"Request ID {target_id} not found")
        return {"error": "Request ID not found"}
    
    stored_data = document_store[target_id]
    redacted=stored_data["redacted_docs"]
    parsed_data = stored_data["parsed_data"]
    
    logger.info(f"Analyzing request {target_id}")
    
    try:
        # Try to get RAG service
        rag_service = get_rag_service()
        llm_service = get_llm_service()
        parsed_datav2=convert_to_dict(parsed_data)
        
        if rag_service and llm_service:
            # Full AI analysis
            checklist = rag_service.build_policy_checklist(parsed_datav2)
            brief = llm_service.generate_negotiation_brief(parsed_datav2, checklist)
            client_email = llm_service.generate_client_email(parsed_datav2, checklist)
            
            logger.info(f"Request {target_id}: AI analysis complete")
            
            return {
                "request_id": target_id,
                "parsed": redacted,
                "checklist": checklist,
                "brief": brief,
                "client_email": client_email,
                "citations": checklist.get("citations", []),
                "powered_by": "Google Gemini 2.0 Flash + RAG"
            }
        else:
            # Fallback to basic analysis
            logger.warning("AI services not available, using fallback analysis")
            return {
                "request_id": target_id,
                "parsed": redacted,
                "checklist": {"required_ok": True, "problems": [], "citations": []},
                "brief": "AI analysis not available. Please review manually.",
                "client_email": "AI email generation not available.",
                "citations": [],
                "powered_by": "Fallback Analysis"
            }
        
    except Exception as e:
        logger.error(f"Error analyzing request {target_id}: {e}")
        return {
            "error": f"Analysis failed: {str(e)}",
            "request_id": target_id
        }
    
def convert_to_dict(parsed_data):
    """Convert Pydantic objects to dictionaries for AI processing"""
    result = {}
    
    # Convert company profile
    if parsed_data.get("company"):
        if hasattr(parsed_data["company"], 'dict'):
            result["company"] = parsed_data["company"].dict()
        else:
            result["company"] = parsed_data["company"]
    else:
        result["company"] = None
    
    # Convert past performance list
    if parsed_data.get("past_performance"):
        pp_list = []
        for pp in parsed_data["past_performance"]:
            if hasattr(pp, 'dict'):
                pp_list.append(pp.dict())
            else:
                pp_list.append(pp)
        result["past_performance"] = pp_list
    else:
        result["past_performance"] = []
    
    # Convert pricing
    if parsed_data.get("pricing"):
        if hasattr(parsed_data["pricing"], 'dict'):
            result["pricing"] = parsed_data["pricing"].dict()
        else:
            result["pricing"] = parsed_data["pricing"]
    else:
        result["pricing"] = None
    
    return result


@router.get("/debug/{request_id}")
async def debug_stored_data(request_id: str):
    """Debug endpoint to check stored data"""
    if request_id not in document_store:
        return {"error": "Request ID not found"}
    
    stored_data = document_store[request_id]
    return {
        "request_id": request_id,
        "redacted_docs": stored_data["redacted_docs"],
        "parsed_data": stored_data["parsed_data"]
    }

@router.post("/test-services")
async def test_services():
    """Test if AI services can be initialized"""
    results = {}
    
    # Test RAG service
    try:
        rag_service = get_rag_service()
        results["rag"] = "available" if rag_service else "failed"
    except Exception as e:
        results["rag"] = f"error: {str(e)}"
    
    # Test LLM service
    try:
        llm_service = get_llm_service()
        results["llm"] = "available" if llm_service else "failed"
        
        if llm_service:
            # Test actual connection
            connection_test = llm_service.test_connection()
            results["llm_connection"] = connection_test
    except Exception as e:
        results["llm"] = f"error: {str(e)}"
    
    return results
