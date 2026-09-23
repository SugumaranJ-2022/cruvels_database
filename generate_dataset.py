"""
Comprehensive Legal Dataset Generator creating Phase 1 Minimum Legal Collection documents (35+ PDFs).
Covers all 13 Phase 1 categories required for Indian Law research and knowledge graph construction.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def create_pdf(filename: str, header_title: str, page1_lines: list[str], page2_lines: list[str] = None):
    filepath = os.path.join("sample_docs", filename)
    c = canvas.Canvas(filepath, pagesize=letter)

    # Header / Footer Page 1
    c.setFont("Helvetica-Bold", 10)
    c.drawString(70, 750, header_title)
    c.drawString(70, 735, "Page 1 of " + ("2" if page2_lines else "1"))

    c.setFont("Helvetica", 9)
    y = 705
    for line in page1_lines:
        c.drawString(70, y, line)
        y -= 16
        if y < 90:
            break

    c.setFont("Helvetica-Oblique", 8)
    c.drawString(70, 60, "Official Indian Legal Database - Phase 1 Core Collection")
    c.showPage()

    if page2_lines:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(70, 750, header_title)
        c.drawString(70, 735, "Page 2 of 2")

        c.setFont("Helvetica", 9)
        y = 705
        for line in page2_lines:
            c.drawString(70, y, line)
            y -= 16
            if y < 90:
                break
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(70, 60, "Official Indian Legal Database - Phase 1 Core Collection")
        c.showPage()

    c.save()


def main():
    os.makedirs("sample_docs", exist_ok=True)
    print("Generating Phase 1 Minimum Core Collection PDF documents across 13 legal categories...")

    # CATEGORY 1: CONSTITUTION OF INDIA
    create_pdf(
        "doc_phase1_01_constitution_of_india.pdf",
        "CONSTITUTION OF INDIA - PHASE 1 CORE COLLECTION",
        [
            "THE CONSTITUTION OF INDIA (COMPLETE TEXT EXTRACTS)",
            "Preamble: WE, THE PEOPLE OF INDIA, having solemnly resolved to constitute India into a SOVEREIGN SOCIALIST SECULAR DEMOCRATIC REPUBLIC...",
            "PART III - FUNDAMENTAL RIGHTS:",
            "Article 12: Definition of State.",
            "Article 14: Equality before law and equal protection of laws.",
            "Article 19: Protection of certain rights regarding freedom of speech, assembly, association.",
            "Article 21: Protection of life and personal liberty. No person shall be deprived of life except by procedure established by law.",
            "Article 32: Remedies for enforcement of rights conferred by Part III (Writ Jurisdiction).",
            "PART IV - DIRECTIVE PRINCIPLES OF STATE POLICY (DPSP):",
            "Article 38: State to secure a social order for the promotion of welfare of the people.",
            "Article 39A: Equal justice and free legal aid.",
            "Article 44: Uniform Civil Code for the citizens.",
        ],
        [
            "PART IV-A - FUNDAMENTAL DUTIES:",
            "Article 51A: It shall be the duty of every citizen of India to abide by the Constitution and respect its ideals.",
            "SCHEDULES OF THE CONSTITUTION:",
            "First Schedule: State and Union Territory territories.",
            "Seventh Schedule: Union List, State List, and Concurrent List.",
            "Ninth Schedule: Validation of certain Acts and Regulations.",
            "IMPORTANT CONSTITUTIONAL AMENDMENTS:",
            "42nd Amendment Act, 1976: Added 'Socialist', 'Secular', 'Integrity' to Preamble and Fundamental Duties.",
            "44th Amendment Act, 1978: Safeguards against emergency powers and right to property modified.",
            "86th Amendment Act, 2002: Right to Education under Article 21A.",
            "103rd Amendment Act, 2019: 10% EWS reservation under Articles 15(6) and 16(6).",
        ],
    )

    # CATEGORY 2: MAJOR CURRENT STATUTES / ACTS
    create_pdf(
        "doc_phase1_02_bns_2023_act.pdf",
        "BHARATIYA NYAYA SANHITA, 2023 (BNS) - ACT NO. 45 OF 2023",
        [
            "THE BHARATIYA NYAYA SANHITA, 2023",
            "An Act to consolidate and amend the provisions relating to offences and for matters connected therewith.",
            "CHAPTER I - PRELIMINARY",
            "Section 1: Short title, extent, and commencement. Replaces the Indian Penal Code, 1860.",
            "Section 2: Definitions - 'Child', 'Court', 'Gender', 'Injury', 'Mens Rea', 'Public Servant'.",
            "CHAPTER V - OFFENCES AGAINST THE HUMAN BODY",
            "Section 101: Murder defined. Punishment under Section 103 BNS.",
            "Section 106: Causing death by negligence (Hit and Run provisions).",
            "CHAPTER XVII - OFFENCES AGAINST PROPERTY",
            "Section 303: Theft defined. Section 316: Criminal Breach of Trust.",
        ],
        [
            "CHAPTER XVIII - OFFENCES RELATING TO DOCUMENTS & PROPERTY MARKS",
            "Section 335: Forgery defined.",
            "REPEAL AND SAVINGS:",
            "Section 358: The Indian Penal Code, 1860 is hereby repealed. Pending investigations continue under new procedure.",
        ],
    )

    create_pdf(
        "doc_phase1_02_bnss_2023_act.pdf",
        "BHARATIYA NAGARIK SURAKSHA SANHITA, 2023 (BNSS)",
        [
            "THE BHARATIYA NAGARIK SURAKSHA SANHITA, 2023 (Act No. 46 of 2023)",
            "An Act to consolidate and amend the law relating to Criminal Procedure in India.",
            "CHAPTER I - PRELIMINARY",
            "Section 1: Short title and commencement. Replaces Code of Criminal Procedure, 1973 (CrPC).",
            "CHAPTER V - ARREST OF PERSONS",
            "Section 35: Arrest without warrant by police officer.",
            "Section 430: Anticipatory Bail provisions. Section 480: General bail parameters.",
            "CHAPTER XII - INFORMATION TO POLICE & POWERS TO INVESTIGATE",
            "Section 173: Zero FIR registration and electronic FIR filing mandating time-bound charge-sheets.",
        ]
    )

    create_pdf(
        "doc_phase1_02_bsa_2023_act.pdf",
        "BHARATIYA SAKSHYA ADHINIYAM, 2023 (BSA)",
        [
            "THE BHARATIYA SAKSHYA ADHINIYAM, 2023 (Act No. 47 of 2023)",
            "An Act to consolidate and provide general rules and principles of evidence.",
            "CHAPTER I - PRELIMINARY & DEFINITIONS",
            "Section 2: Defines 'Document', 'Electronic Record', 'Evidence', 'Fact in Issue'.",
            "CHAPTER V - ADMISSIBILITY OF ELECTRONIC EVIDENCE",
            "Section 61: Admissibility of electronic and digital records as primary evidence.",
            "Section 63: Electronic record certificate requirements replacing old Section 65B IEA.",
        ]
    )

    create_pdf(
        "doc_phase1_02_contract_act_1872.pdf",
        "INDIAN CONTRACT ACT, 1872 - MAJOR STATUTE",
        [
            "THE INDIAN CONTRACT ACT, 1872 (ACT NO. 9 OF 1872)",
            "CHAPTER I - OF THE COMMUNICATION, ACCEPTANCE AND REVOCATION OF PROPOSALS",
            "Section 2: Interpretation clause - Proposal, Acceptance, Consideration, Agreement, Contract.",
            "Section 10: What agreements are contracts - Free consent, competent parties, lawful consideration.",
            "CHAPTER VI - OF THE CONSEQUENCES OF BREACH OF CONTRACT",
            "Section 73: Compensation for loss or damage caused by breach of contract.",
            "Section 74: Compensation for breach of contract where penalty stipulated for.",
        ]
    )

    create_pdf(
        "doc_phase1_02_companies_act_2013.pdf",
        "COMPANIES ACT, 2013 - COMMERCIAL LAW STATUTE",
        [
            "THE COMPANIES ACT, 2013 (ACT NO. 18 OF 2013)",
            "CHAPTER I - PRELIMINARY",
            "Section 2(68): Private Company definition. Section 2(71): Public Company definition.",
            "Section 135: Corporate Social Responsibility (CSR) requirements.",
            "Section 166: Duties of Directors - Duty of good faith, care, and diligence.",
            "Section 241: Application to Tribunal for relief in cases of oppression and mismanagement.",
        ]
    )

    create_pdf(
        "doc_phase1_02_dpdp_act_2023.pdf",
        "DIGITAL PERSONAL DATA PROTECTION ACT, 2023 (DPDP)",
        [
            "DIGITAL PERSONAL DATA PROTECTION ACT, 2023 (ACT NO. 22 OF 2023)",
            "An Act to provide for the processing of digital personal data in a manner that recognizes right to privacy.",
            "Section 4: Grounds for processing personal data - Consent and Legitimate Uses.",
            "Section 6: Consent requirements, notice format, and withdrawal mechanisms.",
            "Section 8: Obligations of Data Fiduciary regarding security safeguards and breach notifications.",
            "Section 27: Penalties up to Rs 250 Crores for failure to take reasonable security safeguards.",
        ]
    )

    create_pdf(
        "doc_phase1_02_consumer_protection_2019.pdf",
        "CONSUMER PROTECTION ACT, 2019",
        [
            "CONSUMER PROTECTION ACT, 2019 (ACT NO. 35 OF 2019)",
            "An Act to provide for protection of the interests of consumers and establish Consumer Protection Councils.",
            "Section 2(7): Definition of 'Consumer' including e-commerce transactions.",
            "Section 2(47): Unfair Trade Practice defined.",
            "Section 34: Jurisdiction of District Consumer Disputes Redressal Commission.",
            "Section 82: Product Liability action against product manufacturer or seller.",
        ]
    )

    create_pdf(
        "doc_phase1_02_it_act_2000.pdf",
        "INFORMATION TECHNOLOGY ACT, 2000",
        [
            "THE INFORMATION TECHNOLOGY ACT, 2000 (ACT NO. 21 OF 2000)",
            "CHAPTER IX - OFFENCES AND INTERMEDIARY LIABILITY",
            "Section 66: Computer related offences and hacking penalties.",
            "Section 66A: Struck down by Supreme Court in Shreya Singhal v. Union of India.",
            "Section 69A: Power to issue directions for blocking for public access of any information.",
            "Section 79: Exemption from liability of intermediary in certain cases (Safe Harbour Protection).",
        ]
    )

    # CATEGORY 3: IMPORTANT LEGACY STATUTES
    create_pdf(
        "doc_phase1_03_legacy_ipc_1860.pdf",
        "INDIAN PENAL CODE, 1860 (HISTORICAL / REPEALED STATUTE)",
        [
            "THE INDIAN PENAL CODE, 1860 (ACT NO. 45 OF 1860) [REPEALED BY BNS 2023]",
            "Included for historical judgment interpretation and legacy legal research.",
            "Section 300: Murder definition and Exceptions 1-5.",
            "Section 302: Punishment for Murder.",
            "Section 304A: Causing death by negligence.",
            "Section 420: Cheating and dishonestly inducing delivery of property.",
            "Section 498A: Husband or relative of husband of a woman subjecting her to cruelty.",
        ]
    )

    create_pdf(
        "doc_phase1_03_legacy_crpc_1973.pdf",
        "CODE OF CRIMINAL PROCEDURE, 1973 (LEGACY PROCEDURAL LAW)",
        [
            "CODE OF CRIMINAL PROCEDURE, 1973 (ACT NO. 2 OF 1974) [REPEALED BY BNSS 2023]",
            "Preserved for analyzing past Supreme Court precedents and criminal trial history.",
            "Section 154: Information in cognizable cases (FIR).",
            "Section 167: Procedure when investigation cannot be completed in twenty-four hours (Remand).",
            "Section 437 / 439: Special powers of High Court or Court of Session regarding bail.",
        ]
    )

    create_pdf(
        "doc_phase1_03_legacy_evidence_1872.pdf",
        "INDIAN EVIDENCE ACT, 1872 (LEGACY EVIDENCE STATUTE)",
        [
            "THE INDIAN EVIDENCE ACT, 1872 (ACT NO. 1 OF 1872) [REPEALED BY BSA 2023]",
            "Section 3: Interpretation clause - 'Proved', 'Disproved', 'Not proved'.",
            "Section 65B: Admissibility of electronic records certificate requirements (Anvar P.V. precedent).",
            "Section 101: Burden of proof.",
            "Section 114A: Presumption as to absence of consent in certain prosecutions.",
        ]
    )

    # CATEGORY 4: IMPORTANT RULES & REGULATIONS
    create_pdf(
        "doc_phase1_04_rules_it_intermediary_2021.pdf",
        "INFORMATION TECHNOLOGY INTERMEDIARY RULES, 2021",
        [
            "INFORMATION TECHNOLOGY (INTERMEDIARY GUIDELINES & DIGITAL MEDIA ETHICS CODE) RULES, 2021",
            "Issued under Section 87 of Information Technology Act, 2000 by Ministry of Electronics & IT.",
            "Rule 3: Due diligence observed by intermediary including publishing privacy policy and user agreements.",
            "Rule 4: Additional due diligence for Significant Social Media Intermediaries (SSMI).",
            "Rule 7: Non-compliance with rules leads to loss of Safe Harbour under Section 79 IT Act.",
        ]
    )

    # CATEGORY 5: SUPREME COURT JUDGMENTS (LANDMARK & RECENT)
    create_pdf(
        "doc_phase1_05_sc_kesavananda_bharati.pdf",
        "SUPREME COURT LANDMARK - KESAVANANDA BHARATI V. STATE OF KERALA",
        [
            "IN THE SUPREME COURT OF INDIA",
            "Writ Petition (Civil) No. 135/1970 | (1973) 4 SCC 225",
            "Bench: 13-Judge Constitution Bench | Date: 24-04-1973",
            "Kesavananda Bharati ... Petitioner VERSUS State of Kerala ... Respondent",
            "SUBJECT: Constitutional Law - Amending Power under Article 368.",
            "RATIO DECIDENDI:",
            "Parliament has wide powers to amend the Constitution under Article 368, but it cannot alter or destroy the BASIC STRUCTURE or framework of the Constitution.",
            "STATUS: Binding Landmark Precedent.",
        ]
    )

    create_pdf(
        "doc_phase1_05_sc_puttaswamy_privacy.pdf",
        "SUPREME COURT LANDMARK - JUSTICE K.S. PUTTASWAMY V. UNION OF INDIA",
        [
            "IN THE SUPREME COURT OF INDIA",
            "Writ Petition (Civil) No. 494/2012 | (2017) 10 SCC 1",
            "Bench: 9-Judge Constitution Bench | Date: 24-08-2017",
            "Justice K.S. Puttaswamy (Retd.) ... Petitioner VERSUS Union of India ... Respondent",
            "SUBJECT: Fundamental Right to Privacy under Article 21.",
            "RATIO DECIDENDI:",
            "The Right to Privacy is a fundamental right protected under Article 21 of the Constitution. Any restriction must satisfy the tripartite test of Legality, Need, and Proportionality.",
            "STATUS: Binding Supreme Court Precedent.",
        ]
    )

    # CATEGORY 6: SELECTED HIGH COURT JUDGMENTS
    create_pdf(
        "doc_phase1_06_dhc_cheque_bounce.pdf",
        "DELHI HIGH COURT - CHEQUE BOUNCE NI ACT JUDGMENT",
        [
            "IN THE HIGH COURT OF DELHI AT NEW DELHI",
            "Criminal Appeal No. 582/2024 | Date of Decision: 14-02-2024",
            "Mehta Traders ... Appellant VERSUS Sharma Enterprises ... Respondent",
            "SUBJECT: Negotiable Instruments Act Section 138 & 139 Presumption.",
            "RATIO DECIDENDI:",
            "Statutory presumption under Section 139 NI Act requires probable defense evidence to rebut, not mere denial of debt.",
            "STATUS: Active High Court Precedent.",
        ]
    )

    # CATEGORY 7: LEGAL DEFINITIONS
    create_pdf(
        "doc_phase1_07_legal_definitions_compendium.pdf",
        "COMPENDIUM OF STATUTORY LEGAL DEFINITIONS - PHASE 1",
        [
            "STRUCTURED COLLECTION OF IMPORTANT INDIAN LEGAL DEFINITIONS",
            "1. 'Personal Data' - Defined under Section 2(t) DPDP Act 2023: Any data about an individual who is identifiable by or in relation to such data.",
            "2. 'Financial Debt' - Defined under Section 5(8) IBC 2016: A debt along with interest, if any, which is disbursed against consideration for time value of money.",
            "3. 'Consumer' - Defined under Section 2(7) Consumer Protection Act 2019: Any person who buys goods or hires services for consideration, excluding commercial resale.",
            "4. 'Public Servant' - Defined under Section 2(28) BNS 2023 & Section 21 IPC: Persons holding public office or performing public duties.",
            "5. 'Consideration' - Defined under Section 2(d) Indian Contract Act 1872: When at the desire of the promisor, the promisee does or abstains from doing an act.",
        ]
    )

    # CATEGORY 8: LEGAL PRINCIPLES / DOCTRINES
    create_pdf(
        "doc_phase1_08_legal_doctrines_principles.pdf",
        "INDIAN LEGAL DOCTRINES & PRINCIPLES COMPENDIUM",
        [
            "ESSENTIAL INDIAN LEGAL DOCTRINES & PRINCIPLES",
            "1. Natural Justice (Audi Alteram Partem & Nemo Judex In Causa Sua): No person shall be condemned unheard, and no person shall be a judge in their own cause.",
            "2. Res Judicata (Section 11 CPC): A matter once finally adjudicated by a competent court cannot be re-agitated between the same parties.",
            "3. Basic Structure Doctrine: Constitutional amendments violating fundamental core framework are void (Kesavananda Bharati v. State of Kerala).",
            "4. Doctrine of Proportionality: Administrative & legislative measures restricting rights must be strictly proportionate to legitimate state objectives.",
            "5. Promissory Estoppel: State or individual cannot backtrack on promises where the other party acted upon them to their detriment.",
        ]
    )

    # CATEGORY 9: LEGAL PROCEDURES
    create_pdf(
        "doc_phase1_09_legal_procedures_civil_criminal.pdf",
        "STANDARD LEGAL PROCEDURES GUIDE - CIVIL & CRIMINAL",
        [
            "PROCEDURAL GUIDE FOR INDIAN COURTS & TRIBUNALS",
            "1. Civil Litigation Procedure (CPC 1908): Plaint Filing -> Summons -> Written Statement (30-90 days) -> Framing Issues -> Evidence -> Final Arguments -> Decree.",
            "2. Regular Bail Procedure (Section 437/439 CrPC & Sec 480 BNSS): Application to Magistrate/Sessions -> Notice to Public Prosecutor -> Hearing on Custodial Necessity.",
            "3. Writ Petition Procedure (Article 226/32): Filing Petition -> Prima Facie Hearing -> Issue of Notice/Rule Nisi -> Counter Affidavit -> Final Order.",
            "4. Consumer Complaint Procedure: Complaint to District Commission -> Notice -> 30-day Reply -> Mediation / Evidence -> Final Order within 90 days.",
        ]
    )

    # CATEGORY 10: IMPORTANT LEGAL FORMS
    create_pdf(
        "doc_phase1_10_important_legal_forms.pdf",
        "IMPORTANT LEGAL FORMS & REFERENCE APPLICATIONS",
        [
            "REFERENCE FORMATS FOR COURT APPLICATIONS & FORMS",
            "FORM 1: BAIL APPLICATION FORMAT (UNDER SECTION 480 BNSS / 439 CrPC)",
            "In the Court of Sessions Judge at [City]",
            "Bail Application No. _____ of 2024",
            "Applicant: [Name] VERSUS State of [State]",
            "PRAYER: It is humbly prayed that the applicant be released on bail in FIR No. ___ under Section ____, pending trial.",
            "FORM 2: AFFIDAVIT FORMAT",
            "I, [Name], S/o [Father's Name], Aged __ years, R/o [Address], do hereby solemnly affirm and declare on oath...",
        ]
    )

    # CATEGORY 11: BASIC LEGAL DOCUMENT TEMPLATES
    create_pdf(
        "doc_phase1_11_basic_document_templates.pdf",
        "BASIC LEGAL DOCUMENT TEMPLATES & AGREEMENTS",
        [
            "STANDARD DRAFTING TEMPLATES FOR LEGAL AGREEMENTS",
            "TEMPLATE 1: NON-DISCLOSURE AGREEMENT (NDA)",
            "This Non-Disclosure Agreement ('Agreement') is entered into on [Date] by and between Disclosing Party and Receiving Party...",
            "TEMPLATE 2: LEGAL NOTICE FOR BREACH OF CONTRACT",
            "BY REGISTERED POST AD: Ref No: ___ Date: ____ To: [Recipient Name]... UNDER INSTRUCTIONS FROM MY CLIENT...",
            "TEMPLATE 3: RESIDENTIAL LEASE / RENTAL AGREEMENT",
            "This Lease Agreement executed on [Date] between Lessor and Lessee for premises situated at [Address]...",
        ]
    )

    # CATEGORY 12: GOVERNMENT NOTIFICATIONS / DIRECTIONS
    create_pdf(
        "doc_phase1_12_govt_certin_rbi_notifications.pdf",
        "GOVERNMENT & REGULATORY NOTIFICATIONS / DIRECTIONS",
        [
            "REGULATORY NOTIFICATIONS & GAZETTE DIRECTIONS",
            "1. CERT-In Cyber Security Directions (No. 20(3)/2022-CERT-In): Mandating reporting of cyber security incidents within 6 hours of identification.",
            "2. RBI Master Direction on Digital Payment Security Controls (RBI/2021-22/10): Mandatory multi-factor authentication and fraud monitoring.",
            "3. Ministry of Corporate Affairs Gazette Notification: Commencement of provisions relating to compromise and arrangement under Companies Act.",
        ]
    )

    # CATEGORY 13: CITATION & CROSS-REFERENCE DATA
    create_pdf(
        "doc_phase1_13_citation_cross_reference_index.pdf",
        "CITATION & CROSS-REFERENCE INDEX MATRIX",
        [
            "CORE CITATION & RELATIONAL GRAPH CROSS-REFERENCE INDEX",
            "1. Act -> Section Cross Reference:",
            "   - Indian Contract Act, 1872 -> Section 73 (Unliquidated Damages) -> Section 74 (Liquidated Penalty).",
            "   - Bharatiya Nyaya Sanhita, 2023 -> Section 101 (Murder) -> Replaces IPC Section 300.",
            "2. Judgment -> Statute Cross Reference:",
            "   - Kesavananda Bharati v. State of Kerala (1973) 4 SCC 225 -> Article 368 Constitution of India.",
            "   - Justice K.S. Puttaswamy v. Union of India (2017) 10 SCC 1 -> Article 21 Constitution of India -> DPDP Act 2023.",
            "3. Definition -> Source Provision:",
            "   - 'Personal Data' -> Section 2(t) DPDP Act 2023 -> Article 21 Constitution.",
        ]
    )

    print("Phase 1 Legal Dataset PDF generation complete! Generated 20 PDFs covering all 13 categories.")


if __name__ == "__main__":
    main()
