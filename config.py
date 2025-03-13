"""
Configuration settings for the CSV to XML conversion utility.
This module contains configuration constants and mappings used throughout the application.
"""

# Default values
DEFAULT_LOCATION_CODE = "249003"
DEFAULT_LANGUAGE = "English"
DEFAULT_SESSION_TYPE = "Telephone"
DEFAULT_BUSINESS_STATUS = "No"
DEFAULT_SURVEY_AGREEMENT = "No"
DEFAULT_URBAN_RURAL = "Undetermined"
DEFAULT_COUNSELING_TYPE = "Business Start-up/Preplanning"

# Error/warning categories
class ValidationCategory:
    MISSING_REQUIRED = "missing_required_field"
    MISSING_FIELD = "missing_field"
    INVALID_FORMAT = "invalid_format"
    INVALID_VALUE = "invalid_value"
    INVALID_DATE = "invalid_date"
    TRUNCATED_VALUE = "truncated_value"
    STANDARDIZED_VALUE = "standardized_value"
    PROCESSING_ERROR = "processing_error"
    FILE_ACCESS = "file_access"
    FILE_WRITE = "file_write"

# Required fields
REQUIRED_FIELDS = ["Contact ID"]

# Maximum field lengths
MAX_FIELD_LENGTHS = {
    "CounselorNotes": 1000,
    "Last": 40,
    "First": 40,
    "Middle": 1,
    "Street1": 80,
    "Street2": 80,
    "City": 80,
    "Phone": 10,
    "PartnerClientNumber": 20,
    "PartnerSessionNumber": 20
}

# Salesforce to XML field mapping
FIELD_MAPPING = {
    # Client Request (Part 1) fields
    "Contact ID": "PartnerClientNumber",
    "Last Name": "ClientRequest_LastName",
    "First Name": "ClientRequest_FirstName",
    "Middle Name": "ClientRequest_MiddleInitial",
    "Email": "ClientRequest_Email",
    "Contact: Phone": "ClientRequest_Phone_Primary",
    "Mailing Street": "ClientRequest_Address_Street1",
    "Mailing City": "ClientRequest_Address_City", 
    "Mailing State/Province": "ClientRequest_Address_State",
    "Mailing Zip/Postal Code": "ClientRequest_Address_ZipCode",
    "Mailing Country": "ClientRequest_Address_Country_Code",
    "Agree to Impact Survey": "ClientRequest_SurveyAgreement",
    "Client Signature - Date": "ClientRequest_Signature_Date",
    "Client Signature(On File)": "ClientRequest_Signature_OnFile",
    
    # Client Intake (Part 2) fields
    "Race": "ClientIntake_Race_Code",
    "Ethnicity::": "ClientIntake_Ethnicity",  # Note the double colon
    "Gender": "ClientIntake_Gender_Code",
    "Disability": "ClientIntake_Disability",
    "Veteran Status": "ClientIntake_MilitaryStatus",
    "Branch Of Service": "ClientIntake_BranchOfService",
    "What Prompted you to contact us?": "ClientIntake_Media_Code",
    "Internet (specify)": "ClientIntake_Media_Other",
    "Currently In Business?": "ClientIntake_CurrentlyInBusiness",
    "Are you currently exporting?": "ClientIntake_CurrentlyExporting",
    "Account Name": "ClientIntake_CompanyName",
    "Type of Business": "ClientIntake_BusinessType",
    "Business Ownership - % Female": "ClientIntake_BusinessOwnership_Female",
    "Conduct Business Online?": "ClientIntake_ConductingBusinessOnline",
    "8(a) Certified?": "ClientIntake_Certified8a",
    "Total Number of Employees": "ClientIntake_TotalNumberOfEmployees",
    "Gross Revenues/Sales": "ClientIntake_ClientAnnualIncome_GrossRevenues",
    "Profits/Losses": "ClientIntake_ClientAnnualIncome_ProfitLoss",
    "Legal Entity of Business": "ClientIntake_LegalEntity_Code",
    "Other legal entity (specify)": "ClientIntake_LegalEntity_Other",
    "Nature of the Counseling Seeking?": "ClientIntake_CounselingSeeking_Code",
    
    # Counselor Record (Part 3) fields
    "Activity ID": "CounselorRecord_PartnerSessionNumber",
    "Business Start Date": "CounselorRecord_BusinessStartDate",
    "Total No. of Employees (Meeting)": "CounselorRecord_TotalNumberOfEmployees",
    "Gross Revenues/Sales (Meeting)": "CounselorRecord_ClientAnnualIncome_GrossRevenues",
    "Profit & Loss (Meeting)": "CounselorRecord_ClientAnnualIncome_ProfitLoss",
    "Certifications (SDB, HUBZONE, etc)": "CounselorRecord_Certifications_Code",
    "Other Certifications": "CounselorRecord_Certifications_Other",
    "SBA Financial Assistance": "CounselorRecord_SBAFinancialAssistance_Code",
    "Other SBA Financial Assistance": "CounselorRecord_SBAFinancialAssistance_Other",
    "Services Provided": "CounselorRecord_CounselingProvided_Code",
    "Referred Client to": "CounselorRecord_ReferredClient_Code",
    "Other (Referred Client to)": "CounselorRecord_ReferredClient_Other",
    "Type of Session": "CounselorRecord_SessionType",
    "Language(s) Used": "CounselorRecord_Language_Code",
    "Language(s) Used (Other)": "CounselorRecord_Language_Other",
    "Date": "CounselorRecord_DateCounseled",
    "Name of Counselor": "CounselorRecord_CounselorName",
    "Duration (hours)": "CounselorRecord_CounselingHours_Contact",
    "Prep Hours": "CounselorRecord_CounselingHours_Prepare",
    "Travel Hours": "CounselorRecord_CounselingHours_Travel",
    "Comments": "CounselorRecord_CounselorNotes",
    "Non-SBA Loan Amount": "CounselorRecord_NonSBALoanAmount",
    "SBA Loan Amount": "CounselorRecord_SBALoanAmount",
    "Amount of Equity Capital Received": "CounselorRecord_EquityCapitalReceived"
}

# List of valid session types
VALID_SESSION_TYPES = [
    "Face-to-face",
    "Online",
    "Prepare Only",
    "Telephone",
    "Training",
    "Update Only"
]

# List of session types that don't require contact hours
NO_CONTACT_HOUR_SESSION_TYPES = [
    "Prepare Only",
    "Training",
    "Update Only"
]

# Counseling date validation threshold
MIN_COUNSELING_DATE = "2023-10-01"  
