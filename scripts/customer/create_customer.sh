#!/bin/bash

# Sierra Yerges

customersCSV="../../csvFiles/customers.csv"
personsCSV="../../csvFiles/persons.csv"

firstName=$1
lastName=$2
address=$3
phone=$4
ssn=$5

nameReg="^[A-Za-z]{2,50}$"
addressReg="^[A-Za-z0-9 ,.-]{5,100}$"
phoneReg="^[0-9]{10}$"
ssnReg="^[0-9]{3}-[0-9]{2}-[0-9]{4}$"

# Validation
if [[ -z $firstName || -z $lastName || -z $address || -z $phone || -z $ssn ]]; then
  exit 5
fi
if ! [[ $firstName =~ $nameReg && $lastName =~ $nameReg ]]; then
  exit 1
fi
if ! [[ $address =~ $addressReg ]]; then
  exit 2
fi
if ! [[ $phone =~ $phoneReg ]]; then
  exit 3
fi
if ! [[ $ssn =~ $ssnReg ]]; then
  exit 4
fi

# Generate Customer ID
if [ ! -f "$customersCSV" ]; then
  echo "CustomerID,SSN" > "$customersCSV"
  customer_id=1
else
  customer_id=$(($(tail -n +2 "$customersCSV" | wc -l) + 1))
fi

# Store in persons.csv
if [ ! -f "$personsCSV" ]; then
  echo "UserType,LastName,FirstName,Address,PhoneNum,SSN" > "$personsCSV"
fi

echo "$customer_id,$ssn" >> "$customersCSV"
echo "Customer,$lastName,$firstName,$address,$phone,$ssn" >> "$personsCSV"
