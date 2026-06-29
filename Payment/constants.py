class AllCloudEndpoints:
    GET_BRANCH = "/api/Branch/GetBranchByUserIdAsync"
    GET_REPAYMENT = "/api/Repayment/GetRepaymentDetails"  # Jo bhi tumhari baaki APIs hain
    SAVE_REPAYMENT = "/api/Repayment/SaveRepayment"
    

class PaymentLogTypes:
    AUTH_TOKEN = "Auth Token"             # Type 1: Token Generation API
    GET_LOAN_DETAILS = "GetLoanDetails"   # Type 2: AllCloud se details fetch karna
    POST_LOAN_DETAILS = "PostLoanDetails"

DEFAULT_PRODUCT_INFO = "PL"