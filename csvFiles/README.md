# csv.Files
The system manages customers, employees, accounts, loans, transactions, and payments in .csv files allocated in this directory.

## Account.csv
Stores account-related information for customers.

Columns:
* AccountID: Unique identifier for the account.
* CustomerID: Links to the Customer.csv file.
* AccountType: Type of account (e.g., Checking, Savings).
* CurrBal: Current balance.
* DateOpened: Date the account was opened.

Purpose:
Tracks all customer accounts, their balances, and their types (e.g., Checking, Savings).

## Customer.csv
Stores customer-specific data.

Columns:
* Username: User made to be used at login.
* Password: Must meet standard below.
  * 8-14 characters.
  * At least one digit.
  * At least one character from the set !@#$&
    * Ex. abcDEF123!
* CustomerID: Unique identifier for the customer.
* SSN: Links to the Person.csv file.

Purpose:
Identifies customers and links their personal details and account information.

## Employee.csv
Stores employee-specific data.

Columns:
* EmployeeID: Unique identifier for each employee.
* Position: Job role (e.g., Teller, Admin).
* SSN: Links to the Person.csv file.

Purpose:
Tracks employee roles and allows the system to assign tasks based on their position.

## Loan.csv
Stores loan-related information.

Columns:
* LoanID: Unique identifier for the loan.
* CustomerID: Links to the Customer.csv file.
* LoanType: Type of loan.
* LoanAmt: Loan amount.
* IntRate: Interest rate.
* Term: Loan term in months.
* StartDate: Start date of loan.
* EndDate: End date of loan.

Purpose:
Manages customer loans, their types, and payment schedules.

## LoanPayment.csv
Tracks payments made towards loans.

Columns:
* LoanPayID: Unique identifier for each loan payment.
* LoanID: Links to the Loan.csv file.
* SchedPayDate: Scheduled payment date.
* PayAmount: Total payment amount.
* PrinPay: Principal payment amount.
* InterestPay: Interest payment amount.
* PaidAmount: Amount actually paid.
* PaidDate: Date of payment.

Purpose:
Keeps track of scheduled and actual payments for loans.

## Person.csv
Stores personal details of all users (Customers and Employees).

Columns:
* UserType: Role (e.g., Customer, Employee).
* LastName: Last name of individual.
* FirstName: First name of individual.
* Address: Residential address.
* PhoneNum: Relevant phone number.
* SSN: Social Security Number.

Purpose:
Acts as the central repository for personal data used across other entities.

## Transaction.csv
Logs all transactions performed on accounts.

Columns:
* TransID: Unique identifier for each transaction.
* AccountID: Links to the Account.csv file.
* TransType: Type of transaction (e.g., Deposit, Withdrawal).
* Amount: Transaction amount.
* TransDate: Date of the transaction.

Purpose:
Tracks deposits, withdrawals, and other account-related transactions.

# Entity Relationships
* Person is the base entity shared by both Customer and Employee roles through the SSN field.
* Customer is linked to one or more Account records using the CustomerID.
* Employee performs actions such as creating accounts or processing transactions.
* Account is linked to multiple Transaction records to log activities.
* Loan is tied to a customer and linked to LoanPayment for payment tracking.

# How to Use These Files
1. Initial Setup:
* Populate Person.csv with personal data for all customers and employees.
* Add customer-specific records to Customer.csv and employee records to Employee.csv.

2. Accounts:
* Create account entries in Account.csv for each customer.
3. Transactions:
* Log all transactions (e.g., deposits, withdrawals) in Transaction.csv.
4. Loans:
* Record loan details in Loan.csv.
* Log scheduled and actual loan payments in LoanPayment.csv.

# Key Notes
* All IDs (e.g., CustomerID, AccountID) must be unique.
* Cross-reference (e.g., SSN, CustomerID, AccountID) to ensure data consistency.
* Utilizes software to load and manage CSV files efficiently.
