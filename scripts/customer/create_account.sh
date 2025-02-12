#!/bin/bash

# Sierra Yerges

personsCSV="../../csvFiles/persons.csv"
accountsCSV="../../csvFiles/accounts.csv"

accountType=$1
initialBalance=$2
ssn=$3  # Find the customer via SSN

balanceReg="^[0-9]+(\\.[0-9]{1,2})?$"

# Validation
if [[ -z $accountType || -z $initialBalance || -z $ssn ]]; then
  exit 3
fi
if ! [[ $accountType =~ ^(Checking|Savings|MoneyMarket)$ ]]; then
  exit 1
fi
if ! [[ $initialBalance =~ $balanceReg ]]; then
  exit 2
fi

# Find customer ID by SSN (ensure no extra spaces)
customerID=$(awk -F, -v ssn="$ssn" '$6 == ssn {print NR-1}' "$personsCSV" | tr -d '[:space:]')

if [[ -z $customerID ]]; then
  exit 4  # Customer not found
fi

# Generate Account ID
if [ ! -f "$accountsCSV" ]; then
  echo "AccountID,CustomerID,AccountType,CurrBal,DateOpened" > "$accountsCSV"
  accountID=1
else
  accountID=$(($(tail -n +2 "$accountsCSV" | wc -l) + 1))
fi

dateOpened=$(date '+%Y-%m-%d')
echo "$accountID,$customerID,$accountType,$initialBalance,$dateOpened" >> "$accountsCSV"
