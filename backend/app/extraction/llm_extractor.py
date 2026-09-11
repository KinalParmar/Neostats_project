from typing import Dict, Any, List
from openai import OpenAI
from app.core.config import settings
import json
import re


class LLMExtractor:
    """Uses LLM to extract structured data from document text"""
    
    def __init__(self):
        self.client = None
        self.model = None
        self.use_fallback = False
        
        if settings.LLM_PROVIDER == "ollama":
            # Use Ollama (FREE local LLM)
            try:
                self.client = OpenAI(
                    base_url=settings.OLLAMA_BASE_URL,
                    api_key="ollama"  # Ollama doesn't require a real API key
                )
                self.model = settings.OLLAMA_MODEL
            except Exception as e:
                print(f"Failed to initialize Ollama client: {e}. Using fallback mode.")
                self.use_fallback = True
        elif settings.LLM_PROVIDER == "openai":
            # Use OpenAI
            if settings.OPENAI_API_KEY:
                self.client = OpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    base_url=settings.OPENAI_BASE_URL
                )
                self.model = settings.OPENAI_MODEL
            else:
                print("OpenAI API key not configured. Using fallback mode.")
                self.use_fallback = True
    
    def extract(self, text_by_page: List[Dict[str, Any]], document_type: str) -> Dict[str, Any]:
        """
        Extract structured data using LLM.
        Returns extracted fields, tables, and evidence.
        """
        if self.use_fallback:
            return self._fallback_extraction(text_by_page, document_type)
        
        if not self.client:
            raise Exception("LLM client not configured. Please set LLM_PROVIDER in .env")
        
        # Combine text from all pages with page numbers
        full_text = self._prepare_text_with_pages(text_by_page)
        
        # Get extraction schema based on document type
        schema = self._get_schema_for_type(document_type)
        
        # Build prompt
        prompt = self._build_extraction_prompt(full_text, document_type, schema)
        
        try:
            # Call LLM
            # Note: Ollama doesn't support response_format={"type": "json_object"}
            # So we use a system prompt to enforce JSON output
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a document intelligence expert. Extract all meaningful fields and tables from financial documents. Return ONLY valid JSON, no markdown formatting, no explanations outside the JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0
            )
            
            # Parse response
            response_text = response.choices[0].message.content.strip()
            
            # Clean up response if it contains markdown code blocks
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            extracted_data = json.loads(response_text)
            
            # Add metadata
            extracted_data["extraction_metadata"] = {
                "model_used": self.model,
                "llm_provider": settings.LLM_PROVIDER,
                "document_type": document_type,
                "total_pages": len(text_by_page)
            }
            
            return extracted_data
            
        except Exception as e:
            print(f"LLM extraction failed: {e}. Falling back to rule-based extraction.")
            return self._fallback_extraction(text_by_page, document_type)
    
    def _fallback_extraction(self, text_by_page: List[Dict[str, Any]], document_type: str) -> Dict[str, Any]:
        """
        Fallback rule-based extraction when LLM is not available.
        Uses regex patterns to extract common fields.
        """
        full_text = self._prepare_text_with_pages(text_by_page)
        
        # Basic field extraction using regex
        fields = {}
        
        # Try to extract dates
        date_pattern = r'\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{4}'
        dates = re.findall(date_pattern, full_text)
        if dates:
            fields["date"] = {
                "value": dates[0],
                "evidence": dates[0],
                "page_number": 1
            }
        
        # Try to extract monetary values
        money_pattern = r'[\$€£]?\s*[\d,]+\.?\d*\s*(?:USD|EUR|GBP|dollars?|euros?|pounds?)?'
        money_values = re.findall(money_pattern, full_text)
        if money_values:
            fields["total"] = {
                "value": money_values[0],
                "evidence": money_values[0],
                "page_number": 1
            }
        
        # Try to extract invoice numbers
        invoice_pattern = r'(?:invoice|inv|bill)\s*#?\s*[:#]?\s*([A-Z0-9-]+)'
        invoice_match = re.search(invoice_pattern, full_text, re.IGNORECASE)
        if invoice_match:
            fields["invoice_number"] = {
                "value": invoice_match.group(1),
                "evidence": invoice_match.group(0),
                "page_number": 1
            }
        
        # Add metadata
        return {
            "fields": fields,
            "tables": [],
            "extraction_metadata": {
                "model_used": "rule_based_fallback",
                "llm_provider": "fallback",
                "document_type": document_type,
                "total_pages": len(text_by_page),
                "note": "LLM not available, using rule-based extraction"
            }
        }
    
    def _prepare_text_with_pages(self, text_by_page: List[Dict[str, Any]]) -> str:
        """Prepare text with page markers for evidence tracking"""
        pages_text = []
        for page in text_by_page:
            pages_text.append(f"--- Page {page['page_number']} ---\n{page['text']}")
        return "\n\n".join(pages_text)
    
    def _get_schema_for_type(self, document_type: str) -> Dict[str, Any]:
        """Return JSON schema for the document type"""
        # Simplified schemas - will be expanded based on needs
        schemas = {
            "invoice": {
                "type": "object",
                "properties": {
                    "fields": {"type": "object"},
                    "tables": {"type": "array"},
                    "evidence": {"type": "object"}
                }
            },
            "balance_sheet": {
                "type": "object",
                "properties": {
                    "fields": {"type": "object"},
                    "tables": {"type": "array"},
                    "evidence": {"type": "object"}
                }
            },
            "profit_loss": {
                "type": "object",
                "properties": {
                    "fields": {"type": "object"},
                    "tables": {"type": "array"},
                    "evidence": {"type": "object"}
                }
            },
            "cash_flow": {
                "type": "object",
                "properties": {
                    "fields": {"type": "object"},
                    "tables": {"type": "array"},
                    "evidence": {"type": "object"}
                }
            }
        }
        return schemas.get(document_type, schemas["invoice"])
    
    def _build_extraction_prompt(self, text: str, document_type: str, schema: Dict[str, Any]) -> str:
        """Build extraction prompt for LLM"""
        return f"""
Extract ALL meaningful fields and tables from this {document_type} document.

Document text (with page numbers):
{text}

Extract:
1. All header fields (dates, parties, currencies, totals, etc.)
2. All tables/line items with their values
3. For each extracted value, include the source text snippet and page number as evidence

Return JSON with this structure:
{{
  "fields": {{
    "field_name": {{
      "value": "extracted value or null if missing",
      "evidence": "source text snippet",
      "page_number": 1
    }}
  }},
  "tables": [
    {{
      "name": "table name",
      "headers": ["col1", "col2", ...],
      "rows": [
        {{"col1": "val1", "col2": "val2", ...}}
      ],
      "evidence": "source text snippet",
      "page_number": 1
    }}
  ]
}}

IMPORTANT:
- If a field is not present in the document, use null - never invent values
- Include page numbers for evidence
- Extract ALL visible data, not just a fixed set of fields
"""
