from typing import List, Dict, Any
import re
import logging
from app.schemas.document import ExtractedData, FieldExtraction, LineItem

logger = logging.getLogger(__name__)


class ExtractionService:
    """Service for extracting structured data from document text"""
    
    def __init__(self, use_ollama: bool = True, ollama_base_url: str = "http://localhost:11434", ollama_model: str = "llama3.2"):
        self.use_ollama = use_ollama
        self.ollama_base_url = ollama_base_url
        self.ollama_model = ollama_model
        self.ollama_client = None
        
        if self.use_ollama:
            try:
                from openai import OpenAI
                self.ollama_client = OpenAI(base_url=ollama_base_url, api_key="ollama")
                logger.info("Ollama client initialized")
            except ImportError:
                logger.warning("OpenAI library not available, falling back to rule-based extraction")
                self.use_ollama = False
    
    def extract(self, text_by_page: List[Dict[str, Any]], document_type: str) -> ExtractedData:
        """
        Extract structured data from document text
        """
        full_text = self._prepare_text(text_by_page)
        logger.info(f"Extraction - Document type: {document_type}, Text length: {len(full_text)}")
        logger.info(f"Extraction - First 500 chars: {full_text[:500]}")
        
        if self.use_ollama and self.ollama_client:
            try:
                logger.info("Attempting LLM extraction")
                result = self._llm_extraction(full_text, document_type)
                logger.info(f"LLM extraction result: {result}")
                return result
            except Exception as e:
                logger.error(f"LLM extraction failed: {e}, falling back to rule-based")
                return self._rule_based_extraction(full_text, document_type)
        else:
            logger.info("Using rule-based extraction")
            result = self._rule_based_extraction(full_text, document_type)
            logger.info(f"Rule-based extraction result: {result}")
            return result
    
    def _prepare_text(self, text_by_page: List[Dict[str, Any]]) -> str:
        """Prepare text from all pages"""
        return "\n\n".join([f"--- Page {p['page_number']} ---\n{p['text']}" for p in text_by_page])
    
    def _llm_extraction(self, text: str, document_type: str) -> ExtractedData:
        """Extract using Ollama LLM"""
        prompt = self._build_extraction_prompt(text, document_type)
        
        response = self.ollama_client.chat.completions.create(
            model=self.ollama_model,
            messages=[
                {"role": "system", "content": "You are a document extraction expert. Extract structured data from financial documents. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        result_text = response.choices[0].message.content
        return self._parse_llm_response(result_text, document_type)
    
    def _build_extraction_prompt(self, text: str, document_type: str) -> str:
        """Build extraction prompt for LLM with few-shot examples"""
        if document_type == "invoice":
            return f"""
You are an expert at extracting data from invoices. Extract the following fields from the invoice text below.

EXAMPLE 1:
Invoice text: "Invoice # INV-23891 Date: 2026-08-15 Vendor: ABC Technologies Currency: USD Subtotal: 12500.00 Tax: 625.00 Total: 13125.00"
Output: {{"invoice_number": "INV-23891", "invoice_date": "2026-08-15", "vendor_name": "ABC Technologies", "currency": "USD", "subtotal": 12500.00, "tax_amount": 625.00, "discount": 0.00, "total_amount": 13125.00, "line_items": []}}

EXAMPLE 2:
Invoice text: "Bill No: X00016469619 Amount Due: $150.00 Date: 15/11/2025"
Output: {{"invoice_number": "X00016469619", "invoice_date": "2025-11-15", "vendor_name": null, "currency": "USD", "subtotal": null, "tax_amount": null, "discount": null, "total_amount": 150.00, "line_items": []}}

Now extract from this invoice:
{text[:8000]}

Return ONLY valid JSON with this structure:
{{
  "invoice_number": "string or null",
  "invoice_date": "YYYY-MM-DD or null",
  "vendor_name": "string or null",
  "currency": "string or null",
  "subtotal": number or null,
  "tax_amount": number or null,
  "discount": number or null,
  "total_amount": number or null,
  "line_items": []
}}
"""
        elif document_type == "balance_sheet":
            return f"""
You are an expert at extracting data from balance sheets. Extract the following fields from the balance sheet text below.

EXAMPLE:
Balance sheet text: "Total Assets: $1,234,567.89 Total Liabilities: $123,456.78 Total Equity: $1,111,111.11"
Output: {{"total_assets": 1234567.89, "total_liabilities": 123456.78, "total_equity": 1111111.11}}

Now extract from this balance sheet:
{text[:8000]}

Return ONLY valid JSON with this structure:
{{
  "total_assets": number or null,
  "total_liabilities": number or null,
  "total_equity": number or null
}}
"""
        elif document_type == "profit_loss":
            return f"""
You are an expert at extracting data from profit & loss statements. Extract the following fields from the P&L text below.

EXAMPLE:
P&L text: "Revenue: $1,234,567.89 Expenses: $234,567.89 Net Profit: $1,000,000.00"
Output: {{"revenue": 1234567.89, "expenses": 234567.89, "net_profit": 1000000.00}}

Now extract from this profit & loss statement:
{text[:8000]}

Return ONLY valid JSON with this structure:
{{
  "revenue": number or null,
  "expenses": number or null,
  "net_profit": number or null
}}
"""
        elif document_type == "cash_flow":
            return f"""
You are an expert at extracting data from cash flow statements. Extract the following fields from the cash flow text below.

EXAMPLE:
Cash flow text: "Operating Cash Flow: $1,234,567.89 Investing Cash Flow: -$123,456.78 Financing Cash Flow: $50,000.00 Net Cash Flow: $1,161,111.11"
Output: {{"operating_cash_flow": 1234567.89, "investing_cash_flow": -123456.78, "financing_cash_flow": 50000.00, "net_cash_flow": 1161111.11}}

Now extract from this cash flow statement:
{text[:8000]}

Return ONLY valid JSON with this structure:
{{
  "operating_cash_flow": number or null,
  "investing_cash_flow": number or null,
  "financing_cash_flow": number or null,
  "net_cash_flow": number or null
}}
"""
        else:
            return f"Extract key financial data from this document:\n{text[:8000]}"
    
    def _parse_llm_response(self, response_text: str, document_type: str) -> ExtractedData:
        """Parse LLM response into ExtractedData"""
        import json
        
        # Try to extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            try:
                data = json.loads(json_match.group())
                return self._dict_to_extracted_data(data, document_type)
            except json.JSONDecodeError:
                pass
        
        # Fallback to rule-based
        return self._rule_based_extraction(response_text, document_type)
    
    def _dict_to_extracted_data(self, data: Dict, document_type: str) -> ExtractedData:
        """Convert dict to ExtractedData with confidence scores"""
        extracted = ExtractedData()
        
        def to_field_extraction(value: Any, confidence: float = 0.95) -> FieldExtraction:
            return FieldExtraction(value=value, confidence=confidence, page_number=1)
        
        if document_type == "invoice":
            if "invoice_number" in data:
                extracted.invoice_number = to_field_extraction(data["invoice_number"])
            if "invoice_date" in data:
                extracted.invoice_date = to_field_extraction(data["invoice_date"])
            if "vendor_name" in data:
                extracted.vendor_name = to_field_extraction(data["vendor_name"])
            if "currency" in data:
                extracted.currency = to_field_extraction(data["currency"])
            if "subtotal" in data:
                extracted.subtotal = to_field_extraction(float(data["subtotal"]))
            if "tax_amount" in data:
                extracted.tax_amount = to_field_extraction(float(data["tax_amount"]))
            if "discount" in data:
                extracted.discount = to_field_extraction(float(data.get("discount", 0)))
            if "total_amount" in data:
                extracted.total_amount = to_field_extraction(float(data["total_amount"]))
            if "line_items" in data:
                extracted.line_items = [LineItem(**item) for item in data["line_items"]]
        
        elif document_type == "balance_sheet":
            if "total_assets" in data:
                extracted.total_assets = to_field_extraction(float(data["total_assets"]))
            if "total_liabilities" in data:
                extracted.total_liabilities = to_field_extraction(float(data["total_liabilities"]))
            if "total_equity" in data:
                extracted.total_equity = to_field_extraction(float(data["total_equity"]))
        
        elif document_type == "profit_loss":
            if "revenue" in data:
                extracted.revenue = to_field_extraction(float(data["revenue"]))
            if "expenses" in data:
                extracted.expenses = to_field_extraction(float(data["expenses"]))
            if "net_profit" in data:
                extracted.net_profit = to_field_extraction(float(data["net_profit"]))
        
        elif document_type == "cash_flow":
            if "operating_cash_flow" in data:
                extracted.operating_cash_flow = to_field_extraction(float(data["operating_cash_flow"]))
            if "investing_cash_flow" in data:
                extracted.investing_cash_flow = to_field_extraction(float(data["investing_cash_flow"]))
            if "financing_cash_flow" in data:
                extracted.financing_cash_flow = to_field_extraction(float(data["financing_cash_flow"]))
            if "net_cash_flow" in data:
                extracted.net_cash_flow = to_field_extraction(float(data["net_cash_flow"]))
        
        return extracted
    
    def _rule_based_extraction(self, text: str, document_type: str) -> ExtractedData:
        """Rule-based extraction using regex patterns"""
        extracted = ExtractedData()
        
        def to_field_extraction(value: Any, confidence: float = 0.85) -> FieldExtraction:
            return FieldExtraction(value=value, confidence=confidence, page_number=1)
        
        # Extract dates (support DD/MM/YYYY, YYYY-MM-DD, etc.)
        date_patterns = [
            r'\d{4}[-/]\d{1,2}[-/]\d{1,2}',
            r'\d{1,2}[-/]\d{1,2}[-/]\d{4}',
            r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}',
        ]
        for pattern in date_patterns:
            dates = re.findall(pattern, text, re.IGNORECASE)
            if dates:
                extracted.invoice_date = to_field_extraction(dates[0])
                break
        
        # Extract monetary values (support various formats)
        money_patterns = [
            r'[\$€£₹₽]\s*[\d,]+\.?\d*',
            r'[\d,]+\.?\d*\s*(?:USD|EUR|GBP|INR|RUB)',
            r'total[:\s]*[\$€£₹₽]?\s*([\d,]+\.?\d*)',
            r'amount[:\s]*[\$€£₹₽]?\s*([\d,]+\.?\d*)',
            r'due[:\s]*[\$€£₹₽]?\s*([\d,]+\.?\d*)',
        ]
        for pattern in money_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Clean the match (remove currency symbols, commas)
                cleaned = re.sub(r'[^\d.]', '', matches[0])
                if cleaned:
                    extracted.total_amount = to_field_extraction(float(cleaned))
                break
        
        # Extract invoice numbers (support X00016469619 format, INV-23891, etc.)
        invoice_patterns = [
            r'[A-Z]\d{11,}',  # X00016469619 format
            r'(?:invoice|inv|bill)\s*#?\s*[:#]?\s*([A-Z0-9-]+)',
            r'invoice\s*no\.?\s*[:#]?\s*([A-Z0-9-]+)',
            r'bill\s*no\.?\s*[:#]?\s*([A-Z0-9-]+)',
        ]
        for pattern in invoice_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                invoice_num = match.group(1) if match.groups() else match.group(0)
                extracted.invoice_number = to_field_extraction(invoice_num)
                break
        
        # Extract company/vendor names
        company_patterns = [
            r'(?:vendor|supplier|from|company|to)[:\s]+([A-Z][A-Za-z\s&]+?)(?:\n|,|address|invoice|bill)',
            r'^()([A-Z][A-Za-z\s&]+?)(?:\n|,|address|invoice|bill)',
        ]
        for pattern in company_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                name = match.group(1).strip() if match.groups() else match.group(0).strip()
                if 2 < len(name) < 100:
                    extracted.vendor_name = to_field_extraction(name)
                    break
        
        # Document-specific extraction
        if document_type == "balance_sheet":
            assets_match = re.search(r'(?:total\s+assets)[:\s]*[\$€£₹₽]?\s*([\d,]+\.?\d*)', text, re.IGNORECASE)
            if assets_match:
                cleaned = re.sub(r'[^\d.]', '', assets_match.group(1))
                if cleaned:
                    extracted.total_assets = to_field_extraction(float(cleaned))
            
            liabilities_match = re.search(r'(?:total\s+liabilities)[:\s]*[\$€£₹₽]?\s*([\d,]+\.?\d*)', text, re.IGNORECASE)
            if liabilities_match:
                cleaned = re.sub(r'[^\d.]', '', liabilities_match.group(1))
                if cleaned:
                    extracted.total_liabilities = to_field_extraction(float(cleaned))
            
            equity_match = re.search(r'(?:total\s+equity|shareholders?\s+equity)[:\s]*[\$€£₹₽]?\s*([\d,]+\.?\d*)', text, re.IGNORECASE)
            if equity_match:
                cleaned = re.sub(r'[^\d.]', '', equity_match.group(1))
                if cleaned:
                    extracted.total_equity = to_field_extraction(float(cleaned))
        
        elif document_type == "profit_loss":
            revenue_match = re.search(r'(?:revenue|total\s+revenue|sales)[:\s]*[\$€£₹₽]?\s*([\d,]+\.?\d*)', text, re.IGNORECASE)
            if revenue_match:
                cleaned = re.sub(r'[^\d.]', '', revenue_match.group(1))
                if cleaned:
                    extracted.revenue = to_field_extraction(float(cleaned))
            
            expenses_match = re.search(r'(?:expenses|total\s+expenses)[:\s]*[\$€£₹₽]?\s*([\d,]+\.?\d*)', text, re.IGNORECASE)
            if expenses_match:
                cleaned = re.sub(r'[^\d.]', '', expenses_match.group(1))
                if cleaned:
                    extracted.expenses = to_field_extraction(float(cleaned))
            
            profit_match = re.search(r'(?:net\s+profit|net\s+income)[:\s]*[\$€£₹₽]?\s*([\d,]+\.?\d*)', text, re.IGNORECASE)
            if profit_match:
                cleaned = re.sub(r'[^\d.]', '', profit_match.group(1))
                if cleaned:
                    extracted.net_profit = to_field_extraction(float(cleaned))
        
        elif document_type == "cash_flow":
            operating_match = re.search(r'(?:operating\s+cash\s+flow|cash\s+flow\s+from\s+operations)[:\s]*[\$€£₹₽]?\s*([\d,]+\.?\d*)', text, re.IGNORECASE)
            if operating_match:
                cleaned = re.sub(r'[^\d.-]', '', operating_match.group(1))
                if cleaned:
                    extracted.operating_cash_flow = to_field_extraction(float(cleaned))
            
            investing_match = re.search(r'(?:investing\s+cash\s+flow|cash\s+flow\s+from\s+investing)[:\s]*[\$€£₹₽]?\s*([\d,]+\.?\d*)', text, re.IGNORECASE)
            if investing_match:
                cleaned = re.sub(r'[^\d.-]', '', investing_match.group(1))
                if cleaned:
                    extracted.investing_cash_flow = to_field_extraction(float(cleaned))
            
            financing_match = re.search(r'(?:financing\s+cash\s+flow|cash\s+flow\s+from\s+financing)[:\s]*[\$€£₹₽]?\s*([\d,]+\.?\d*)', text, re.IGNORECASE)
            if financing_match:
                cleaned = re.sub(r'[^\d.-]', '', financing_match.group(1))
                if cleaned:
                    extracted.financing_cash_flow = to_field_extraction(float(cleaned))
            
            net_match = re.search(r'(?:net\s+cash\s+flow|total\s+cash\s+flow)[:\s]*[\$€£₹₽]?\s*([\d,]+\.?\d*)', text, re.IGNORECASE)
            if net_match:
                cleaned = re.sub(r'[^\d.-]', '', net_match.group(1))
                if cleaned:
                    extracted.net_cash_flow = to_field_extraction(float(cleaned))
        
        return extracted
