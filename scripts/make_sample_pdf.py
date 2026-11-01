"""Generate data/pdfs/sample_company_handbook.pdf so you can test without your own PDFs.

    python -m scripts.make_sample_pdf     (needs reportlab: pip install -r requirements-dev.txt)
"""
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

PAGES = {
    "1. Leave Policy": [
        "Full-time employees receive 18 days of paid annual leave per calendar year. "
        "Leave accrues monthly at 1.5 days per month and up to 5 unused days may be carried "
        "over into the next year. Carried-over days expire on 31 March.",
        "Sick leave is separate from annual leave. Employees may take up to 14 days of paid "
        "sick leave per year. A medical certificate is required for absences longer than two "
        "consecutive days.",
        "Parental leave: primary caregivers receive 16 weeks of fully paid leave, and secondary "
        "caregivers receive 4 weeks of fully paid leave, to be taken within 12 months of birth or adoption.",
    ],
    "2. Remote Work": [
        "Employees may work remotely up to three days per week with manager approval. "
        "Core collaboration hours are 10:00 to 16:00 Singapore time, during which staff "
        "should be reachable on chat.",
        "The company provides a one-time home office allowance of SGD 600 for a desk, chair "
        "or monitor. Receipts must be submitted through the expense portal within 30 days.",
    ],
    "3. Expenses and Travel": [
        "Business travel must be booked through the approved travel agency. Economy class is "
        "standard for flights under 6 hours; premium economy is allowed for longer flights.",
        "The daily meal allowance while travelling is SGD 80. Expense claims must be submitted "
        "within 60 days of the expense date and require itemised receipts for amounts over SGD 25.",
        "Hotel stays are limited to SGD 250 per night in Singapore and SGD 300 per night overseas.",
    ],
    "4. IT and Security": [
        "Passwords must be at least 14 characters and multi-factor authentication is mandatory "
        "for all company accounts. Lost or stolen laptops must be reported to the IT helpdesk "
        "within 24 hours by emailing helpdesk@example.com.",
        "Company data may only be stored on approved systems. Personal USB drives are not "
        "permitted for storing customer data.",
    ],
}


def main() -> None:
    out = Path("data/pdfs/sample_company_handbook.pdf")
    out.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    story = [Paragraph("Example Corp Employee Handbook (Sample)", styles["Title"]), Spacer(1, 12)]
    for n, (title, paras) in enumerate(PAGES.items()):
        if n:
            story.append(PageBreak())
        story.append(Paragraph(title, styles["Heading1"]))
        for p in paras:
            story += [Paragraph(p, styles["BodyText"]), Spacer(1, 8)]
    SimpleDocTemplate(str(out), pagesize=A4).build(story)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
