from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator


def validate_afm_modulo11(afm: str) -> bool:
    """Υπολογισμός εγκυρότητας ελληνικού ΑΦΜ με βάση τον αλγόριθμο Modulo 11."""
    if not afm or len(afm) != 9 or not afm.isdigit():
        return False

    digits = [int(d) for d in afm]
    check_digit = digits[-1]
    
    multipliers = [256, 128, 64, 32, 16, 8, 4, 2]
    sum_products = sum(d * m for d, m in zip(digits[:8], multipliers))
    
    remainder = sum_products % 11
    expected_check_digit = 0 if remainder in (0, 10) else remainder
    
    return check_digit == expected_check_digit


class FinancialDetails(BaseModel):
    net_amount: float = Field(..., description="Το καθαρό ποσό προ ΦΠΑ")
    vat_rate: float = Field(..., description="Ο συντελεστής ΦΠΑ (π.χ. 0.24)")
    total_amount: float = Field(..., description="Το τελικό ποσό συμπεριλαμβανομένου ΦΠΑ")

    @model_validator(mode="after")
    def verify_financial_integrity(self):
        expected_total = round(self.net_amount * (1.0 + self.vat_rate), 2)
        # Επιτρέπουμε απόκλιση έως 1 ευρώ λόγω στρογγυλοποιήσεων σε κρατήσεις/κείμενα
        if abs(expected_total - self.total_amount) > 1.0:
            raise ValueError(
                f"Μαθηματικό λάθος: net ({self.net_amount}) + vat ({self.vat_rate}) "
                f"βγάζει {expected_total}, αλλά δηλώθηκε {self.total_amount}!"
            )
        return self


class ContractSchema(BaseModel):
    document_title: str = Field(..., description="Ο τίτλος ή το θέμα του εγγράφου")
    contractor_name: Optional[str] = Field(
        None, description="Η επωνυμία του αναδόχου ή 'ΑΝΕΥ ΑΝΑΔΟΧΟΥ' αν είναι πρόσκληση/διακήρυξη"
    )
    tax_id: Optional[str] = Field(
        None, description="Το 9ψήφιο ΑΦΜ του αναδόχου. Αν δεν υπάρχει ανάδοχος, παραμένει null."
    )
    financials: FinancialDetails = Field(..., description="Οικονομικά στοιχεία της πράξης")

    @field_validator("tax_id")
    @classmethod
    def check_afm(cls, v: Optional[str]):
        if v is None or v == "" or v == "000000000" or "ΑΝΕΥ" in str(v).upper():
            return None
        clean_v = v.strip()
        if not validate_afm_modulo11(clean_v):
            raise ValueError(f"Μη έγκυρο ΑΦΜ: '{v}'. Αποτυχία αλγορίθμου Modulo 11.")
        return clean_v