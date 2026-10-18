from pathlib import Path
from pypdf import PdfReader

pdf_path = Path("data/raw/doc_2_digital.pdf")
reader = PdfReader(str(pdf_path))

full_text = "\n".join([page.extract_text() or "" for page in reader.pages])

print(f"Συνολικό μήκος κειμένου: {len(full_text)} χαρακτήρες\n")

# Αναζήτηση παραγράφων με οικονομικά στοιχεία ή αναδόχους
keywords = ["μίσθωμα", "αποζημίωση", "ευρώ", "ανάδοχ", "δρομολόγ"]

for kw in keywords:
  count = full_text.lower().count(kw)
  print(f"Η λέξη-κλειδί '{kw}' εντοπίστηκε {count} φορές.")

print("\n--- ΕΝΔΕΙΚΤΙΚΟ ΑΠΟΣΠΑΣΜΑ ΟΙΚΟΝΟΜΙΚΩΝ/ΟΡΩΝ ---")
# Εκτύπωση αποσπασμάτων γύρω από ποσά ή ευρώ
for line in full_text.split("\n"):
  if any(k in line.lower() for k in ["ευρώ", "€", "μίσθωμα"]):
    print(f">> {line.strip()}")