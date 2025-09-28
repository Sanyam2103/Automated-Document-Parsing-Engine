import os
import google.generativeai as genai
from typing import Dict, Any
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

class LLMService:
    """Production LLM service using direct Google GenAI"""
    
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Configure generation parameters
        self.generation_config = genai.types.GenerationConfig(
            temperature=0.3,
            top_p=0.8,
            top_k=40,
            max_output_tokens=1024
        )
    
    def generate_negotiation_brief(self, parsed_data: Dict[str, Any], checklist: Dict[str, Any]) -> str:
        """Generate negotiation prep brief using Gemini"""
        
        company = parsed_data.get("company", {})
        company_name = company.get("company_name", "Unknown Vendor")
        naics_codes = ", ".join(company.get("naics", []) if company.get("naics") else [])
        past_performance = parsed_data.get("past_performance", [])
        pricing = parsed_data.get("pricing", {})
        
        problems_text = "\n".join([
            f"- {p['issue'].replace('_', ' ').title()}: {p['evidence']} (Rule {p['rule_id']})"
            for p in checklist.get("problems", [])
        ]) or "No major compliance issues identified."
        
        prompt = f"""You are a GSA procurement specialist preparing a negotiation brief. Analyze the vendor's submission and compliance status.

VENDOR DATA:
Company: {company_name}
NAICS Codes: {naics_codes or 'Not provided'}
Past Performance: {len(past_performance)} contracts submitted
Pricing Provided: {'Yes - Labor categories included' if pricing and pricing.get("labor_categories") else 'No - Missing or incomplete'}

COMPLIANCE ISSUES:
{problems_text}

Generate a concise 2-paragraph negotiation brief covering:
1. **Strengths**: What the vendor does well, competitive advantages, areas of compliance
2. **Risks & Leverage Points**: Compliance gaps, missing documentation, areas for negotiation pressure

Write in professional tone suitable for internal GSA team review. Focus on actionable insights for negotiations.

Be specific about which GSA rules are satisfied or violated. Keep it under 200 words total."""
        
        try:
            response = self.model.generate_content(
                prompt, 
                generation_config=self.generation_config
            )
            logger.info("Generated negotiation brief using Gemini")
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error generating negotiation brief: {e}")
            return f"""**Negotiation Brief Error**: Unable to generate brief using AI. 
            
**Manual Review Required**: Company {company_name} has {len(checklist.get('problems', []))} compliance issues that need review. Please analyze vendor data manually and prepare negotiation strategy based on GSA requirements R1-R5."""
    
    def generate_client_email(self, parsed_data: Dict[str, Any], checklist: Dict[str, Any]) -> str:
        """Generate polite client email using Gemini"""
        
        company = parsed_data.get("company", {})
        company_name = company.get("company_name", "Vendor")
        problems = checklist.get("problems", [])
        
        if not problems:
            issues_summary = "All GSA requirements met - complete and compliant submission"
        else:
            issues_list = []
            for p in problems:
                issue_friendly = p['issue'].replace('_', ' ').title()
                issues_list.append(f"-  {issue_friendly}: {p['evidence']}")
            issues_summary = "\n".join(issues_list)
        
        prompt = f"""You are a GSA contracting officer. Write a professional email to a vendor about their submission status.

VENDOR: {company_name}
SUBMISSION STATUS: {'APPROVED' if not problems else 'REQUIRES ATTENTION'}

ISSUES FOUND:
{issues_summary}

Generate a professional email that:
1. Thanks them for their submission
2. If issues exist: clearly lists missing/incomplete items with specific requirements
3. If no issues: congratulates them and outlines next steps
4. Provides specific actionable next steps
5. Maintains encouraging, professional tone
6. Includes appropriate subject line

Keep it concise but thorough. Use GSA's professional communication style."""
        
        try:
            response = self.model.generate_content(
                prompt, 
                generation_config=self.generation_config
            )
            logger.info("Generated client email using Gemini")
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error generating client email: {e}")
            return f"""Subject: Submission Status - {company_name}

Dear {company_name} Team,

Thank you for your submission. Due to technical issues with our automated review system, we are unable to provide detailed feedback at this time.

Please contact our procurement office directly for manual review of your submission.

Best regards,
GSA Evaluation Team
            
[Error: {str(e)}]"""
    
    def test_connection(self) -> Dict[str, Any]:
        """Test Gemini API connection"""
        try:
            response = self.model.generate_content("Hello, this is a test. Please respond with 'API connection successful'.")
            return {
                "status": "success",
                "message": "Gemini API connected successfully",
                "response": response.text.strip()
            }
        except Exception as e:
            return {
                "status": "error", 
                "message": f"Gemini API connection failed: {str(e)}"
            }
