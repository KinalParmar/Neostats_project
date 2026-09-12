from typing import List, Dict, Any
import logging
from app.schemas.document import Validation, ValidationCheck, ExtractedData

logger = logging.getLogger(__name__)


class FinancialValidationService:
    """Service for validating financial calculations"""
    
    def validate(self, extracted_data: ExtractedData, document_type: str) -> Validation:
        """
        Perform financial validation based on document type
        """
        checks = []
        issues = []
        
        if document_type == "invoice":
            checks = self._validate_invoice(extracted_data)
        elif document_type == "balance_sheet":
            checks = self._validate_balance_sheet(extracted_data)
        elif document_type == "profit_loss":
            checks = self._validate_profit_loss(extracted_data)
        elif document_type == "cash_flow":
            checks = self._validate_cash_flow(extracted_data)
        
        # Determine overall status
        failed_checks = [c for c in checks if c.status == "FAIL"]
        if failed_checks:
            overall_status = "FAIL"
            issues = [f"Check '{c.name}' failed" for c in failed_checks]
        elif any(c.status == "NOT_APPLICABLE" for c in checks):
            overall_status = "PARTIAL"
        else:
            overall_status = "PASS"
        
        return Validation(
            checks=checks,
            overall_status=overall_status,
            issues=issues
        )
    
    def _validate_invoice(self, data: ExtractedData) -> List[ValidationCheck]:
        """Validate invoice calculations"""
        checks = []
        
        # Invoice total check: subtotal + tax - discount = total
        if data.subtotal and data.tax_amount and data.total_amount:
            subtotal = self._extract_numeric_value(data.subtotal.value)
            tax = self._extract_numeric_value(data.tax_amount.value)
            discount = self._extract_numeric_value(data.discount.value) if data.discount else 0
            total = self._extract_numeric_value(data.total_amount.value)
            
            calculated = subtotal + tax - discount
            variance = abs(calculated - total)
            status = "PASS" if variance < 0.01 else "FAIL"
            
            checks.append(ValidationCheck(
                name="invoice_total_check",
                formula="subtotal + tax_amount - discount",
                operands={"subtotal": subtotal, "tax_amount": tax, "discount": discount},
                calculated_value=calculated,
                reported_value=total,
                variance=variance,
                status=status
            ))
        else:
            checks.append(ValidationCheck(
                name="invoice_total_check",
                formula="subtotal + tax_amount - discount",
                operands={},
                calculated_value=None,
                reported_value=None,
                variance=None,
                status="NOT_APPLICABLE"
            ))
        
        # Line items total check
        if data.line_items:
            line_items_total = sum(item.amount for item in data.line_items)
            if data.subtotal:
                subtotal = self._extract_numeric_value(data.subtotal.value)
                variance = abs(line_items_total - subtotal)
                status = "PASS" if variance < 0.01 else "FAIL"
                
                checks.append(ValidationCheck(
                    name="line_items_total_check",
                    formula="sum(line_items.amount)",
                    operands={"line_items_total": line_items_total},
                    calculated_value=line_items_total,
                    reported_value=subtotal,
                    variance=variance,
                    status=status
                ))
        
        return checks
    
    def _validate_balance_sheet(self, data: ExtractedData) -> List[ValidationCheck]:
        """Validate balance sheet equation: Assets = Liabilities + Equity"""
        checks = []
        
        if data.total_assets and data.total_liabilities and data.total_equity:
            assets = self._extract_numeric_value(data.total_assets.value)
            liabilities = self._extract_numeric_value(data.total_liabilities.value)
            equity = self._extract_numeric_value(data.total_equity.value)
            
            calculated = liabilities + equity
            variance = abs(calculated - assets)
            status = "PASS" if variance < 0.01 else "FAIL"
            
            checks.append(ValidationCheck(
                name="balance_sheet_equation",
                formula="total_liabilities + total_equity",
                operands={"total_liabilities": liabilities, "total_equity": equity},
                calculated_value=calculated,
                reported_value=assets,
                variance=variance,
                status=status
            ))
        else:
            checks.append(ValidationCheck(
                name="balance_sheet_equation",
                formula="total_liabilities + total_equity",
                operands={},
                calculated_value=None,
                reported_value=None,
                variance=None,
                status="NOT_APPLICABLE"
            ))
        
        return checks
    
    def _validate_profit_loss(self, data: ExtractedData) -> List[ValidationCheck]:
        """Validate profit & loss: Revenue - Expenses = Net Profit"""
        checks = []
        
        if data.revenue and data.expenses and data.net_profit:
            revenue = self._extract_numeric_value(data.revenue.value)
            expenses = self._extract_numeric_value(data.expenses.value)
            net_profit = self._extract_numeric_value(data.net_profit.value)
            
            calculated = revenue - expenses
            variance = abs(calculated - net_profit)
            status = "PASS" if variance < 0.01 else "FAIL"
            
            checks.append(ValidationCheck(
                name="profit_loss_equation",
                formula="revenue - expenses",
                operands={"revenue": revenue, "expenses": expenses},
                calculated_value=calculated,
                reported_value=net_profit,
                variance=variance,
                status=status
            ))
        else:
            checks.append(ValidationCheck(
                name="profit_loss_equation",
                formula="revenue - expenses",
                operands={},
                calculated_value=None,
                reported_value=None,
                variance=None,
                status="NOT_APPLICABLE"
            ))
        
        return checks
    
    def _validate_cash_flow(self, data: ExtractedData) -> List[ValidationCheck]:
        """Validate cash flow: Operating + Investing + Financing = Net Cash Flow"""
        checks = []
        
        if data.operating_cash_flow and data.investing_cash_flow and data.financing_cash_flow and data.net_cash_flow:
            operating = self._extract_numeric_value(data.operating_cash_flow.value)
            investing = self._extract_numeric_value(data.investing_cash_flow.value)
            financing = self._extract_numeric_value(data.financing_cash_flow.value)
            net = self._extract_numeric_value(data.net_cash_flow.value)
            
            calculated = operating + investing + financing
            variance = abs(calculated - net)
            status = "PASS" if variance < 0.01 else "FAIL"
            
            checks.append(ValidationCheck(
                name="cash_flow_equation",
                formula="operating_cash_flow + investing_cash_flow + financing_cash_flow",
                operands={"operating_cash_flow": operating, "investing_cash_flow": investing, "financing_cash_flow": financing},
                calculated_value=calculated,
                reported_value=net,
                variance=variance,
                status=status
            ))
        else:
            checks.append(ValidationCheck(
                name="cash_flow_equation",
                formula="operating_cash_flow + investing_cash_flow + financing_cash_flow",
                operands={},
                calculated_value=None,
                reported_value=None,
                variance=None,
                status="NOT_APPLICABLE"
            ))
        
        return checks
    
    def _extract_numeric_value(self, value: Any) -> float:
        """Extract numeric value from various formats"""
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            # Remove currency symbols and commas
            cleaned = value.replace('$', '').replace('€', '').replace('£', '').replace(',', '').strip()
            try:
                return float(cleaned)
            except ValueError:
                return 0.0
        return 0.0
