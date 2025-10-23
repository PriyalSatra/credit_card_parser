"""PDF parser boilerplate.

Contains a simple parse_statement(file_path) function to start development.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Any
import re
import pdfplumber

def parse_statement(file_path: str) -> None:
    """Parse a PDF statement located at file_path (boilerplate).

    Currently this is a stub that prints a message. Replace with real parsing logic.
    """
    print('Parsing file...')

class StatementData(BaseModel):
    issuer: str
    card_last_4: str
    billing_cycle: str
    due_date: str
    total_balance: float
    transactions: list[dict]


class BaseParser(ABC):
    """Abstract base class for statement parsers."""

    @abstractmethod
    def parse(self, file_path: str) -> StatementData:
        """Parse the statement at file_path and return a StatementData instance.

        Implementations should open and parse the PDF and populate the model.
        """
        raise NotImplementedError


class ChaseParser(BaseParser):
    """Concrete parser for Chase statements (basic implementation).

    This implementation extracts all text from the PDF and uses simple
    regular expressions to locate standard English labels for the required
    fields. It's a best-effort heuristic and should be adapted to match
    the exact PDF layout you encounter.
    """

    def parse(self, file_path: str) -> StatementData:
        # Extract raw text from all pages
        pages_text: list[str] = []
        transactions = []
        
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                pages_text.append(page.extract_text() or "")
                
                # Extract transaction table from page 1 (index 0)
                if page_num == 0:
                    tables = page.extract_tables()
                    for table in tables:
                        # Look for tables with 3 columns (Date, Description, Amount)
                        if table and len(table) > 1:  # Has header + data rows
                            # Check if this looks like a transaction table
                            if len(table[0]) == 3:  # 3 columns
                                # Skip header row and process data rows
                                for row in table[1:]:
                                    if len(row) == 3 and row[0] and row[1] and row[2]:
                                        # Clean up the data
                                        date = str(row[0]).strip() if row[0] else ""
                                        description = str(row[1]).strip() if row[1] else ""
                                        amount = str(row[2]).strip() if row[2] else ""
                                        
                                        # Skip empty rows or header-like rows
                                        if date and description and amount:
                                            # Convert amount to float if possible
                                            try:
                                                # Remove currency symbols and commas
                                                amount_clean = amount.replace('$', '').replace(',', '').strip()
                                                amount_float = float(amount_clean)
                                            except (ValueError, AttributeError):
                                                amount_float = 0.0
                                            
                                            transactions.append({
                                                "date": date,
                                                "description": description,
                                                "amount": amount_float
                                            })
        
        raw = "\n".join(pages_text)

        # Attempt to extract card last 4 digits
        card_match = re.search(
            r'(?:Card(?: Number)?(?:\s*ending in|\s*ending with)?|Account Number|Acct\.?)[\s:]*\*?([0-9]{4})',
            raw,
            re.IGNORECASE,
        )
        card_last_4 = card_match.group(1) if card_match else ""

        # Billing cycle (e.g. "Billing cycle: 08/01/2025 - 08/31/2025" or similar)
        billing_match = re.search(r'Billing\s*Cycle[:\s]*([A-Za-z0-9/\- ,]+)', raw, re.IGNORECASE)
        billing_cycle = billing_match.group(1).strip() if billing_match else ""

        # Due date (accepts formats like "Due Date: August 25, 2025" or "Due Date: 08/25/2025")
        due_match = re.search(r'(?:Payment\s*)?Due\s*Date[:\s]*([A-Za-z0-9,/\- ]+)', raw, re.IGNORECASE)
        due_date = due_match.group(1).strip() if due_match else ""

        # Total / New balance (e.g. "New Balance: $1,234.56")
        balance_match = re.search(r'(?:New|Total|Current)?\s*Balance[:\s]*\$?([0-9,]+\.[0-9]{2})', raw, re.IGNORECASE)
        total_balance = 0.0
        if balance_match:
            bal_str = balance_match.group(1).replace(',', '')
            try:
                total_balance = float(bal_str)
            except ValueError:
                total_balance = 0.0

        # Build and return the model with extracted transactions
        return StatementData(
            issuer="Chase",
            card_last_4=card_last_4,
            billing_cycle=billing_cycle,
            due_date=due_date,
            total_balance=total_balance,
            transactions=transactions,
        )


if __name__ == "__main__":
    # Example usage of the ChaseParser
    parser = ChaseParser()
    
    # Parse a sample statement
    sample_file = "statements/chase_sample.pdf"
    try:
        statement_data = parser.parse(sample_file)
        print("Extracted Statement Data:")
        print(statement_data.model_dump_json(indent=4))
    except FileNotFoundError:
        print(f"Sample file '{sample_file}' not found. Please add a PDF file to the statements/ directory.")
    except Exception as e:
        print(f"Error parsing file: {e}")
