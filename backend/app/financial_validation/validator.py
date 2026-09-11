from typing import Dict, Any, List
from decimal import Decimal, InvalidOperation


class FinancialValidator:
    """Validates financial relationships in extracted data"""
    
    NUMERICAL_TOLERANCE = Decimal('0.01')  # 2 decimal places tolerance
    
    @staticmethod
    def validate(extracted_data: Dict[str, Any], document_type: str) -> List[Dict[str, Any]]:
        """
        Run financial validations based on document type.
        Returns list of validation results.
        """
        validations = []
        
        if document_type == "invoice":
            validations.extend(FinancialValidator._validate_invoice(extracted_data))
        elif document_type == "balance_sheet":
            validations.extend(FinancialValidator._validate_balance_sheet(extracted_data))
        elif document_type == "profit_loss":
            validations.extend(FinancialValidator._validate_profit_loss(extracted_data))
        elif document_type == "cash_flow":
            validations.extend(FinancialValidator._validate_cash_flow(extracted_data))
        
        return validations
    
    @staticmethod
    def _validate_invoice(extracted_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate invoice: subtotal + tax = total"""
        validations = []
        fields = extracted_data.get("fields", {})
        
        subtotal = FinancialValidator._parse_decimal(fields.get("subtotal", {}).get("value"))
        tax = FinancialValidator._parse_decimal(fields.get("tax", {}).get("value"))
        total = FinancialValidator._parse_decimal(fields.get("total", {}).get("value"))
        
        if subtotal is not None and tax is not None and total is not None:
            calculated_total = subtotal + tax
            variance = abs(calculated_total - total)
            
            status = "PASS" if variance <= FinancialValidator.NUMERICAL_TOLERANCE else "FAIL"
            
            validations.append({
                "check_name": "Invoice Total Calculation",
                "formula": "subtotal + tax = total",
                "inputs": {
                    "subtotal": str(subtotal),
                    "tax": str(tax),
                    "reported_total": str(total)
                },
                "calculated_value": str(calculated_total),
                "reported_value": str(total),
                "variance": str(variance),
                "status": status
            })
        else:
            validations.append({
                "check_name": "Invoice Total Calculation",
                "formula": "subtotal + tax = total",
                "inputs": {},
                "calculated_value": None,
                "reported_value": None,
                "variance": None,
                "status": "NOT_APPLICABLE"
            })
        
        return validations
    
    @staticmethod
    def _validate_balance_sheet(extracted_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate balance sheet: Assets = Liabilities + Equity"""
        validations = []
        fields = extracted_data.get("fields", {})
        
        total_assets = FinancialValidator._parse_decimal(fields.get("total_assets", {}).get("value"))
        total_liabilities = FinancialValidator._parse_decimal(fields.get("total_liabilities", {}).get("value"))
        total_equity = FinancialValidator._parse_decimal(fields.get("total_equity", {}).get("value"))
        
        if total_assets is not None and total_liabilities is not None and total_equity is not None:
            calculated_liabilities_plus_equity = total_liabilities + total_equity
            variance = abs(total_assets - calculated_liabilities_plus_equity)
            
            status = "PASS" if variance <= FinancialValidator.NUMERICAL_TOLERANCE else "FAIL"
            
            validations.append({
                "check_name": "Balance Sheet Equation",
                "formula": "Assets = Liabilities + Equity",
                "inputs": {
                    "total_assets": str(total_assets),
                    "total_liabilities": str(total_liabilities),
                    "total_equity": str(total_equity)
                },
                "calculated_value": str(calculated_liabilities_plus_equity),
                "reported_value": str(total_assets),
                "variance": str(variance),
                "status": status
            })
        else:
            validations.append({
                "check_name": "Balance Sheet Equation",
                "formula": "Assets = Liabilities + Equity",
                "inputs": {},
                "calculated_value": None,
                "reported_value": None,
                "variance": None,
                "status": "NOT_APPLICABLE"
            })
        
        return validations
    
    @staticmethod
    def _validate_profit_loss(extracted_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate profit & loss: Revenue - Expenses = Net Profit"""
        validations = []
        fields = extracted_data.get("fields", {})
        
        total_revenue = FinancialValidator._parse_decimal(fields.get("total_revenue", {}).get("value"))
        total_expenses = FinancialValidator._parse_decimal(fields.get("total_expenses", {}).get("value"))
        net_profit = FinancialValidator._parse_decimal(fields.get("net_profit", {}).get("value"))
        
        if total_revenue is not None and total_expenses is not None and net_profit is not None:
            calculated_profit = total_revenue - total_expenses
            variance = abs(calculated_profit - net_profit)
            
            status = "PASS" if variance <= FinancialValidator.NUMERICAL_TOLERANCE else "FAIL"
            
            validations.append({
                "check_name": "Profit & Loss Calculation",
                "formula": "Revenue - Expenses = Net Profit",
                "inputs": {
                    "total_revenue": str(total_revenue),
                    "total_expenses": str(total_expenses),
                    "reported_net_profit": str(net_profit)
                },
                "calculated_value": str(calculated_profit),
                "reported_value": str(net_profit),
                "variance": str(variance),
                "status": status
            })
        else:
            validations.append({
                "check_name": "Profit & Loss Calculation",
                "formula": "Revenue - Expenses = Net Profit",
                "inputs": {},
                "calculated_value": None,
                "reported_value": None,
                "variance": None,
                "status": "NOT_APPLICABLE"
            })
        
        return validations
    
    @staticmethod
    def _validate_cash_flow(extracted_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate cash flow: Opening Balance + Net Change = Closing Balance"""
        validations = []
        fields = extracted_data.get("fields", {})
        
        opening_balance = FinancialValidator._parse_decimal(fields.get("opening_balance", {}).get("value"))
        net_change = FinancialValidator._parse_decimal(fields.get("net_cash_change", {}).get("value"))
        closing_balance = FinancialValidator._parse_decimal(fields.get("closing_balance", {}).get("value"))
        
        if opening_balance is not None and net_change is not None and closing_balance is not None:
            calculated_closing = opening_balance + net_change
            variance = abs(calculated_closing - closing_balance)
            
            status = "PASS" if variance <= FinancialValidator.NUMERICAL_TOLERANCE else "FAIL"
            
            validations.append({
                "check_name": "Cash Flow Reconciliation",
                "formula": "Opening Balance + Net Change = Closing Balance",
                "inputs": {
                    "opening_balance": str(opening_balance),
                    "net_change": str(net_change),
                    "reported_closing_balance": str(closing_balance)
                },
                "calculated_value": str(calculated_closing),
                "reported_value": str(closing_balance),
                "variance": str(variance),
                "status": status
            })
        else:
            validations.append({
                "check_name": "Cash Flow Reconciliation",
                "formula": "Opening Balance + Net Change = Closing Balance",
                "inputs": {},
                "calculated_value": None,
                "reported_value": None,
                "variance": None,
                "status": "NOT_APPLICABLE"
            })
        
        return validations
    
    @staticmethod
    def _parse_decimal(value: Any) -> Decimal:
        """Parse a value to Decimal, return None if invalid"""
        if value is None:
            return None
        try:
            # Handle string values with currency symbols, commas, etc.
            if isinstance(value, str):
                # Remove currency symbols and commas
                cleaned = value.strip()
                cleaned = cleaned.replace('$', '').replace('€', '').replace('£', '').replace(',', '')
                cleaned = cleaned.strip()
                if not cleaned:
                    return None
                return Decimal(cleaned)
            return Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError):
            return None
