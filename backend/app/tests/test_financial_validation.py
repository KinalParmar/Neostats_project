import pytest
from app.financial_validation.validator import FinancialValidator
from decimal import Decimal


class TestFinancialValidator:
    """Tests for financial validation"""
    
    def test_invoice_validation_pass(self):
        """Test invoice validation with correct values"""
        extracted_data = {
            "fields": {
                "subtotal": {"value": "100.00"},
                "tax": {"value": "20.00"},
                "total": {"value": "120.00"}
            }
        }
        
        validations = FinancialValidator.validate(extracted_data, "invoice")
        
        assert len(validations) == 1
        assert validations[0]["status"] == "PASS"
        assert validations[0]["check_name"] == "Invoice Total Calculation"
    
    def test_invoice_validation_fail(self):
        """Test invoice validation with incorrect values"""
        extracted_data = {
            "fields": {
                "subtotal": {"value": "100.00"},
                "tax": {"value": "20.00"},
                "total": {"value": "150.00"}  # Wrong total
            }
        }
        
        validations = FinancialValidator.validate(extracted_data, "invoice")
        
        assert len(validations) == 1
        assert validations[0]["status"] == "FAIL"
    
    def test_invoice_validation_not_applicable(self):
        """Test invoice validation when fields are missing"""
        extracted_data = {
            "fields": {
                "subtotal": {"value": "100.00"}
                # Missing tax and total
            }
        }
        
        validations = FinancialValidator.validate(extracted_data, "invoice")
        
        assert len(validations) == 1
        assert validations[0]["status"] == "NOT_APPLICABLE"
    
    def test_balance_sheet_validation_pass(self):
        """Test balance sheet validation with correct values"""
        extracted_data = {
            "fields": {
                "total_assets": {"value": "1000.00"},
                "total_liabilities": {"value": "600.00"},
                "total_equity": {"value": "400.00"}
            }
        }
        
        validations = FinancialValidator.validate(extracted_data, "balance_sheet")
        
        assert len(validations) == 1
        assert validations[0]["status"] == "PASS"
    
    def test_parse_decimal_with_currency(self):
        """Test decimal parsing with currency symbols"""
        assert FinancialValidator._parse_decimal("$1,234.56") == Decimal("1234.56")
        assert FinancialValidator._parse_decimal("€1.234,56") is None  # Different format
        assert FinancialValidator._parse_decimal("1,234.56") == Decimal("1234.56")
        assert FinancialValidator._parse_decimal(None) is None
