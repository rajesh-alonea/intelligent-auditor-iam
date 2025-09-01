import json
import random
from datetime import datetime, timedelta
import uuid

def generate_sailpoint_sample_data():
    """Generate 100 sample SailPoint identity and access records"""
    
    # Sample data pools
    departments = ["Finance", "HR", "IT", "Sales", "Operations", "Legal", "Marketing", "Engineering"]
    locations = ["New York", "London", "Tokyo", "Sydney", "Frankfurt", "Singapore", "Toronto", "Mumbai"]
    job_titles = [
        "Financial Analyst", "Software Engineer", "HR Manager", "Sales Representative",
        "Operations Manager", "Legal Counsel", "Marketing Specialist", "Database Administrator",
        "Business Analyst", "Project Manager", "Security Administrator", "Compliance Officer"
    ]
    
    applications = [
        "SAP", "Salesforce", "Oracle", "Active Directory", "Exchange", "SharePoint",
        "Workday", "ServiceNow", "Jira", "Confluence", "Tableau", "PowerBI"
    ]
    
    entitlements = [
        "Read", "Write", "Admin", "Approve", "Create", "Delete", "Modify", "Execute",
        "View Reports", "Manage Users", "Financial Data Access", "HR Data Access"
    ]
    
    access_types = ["Application", "Role", "Group", "Entitlement", "Permission"]
    
    identities = []
    access_records = []
    
    # Generate 100 identities
    for i in range(100):
        identity_id = f"ID{str(i+1).zfill(6)}"
        employee_id = f"EMP{str(i+1001).zfill(4)}"
        
        identity = {
            "id": identity_id,
            "employeeId": employee_id,
            "firstName": f"User{i+1}",
            "lastName": f"LastName{i+1}",
            "email": f"user{i+1}@company.com",
            "department": random.choice(departments),
            "jobTitle": random.choice(job_titles),
            "location": random.choice(locations),
            "manager": f"MGR{str(random.randint(1, 20)).zfill(3)}",
            "startDate": (datetime.now() - timedelta(days=random.randint(30, 1825))).isoformat(),
            "status": random.choice(["Active", "Active", "Active", "Active", "Inactive", "Terminated"]),
            "riskScore": round(random.uniform(0.1, 0.9), 2),
            "lastLogin": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
            "attributes": {
                "costCenter": f"CC{random.randint(1000, 9999)}",
                "division": random.choice(["North America", "Europe", "Asia Pacific"]),
                "employeeType": random.choice(["Full-Time", "Part-Time", "Contractor"]),
                "clearanceLevel": random.choice(["Public", "Internal", "Confidential", "Restricted"])
            }
        }
        identities.append(identity)
        
        # Generate 2-5 access records per identity
        for j in range(random.randint(2, 5)):
            access_record = {
                "id": str(uuid.uuid4()),
                "identityId": identity_id,
                "employeeId": employee_id,
                "application": random.choice(applications),
                "accessType": random.choice(access_types),
                "entitlement": random.choice(entitlements),
                "grantedDate": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
                "lastAccessed": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                "requestedBy": f"REQ{random.randint(1, 50)}",
                "approvedBy": f"APP{random.randint(1, 20)}",
                "businessJustification": random.choice([
                    "Role-based access requirement",
                    "Project-specific access",
                    "Temporary elevated access",
                    "Standard department access",
                    "Management override"
                ]),
                "reviewDate": (datetime.now() + timedelta(days=random.randint(30, 180))).isoformat(),
                "certificationStatus": random.choice(["Certified", "Pending Review", "Expired", "Revoked"]),
                "riskLevel": random.choice(["Low", "Medium", "High"]),
                "isPrivileged": random.choice([True, False, False, False]),  # 25% privileged
                "isOrphaned": random.choice([True, False, False, False, False]),  # 20% orphaned
                "violatesSOD": random.choice([True, False, False, False, False]),  # 20% SOD violations
                "compliance": {
                    "sox": random.choice([True, True, True, False]),  # 25% SOX violations
                    "gdpr": random.choice([True, True, True, True, False]),  # 20% GDPR violations
                    "hipaa": random.choice([True, True, True, True, False]),  # 20% HIPAA violations
                    "pci": random.choice([True, True, True, False])  # 25% PCI violations
                },
                "metadata": {
                    "source": "SailPoint IIQ",
                    "lastUpdated": datetime.now().isoformat(),
                    "confidence": round(random.uniform(0.7, 1.0), 2),
                    "dataClassification": random.choice(["Public", "Internal", "Confidential", "Restricted"])
                }
            }
            access_records.append(access_record)
    
    return {
        "identities": identities,
        "accessRecords": access_records,
        "metadata": {
            "totalIdentities": len(identities),
            "totalAccessRecords": len(access_records),
            "generatedAt": datetime.now().isoformat(),
            "version": "1.0",
            "source": "SailPoint Identity Platform"
        }
    }

if __name__ == "__main__":
    print("Generating SailPoint sample data...")
    data = generate_sailpoint_sample_data()
    
    # Save complete dataset
    with open("sailpoint_sample_data.json", "w") as f:
        json.dump(data, f, indent=2)
    
    # Save identities separately
    with open("identities.json", "w") as f:
        json.dump(data["identities"], f, indent=2)
    
    # Save access records separately  
    with open("access_records.json", "w") as f:
        json.dump(data["accessRecords"], f, indent=2)
    
    print(f"Generated {data['metadata']['totalIdentities']} identities")
    print(f"Generated {data['metadata']['totalAccessRecords']} access records")
    print("Files created:")
    print("- sailpoint_sample_data.json (complete dataset)")
    print("- identities.json (identities only)")
    print("- access_records.json (access records only)")
