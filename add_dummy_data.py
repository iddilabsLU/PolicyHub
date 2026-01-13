"""
Add dummy document data to PolicyHub for testing purposes.

Run this script to populate the database with 10 sample documents.
"""

import uuid
from datetime import datetime, timedelta

from core.database import DatabaseManager


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


def add_dummy_documents():
    """Add 10 dummy documents to the database."""

    db = DatabaseManager.get_instance()

    # Get the first user to use as creator
    user_row = db.fetch_one("SELECT user_id FROM users LIMIT 1")
    if not user_row:
        print("Error: No users found in database. Please create an admin user first.")
        return

    creator_id = user_row["user_id"]
    now = datetime.now().isoformat()

    # Define 10 dummy documents with varied data
    documents = [
        {
            "doc_id": generate_uuid(),
            "doc_type": "POLICY",
            "doc_ref": "POL-AML-001",
            "title": "Anti-Money Laundering Policy",
            "description": "Core policy for AML compliance and customer due diligence procedures",
            "category": "AML",
            "owner": "Compliance Officer",
            "approver": "Board of Directors",
            "status": "ACTIVE",
            "version": "2.0",
            "effective_date": (datetime.now() - timedelta(days=180)).date().isoformat(),
            "last_review_date": (datetime.now() - timedelta(days=180)).date().isoformat(),
            "next_review_date": (datetime.now() + timedelta(days=185)).date().isoformat(),
            "review_frequency": "ANNUAL",
            "notes": "Updated to align with latest FATF recommendations",
            "mandatory_read_all": 1,
            "applicable_entity": "All Entities",
        },
        {
            "doc_id": generate_uuid(),
            "doc_type": "PROCEDURE",
            "doc_ref": "PROC-OPS-015",
            "title": "Trade Settlement Procedure",
            "description": "Step-by-step process for trade settlement and reconciliation",
            "category": "OPS",
            "owner": "Operations Manager",
            "approver": "COO",
            "status": "UNDER_REVIEW",
            "version": "1.2",
            "effective_date": (datetime.now() - timedelta(days=90)).date().isoformat(),
            "last_review_date": (datetime.now() - timedelta(days=90)).date().isoformat(),
            "next_review_date": (datetime.now() + timedelta(days=92)).date().isoformat(),
            "review_frequency": "SEMI_ANNUAL",
            "notes": "Currently under review to include new settlement platform",
            "mandatory_read_all": 0,
            "applicable_entity": "Trading Division",
        },
        {
            "doc_id": generate_uuid(),
            "doc_type": "POLICY",
            "doc_ref": "POL-GOV-003",
            "title": "Board Meeting & Governance Policy",
            "description": "Framework for board meetings, quorum requirements, and decision-making",
            "category": "GOV",
            "owner": "Company Secretary",
            "approver": "Chairman",
            "status": "ACTIVE",
            "version": "3.1",
            "effective_date": (datetime.now() - timedelta(days=400)).date().isoformat(),
            "last_review_date": (datetime.now() - timedelta(days=35)).date().isoformat(),
            "next_review_date": (datetime.now() + timedelta(days=-10)).date().isoformat(),  # OVERDUE
            "review_frequency": "ANNUAL",
            "notes": "OVERDUE - Needs review following new Companies Act provisions",
            "mandatory_read_all": 0,
            "applicable_entity": None,
        },
        {
            "doc_id": generate_uuid(),
            "doc_type": "MANUAL",
            "doc_ref": "MAN-IT-002",
            "title": "Cybersecurity Incident Response Manual",
            "description": "Complete guide for detecting, responding to, and recovering from security incidents",
            "category": "IT",
            "owner": "IT Security Manager",
            "approver": "CTO",
            "status": "ACTIVE",
            "version": "1.0",
            "effective_date": (datetime.now() - timedelta(days=60)).date().isoformat(),
            "last_review_date": (datetime.now() - timedelta(days=60)).date().isoformat(),
            "next_review_date": (datetime.now() + timedelta(days=305)).date().isoformat(),
            "review_frequency": "ANNUAL",
            "notes": None,
            "mandatory_read_all": 1,
            "applicable_entity": "All IT Staff",
        },
        {
            "doc_id": generate_uuid(),
            "doc_type": "HR_OTHERS",
            "doc_ref": "HR-POL-007",
            "title": "Remote Working Policy",
            "description": "Guidelines and requirements for remote and hybrid work arrangements",
            "category": "HR",
            "owner": "HR Director",
            "approver": "CEO",
            "status": "ACTIVE",
            "version": "2.3",
            "effective_date": (datetime.now() - timedelta(days=20)).date().isoformat(),
            "last_review_date": (datetime.now() - timedelta(days=20)).date().isoformat(),
            "next_review_date": (datetime.now() + timedelta(days=25)).date().isoformat(),  # DUE SOON
            "review_frequency": "SEMI_ANNUAL",
            "notes": "Recently updated - quarterly monitoring required",
            "mandatory_read_all": 1,
            "applicable_entity": "All Staff",
        },
        {
            "doc_id": generate_uuid(),
            "doc_type": "POLICY",
            "doc_ref": "POL-DP-001",
            "title": "Data Protection & Privacy Policy",
            "description": "GDPR compliance framework and data handling procedures",
            "category": "DP",
            "owner": "Data Protection Officer",
            "approver": "Legal Counsel",
            "status": "ACTIVE",
            "version": "4.0",
            "effective_date": (datetime.now() - timedelta(days=200)).date().isoformat(),
            "last_review_date": (datetime.now() - timedelta(days=200)).date().isoformat(),
            "next_review_date": (datetime.now() + timedelta(days=165)).date().isoformat(),
            "review_frequency": "ANNUAL",
            "notes": "Reviewed following ICO guidance update",
            "mandatory_read_all": 1,
            "applicable_entity": "All Entities",
        },
        {
            "doc_id": generate_uuid(),
            "doc_type": "PROCEDURE",
            "doc_ref": "PROC-ACC-022",
            "title": "Month-End Close Procedure",
            "description": "Detailed checklist for monthly financial close process",
            "category": "ACC",
            "owner": "Financial Controller",
            "approver": "CFO",
            "status": "ACTIVE",
            "version": "1.5",
            "effective_date": (datetime.now() - timedelta(days=120)).date().isoformat(),
            "last_review_date": (datetime.now() - timedelta(days=120)).date().isoformat(),
            "next_review_date": (datetime.now() + timedelta(days=60)).date().isoformat(),  # UPCOMING
            "review_frequency": "SEMI_ANNUAL",
            "notes": "Minor updates needed for new ERP module",
            "mandatory_read_all": 0,
            "applicable_entity": "Finance Team",
        },
        {
            "doc_id": generate_uuid(),
            "doc_type": "POLICY",
            "doc_ref": "POL-BCP-001",
            "title": "Business Continuity & Disaster Recovery Policy",
            "description": "Framework for maintaining operations during business disruptions",
            "category": "BCP",
            "owner": "Risk Manager",
            "approver": "Executive Committee",
            "status": "ACTIVE",
            "version": "2.0",
            "effective_date": (datetime.now() - timedelta(days=270)).date().isoformat(),
            "last_review_date": (datetime.now() - timedelta(days=270)).date().isoformat(),
            "next_review_date": (datetime.now() + timedelta(days=95)).date().isoformat(),
            "review_frequency": "ANNUAL",
            "notes": "Annual testing scheduled for next quarter",
            "mandatory_read_all": 1,
            "applicable_entity": "All Entities",
        },
        {
            "doc_id": generate_uuid(),
            "doc_type": "PROCEDURE",
            "doc_ref": "PROC-RISK-008",
            "title": "Risk Assessment Procedure",
            "description": "Methodology for identifying, assessing, and mitigating operational risks",
            "category": "RISK",
            "owner": "Risk Analyst",
            "approver": "CRO",
            "status": "DRAFT",
            "version": "0.9",
            "effective_date": (datetime.now() + timedelta(days=14)).date().isoformat(),
            "last_review_date": datetime.now().date().isoformat(),
            "next_review_date": (datetime.now() + timedelta(days=104)).date().isoformat(),
            "review_frequency": "QUARTERLY",
            "notes": "Draft pending final approval - target activation next week",
            "mandatory_read_all": 0,
            "applicable_entity": None,
        },
        {
            "doc_id": generate_uuid(),
            "doc_type": "MANUAL",
            "doc_ref": "MAN-REG-005",
            "title": "Regulatory Reporting Manual",
            "description": "Complete guide for preparing and submitting regulatory returns",
            "category": "REG",
            "owner": "Compliance Manager",
            "approver": "Head of Compliance",
            "status": "SUPERSEDED",
            "version": "3.2",
            "effective_date": (datetime.now() - timedelta(days=800)).date().isoformat(),
            "last_review_date": (datetime.now() - timedelta(days=400)).date().isoformat(),
            "next_review_date": (datetime.now() - timedelta(days=35)).date().isoformat(),
            "review_frequency": "ANNUAL",
            "notes": "Superseded by MAN-REG-006 following regulatory changes",
            "mandatory_read_all": 0,
            "applicable_entity": "Compliance Team",
        },
    ]

    # Insert documents
    insert_sql = """
        INSERT INTO documents (
            doc_id, doc_type, doc_ref, title, description, category, owner, approver,
            status, version, effective_date, last_review_date, next_review_date,
            review_frequency, notes, mandatory_read_all, applicable_entity,
            created_at, created_by, updated_at, updated_by
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
    """

    inserted_count = 0

    with db.get_connection() as conn:
        for doc in documents:
            try:
                conn.execute(
                    insert_sql,
                    (
                        doc["doc_id"],
                        doc["doc_type"],
                        doc["doc_ref"],
                        doc["title"],
                        doc["description"],
                        doc["category"],
                        doc["owner"],
                        doc["approver"],
                        doc["status"],
                        doc["version"],
                        doc["effective_date"],
                        doc["last_review_date"],
                        doc["next_review_date"],
                        doc["review_frequency"],
                        doc["notes"],
                        doc["mandatory_read_all"],
                        doc["applicable_entity"],
                        now,
                        creator_id,
                        now,
                        creator_id,
                    ),
                )
                inserted_count += 1
                print(f"✓ Added: {doc['doc_ref']} - {doc['title']}")
            except Exception as e:
                print(f"✗ Failed to add {doc['doc_ref']}: {e}")

    print(f"\n{'='*60}")
    print(f"Successfully inserted {inserted_count} dummy documents!")
    print(f"{'='*60}")
    print("\nDocument Status Summary:")
    print("  - ACTIVE: 7 documents")
    print("  - UNDER_REVIEW: 1 document")
    print("  - DRAFT: 1 document")
    print("  - SUPERSEDED: 1 document")
    print("\nReview Status Summary:")
    print("  - OVERDUE: 1 document (POL-GOV-003)")
    print("  - DUE SOON: 1 document (HR-POL-007)")
    print("  - UPCOMING: 1 document (PROC-ACC-022)")
    print("  - ON TRACK: 7 documents")


if __name__ == "__main__":
    print("PolicyHub - Adding Dummy Data")
    print("=" * 60)
    add_dummy_documents()
