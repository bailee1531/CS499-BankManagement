#!/bin/bash

# Sierra Yerges

accountsCSV="../../csvFiles/accounts.csv"
transactionsCSV="../../csvFiles/transactions.csv"

accountID=$1
depositAmount=$2

amountReg="^[0-9]+(\\.[0-9]{1,2})?$"
idReg="^[0-9]+$"

# Validation
if [[ -z $accountID || -z $depositAmount ]]; then
  exit 2
fi
if ! [[ $accountID =~ $idReg ]]; then
  exit 2
fi
if ! [[ $depositAmount =~ $amountReg ]]; then
  exit 1
fi

# Update balance and log transaction
if grep -q "^$accountID," "$accountsCSV"; then
  currBalance=$(awk -F, -v accID="$accountID" '$1 == accID {print $4}' "$accountsCSV")
  newBalance=$(echo "$currBalance + $depositAmount" | bc)
  awk -F, -v accID="$accountID" -v newBal="$newBalance" 'BEGIN {OFS=","} $1 == accID {$4 = newBal} {print}' "$accountsCSV" > temp.csv && mv temp.csv "$accountsCSV"

  # Log transaction
  if [ ! -f "$transactionsCSV" ]; then
    echo "TransactionID,AccountID,TransactionType,Amount,TransactionDate" > "$transactionsCSV"
    transactionID=1
  else
    transactionID=$(($(tail -n +2 "$transactionsCSV" | wc -l) + 1))
  fi

echo -e "\n$transactionID,$accountID,Deposit,$depositAmount,$(date '+%Y-%m-%d')" >> "$transactionsCSV"
else
  exit 2
fi
