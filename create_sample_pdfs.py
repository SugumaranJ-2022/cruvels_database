"""
Script to create sample legal PDF documents for testing the Task A pipeline.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def create_sample_judgment(file_path: str) -> None:
    c = canvas.Canvas(file_path, pagesize=letter)
    
    # Page 1
    c.drawString(100, 750, "HIGH COURT OF DELHI")
    c.drawString(100, 735, "Page 1 of 2")
    c.drawString(100, 700, "IN THE HIGH COURT OF DELHI AT NEW DELHI")
    c.drawString(100, 680, "Civil Appeal No. 452O/2024")
    c.drawString(100, 660, "Date of Decision: 15-03-2024")
    c.drawString(100, 630, "ABC Pvt Ltd ... Appellant")
    c.drawString(100, 610, "VERSUS")
    c.drawString(100, 590, "XYZ Corporation ... Respondent")
    c.drawString(100, 550, "FACTS OF THE CASE:")
    c.drawString(100, 530, "1. The appellant entered into a commercial contract dated 12-01-2022.")
    c.drawString(100, 510, "2. A breach occurred under Section 7l of the Indian Contract Act, 1872.")
    c.drawString(100, 480, "ISSUES:")
    c.drawString(100, 460, "1. Whether Section 73 of the Contract Act applies to liquidated damages?")
    c.drawString(100, 100, "Confidential Document")
    c.showPage()
    
    # Page 2
    c.drawString(100, 750, "HIGH COURT OF DELHI")
    c.drawString(100, 735, "Page 2 of 2")
    c.drawString(100, 700, "REASONING & DECISION:")
    c.drawString(100, 680, "The Court analyzed the provisions of Section 73 and Section 74.")
    c.drawString(100, 660, "Proof of actual damage is necessary unless liquidated damages represent genuine pre-estimate.")
    c.drawString(100, 630, "RATIO DECIDENDI:")
    c.drawString(100, 610, "Section 73 mandates proof of loss before claiming compensation for breach.")
    c.drawString(100, 580, "DECISION:")
    c.drawString(100, 560, "Appeal is allowed. Costs awarded to appellant.")
    c.drawString(100, 100, "Confidential Document")
    c.save()


def main() -> None:
    os.makedirs("sample_docs", exist_ok=True)
    create_sample_judgment("sample_docs/judgment_sample.pdf")
    print("Created sample PDF in sample_docs/judgment_sample.pdf")


if __name__ == "__main__":
    main()
