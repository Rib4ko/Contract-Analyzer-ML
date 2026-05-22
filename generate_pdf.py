from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=12)

contract_text = """
MASTER SERVICES AGREEMENT

This Master Services Agreement is entered into by and between Acme Corp ("Client") and Globex Solutions ("Vendor").

1. SERVICES PROVIDED
Vendor agrees to provide software development and consulting services as outlined in the attached statements of work.

2. PAYMENT TERMS
Client agrees to pay Vendor within 90 days of receiving an invoice. If payment is delayed, no penalty will apply for the first 30 days of delay. Payments may be made via check or wire transfer.

3. DURATION AND TERM
This agreement is valid for a period of three (3) years. It will automatically renew for successive one-year periods unless either party provides 30 days written notice of termination.

4. CONFIDENTIALITY
Vendor and Client agree to keep all shared information confidential for a period of 2 years after the contract ends.

5. INSURANCE REQUIREMENTS
Vendor will maintain general liability insurance with a minimum limit of $500,000. 

6. GOVERNING LAW
This agreement shall be governed by the laws of the State of California. Any disputes shall be handled in San Francisco courts.

7. DEFINITIONS
The term "Confidential Information" means any data or information that is proprietary to the disclosing party and not generally known to the public. "Deliverables" refers to the software code and documentation produced by the Vendor. Note that "Intellectual Property" is not defined herein.

IN WITNESS WHEREOF, the parties have executed this Agreement.
"""

for line in contract_text.split('\n'):
    pdf.cell(200, 10, txt=line, ln=1)

pdf.output("acme_vendor_contract.pdf")
print("PDF generated successfully.")
