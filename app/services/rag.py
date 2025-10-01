import os
import json
import re
import logging
from typing import List, Dict, Any, Optional
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
from langchain.embeddings.base import Embeddings
import google.generativeai as genai
import numpy as np
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from app.services.validator import HybridValidator

load_dotenv()
logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

class CustomEmbeddings(Embeddings):
    """Custom embeddings using sentence-transformers"""
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(texts)
        return embeddings.tolist()
    
    def embed_query(self, text: str) -> List[float]:
        embedding = self.model.encode([text])
        return embedding[0].tolist()

class GSARulesRAG:
    """Production RAG system using direct Google GenAI"""
    
    def __init__(self, rules_documents=None):
        # Initialize custom embeddings
        self.embeddings = CustomEmbeddings()
        
        # Initialize Gemini model
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
        # GSA Rules Pack from assignment
        if rules_documents is not None:
            self.rules_documents = [
                Document(
                    page_content="NAICS & SIN Mapping: 541511 maps to 54151S, 541512 maps to 54151S, 541611 maps to 541611, 518210 maps to 518210C",
                    metadata={"rule_id": "R2", "title": "NAICS & SIN Mapping", "category": "mapping"}
                ),
                Document(
                    page_content="Past Performance: At least 1 past performance contract ≥ $25,000 within last 36 months. Must include customer name, contract value, period, and contact email.",
                    metadata={"rule_id": "R3", "title": "Past Performance", "category": "performance"}
                ),
                Document(
                    page_content="Pricing & Catalog: Provide labor categories and rates in structured sheet. If missing rate basis or units, flag pricing_incomplete.",
                    metadata={"rule_id": "R4", "title": "Pricing & Catalog", "category": "pricing"}
                ),
                Document(
                    page_content="Submission Hygiene: All personally identifiable information must be stored in redacted form. Only derived fields and hashes are stored by default.",
                    metadata={"rule_id": "R5", "title": "Submission Hygiene", "category": "security"}
                )]
        else:
            self.rules_documents = [
                Document(
                    page_content="Identity & Registry: Required UEI (12 chars), DUNS (9 digits), and active SAM.gov registration. Primary contact must have valid email and phone.",
                    metadata={"rule_id": "R1", "title": "Identity & Registry", "category": "identity"}
                ),
                Document(
                    page_content="NAICS & SIN Mapping: 541511 maps to 54151S, 541512 maps to 54151S, 541611 maps to 541611, 518210 maps to 518210C",
                    metadata={"rule_id": "R2", "title": "NAICS & SIN Mapping", "category": "mapping"}
                ),
                Document(
                    page_content="Past Performance: At least 1 past performance contract ≥ $25,000 within last 36 months. Must include customer name, contract value, period, and contact email.",
                    metadata={"rule_id": "R3", "title": "Past Performance", "category": "performance"}
                ),
                Document(
                    page_content="Pricing & Catalog: Provide labor categories and rates in structured sheet. If missing rate basis or units, flag pricing_incomplete.",
                    metadata={"rule_id": "R4", "title": "Pricing & Catalog", "category": "pricing"}
                ),
                Document(
                    page_content="Submission Hygiene: All personally identifiable information must be stored in redacted form. Only derived fields and hashes are stored by default.",
                    metadata={"rule_id": "R5", "title": "Submission Hygiene", "category": "security"}
                )
            ]
        
        # Initialize vector store
        self.vectorstore = None
        self._initialize_vectorstore()

    # @classmethod
    # def with_rules_override(cls, rules_documents):
    #     """
    #     Alternate constructor to initialize GSARulesRAG with a custom rules_documents list.
    #     Example: To test without R1, pass a rules list excluding R1.
    #     """
    #     return cls(rules_documents=rules_documents)

    def _initialize_vectorstore(self):
        """Initialize ChromaDB vector store with GSA rules"""
        try:
            self.vectorstore = Chroma.from_documents(
                documents=self.rules_documents,
                embedding=self.embeddings,
                collection_name="gsa_rules_direct"
            )
            logger.info("Vector store initialized successfully with sentence-transformers")
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise
    
    def retrieve_relevant_rules(self, query: str, k: int = 3) -> List[Document]:
        """Retrieve most relevant rules for a query using semantic search"""
        if not self.vectorstore:
            logger.warning("Vector store not initialized")
            return []
        
        try:
            docs = self.vectorstore.similarity_search(query, k=k)
            logger.info(f"Retrieved {len(docs)} relevant rules for query: {query}")
            return docs
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return []
    
    def _extract_json_from_response(self, response_text: str) -> str:
        """Extract JSON from Gemini response, handling various formatting"""
        response_text = response_text.strip()
        
        # Handle markdown code blocks with ```
        if "```json" in response_text:
            # Extract content between ``````
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            if end != -1:
                response_text = response_text[start:end].strip()
        elif response_text.startswith("```"):
            # Remove generic code blocks (``````)
            response_text = response_text[3:-3].strip()
        
        # Find the actual JSON content by locating the outermost braces
        start_idx = response_text.find("{")
        end_idx = response_text.rfind("}") + 1
        
        if start_idx != -1 and end_idx > start_idx:
            response_text = response_text[start_idx:end_idx]
        
        return response_text
    
    def build_policy_checklist(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build policy-aware checklist using RAG and Gemini"""
        
        # Get relevant context from vector store
        issues = HybridValidator.validate_all_data(parsed_data)
        problems = []
        citations = []

        # For each issue, retrieve its corresponding rule doc(s)
        matched_rules = {}  # Map: issue_id -> (rule_doc/None)

        for issue in issues:
            # Determine query for rule retrieval (can use category if present, else fallback)
            query = getattr(issue, "rule_category", "") or getattr(issue, "description", "")
            rule_docs = self.retrieve_relevant_rules(query, k=1)
            rule_doc = rule_docs[0] if rule_docs else None
            matched_rules[issue.issue_id] = rule_doc

            # Extract correct rule_id for each issue from the matched rule doc
            if rule_doc and "rule_id" in rule_doc.metadata:
                rule_id = rule_doc.metadata["rule_id"]
            else:
                rule_id = "UNKNOWN"

            problems.append({
                "issue": issue.issue_id,
                "evidence": issue.evidence,
                "rule_id": rule_id
            })

            # Add citation for this rule_doc unless already present (by rule_id)
            if rule_doc and rule_id != "UNKNOWN" and rule_id not in {c["rule_id"] for c in citations}:
                citations.append({
                    "rule_id": rule_id,
                    "chunk": rule_doc.page_content
                })

        # Build context block for prompt
        context = "\n\n".join([f"{c['rule_id']}: {c['chunk']}" for c in citations])

        prompt = f"""
        You are a GSA compliance expert. Analyze the provided vendor data for GSA rules. Below, issues have already been detected by the system's rule checker and are attributed to specific rule IDs and evidence.

        DO NOT merge evidence or issue descriptions across rules or sections; report each issue using the evidence and rule_id provided.
        If no issues are present for a rule, do not fabricate evidence or descriptions.

        SYSTEM-DETECTED COMPLIANCE ISSUES:
        {"; ".join(
            f"Rule: {p['rule_id']}, Issue: {p['issue']}, Evidence: {p['evidence']}" for p in problems
        )}

        GSA RULES CONTEXT:
        {context}

        VENDOR DATA:
        Company: {str(parsed_data.get("company", {}))}
        Past Performance: {str(parsed_data.get("past_performance", []))}
        Pricing: {str(parsed_data.get("pricing", {}))}

        Based on the GSA rules above and the system-detected issues, return a JSON checklist that ONLY includes the issues, evidence, and rule_ids as provided.
        Response format:
        {{
        "required_ok": true/false,
        "problems": [
            {{"issue": "issue_id", "evidence": "evidence", "rule_id": "rule_id"}}
        ],
        "citations": [
            {{"rule_id": "R1", "chunk": "rule description"}}
        ]
        }}
        Do not invent or infer issues, evidence, or rule references outside of those provided above.
        Return STRICTLY valid JSON. Do not include any other text, explanations, or formatting.
        """

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Use robust JSON extraction
            clean_json = self._extract_json_from_response(response_text)
            
            # Parse JSON with better error handling
            try:
                checklist_result = json.loads(clean_json)
                
                # Validate required fields exist
                if not isinstance(checklist_result, dict):
                    raise ValueError("Response is not a dictionary")
                
                required_fields = ["required_ok", "problems", "citations"]
                for field in required_fields:
                    if field not in checklist_result:
                        logger.warning(f"Missing field {field} in LLM response, using fallback")
                        return self._fallback_checklist(parsed_data)
                
                logger.info("Successfully generated policy checklist using Gemini")
                return checklist_result
                
            except json.JSONDecodeError as je:
                logger.error(f"JSON decode error: {je}. Response was: {clean_json[:200]}...")
                return self._fallback_checklist(parsed_data)
                
        except Exception as e:
            logger.error(f"Error generating checklist with Gemini: {e}")
            return self._fallback_checklist(parsed_data)
    
    def _fallback_checklist(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback rule-based checklist if LLM fails"""
        checklist = {
            "required_ok": True,
            "problems": [],
            "citations": [
                {"rule_id": "R1", "chunk": "Identity & Registry requirements"},
                {"rule_id": "R3", "chunk": "Past Performance requirements"}
            ]
        }
        
        company = parsed_data.get("company", {})
        past_performance = parsed_data.get("past_performance", [])
        
        # R1: UEI check
        if not company.get("uei") or len(str(company.get("uei", ""))) != 12:
            checklist["problems"].append({
                "issue": "missing_uei",
                "evidence": "UEI field is empty, missing, or not 12 characters",
                "rule_id": "R1"
            })
            checklist["required_ok"] = False
        
        # R1: DUNS check
        if not company.get("duns"):
            checklist["problems"].append({
                "issue": "missing_duns",
                "evidence": "DUNS field is empty or missing",
                "rule_id": "R1"
            })
            checklist["required_ok"] = False
        
        # R1: SAM status check
        if company.get("sam_status") != "registered":
            checklist["problems"].append({
                "issue": "sam_not_active",
                "evidence": f"SAM.gov status is '{company.get('sam_status')}', should be 'registered'",
                "rule_id": "R1"
            })
            checklist["required_ok"] = False
        
        # R3: Past Performance value check
        valid_pp = 0
        for pp in past_performance:
            value_str = str(pp.get("value", "0"))
            # Extract numeric value from strings like "$25,000" or "25000"
            value_numbers = re.findall(r'[\d,]+', value_str)
            if value_numbers:
                try:
                    value = int(value_numbers[0].replace(',', ''))
                    if value >= 25000:
                        valid_pp += 1
                except (ValueError, IndexError):
                    continue
        
        if valid_pp == 0:
            checklist["problems"].append({
                "issue": "past_performance_min_value_not_met",
                "evidence": f"No past performance contracts ≥ $25,000 found. Total contracts: {len(past_performance)}",
                "rule_id": "R3"
            })
            checklist["required_ok"] = False
        
        # R4: Pricing check
        pricing = parsed_data.get("pricing")
        if not pricing or not pricing.get("labor_categories"):
            checklist["problems"].append({
                "issue": "pricing_incomplete",
                "evidence": "No labor categories found in pricing data",
                "rule_id": "R4"
            })
            checklist["required_ok"] = False
        
        logger.info(f"Fallback checklist completed. Found {len(checklist['problems'])} issues.")
        return checklist
