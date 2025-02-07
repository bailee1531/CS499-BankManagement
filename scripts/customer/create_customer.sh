#!/bin/bash

# Sierra Yerges

customersCSV="../../csvFiles/customers.csv"
personsCSV="../../csvFiles/persons.csv"

firstName=$1
lastName=$2
address=$3
phone=$4
ssn=$5
username=$6
password=$7

nameReg="^[A-Za-z]{2,50}$"
addressReg="^[A-Za-z0-9 ,.-]{5,100}$"
phoneReg="^[0-9]{10}$"
ssnReg="^[0-9]{3}-[0-9]{2}-[0-9]{4}$"
passwordReg="^[a-z0-9A-Z!@#$&]{8,14}$"

# Validation
if [[ -z $firstName || -z $lastName || -z $address || -z $phone || -z $ssn || -z $username || -z $password ]]; then
  exit 7  # Missing input
fi
if ! [[ $firstName =~ $nameReg && $lastName =~ $nameReg ]]; then
  exit 1  # Invalid name
fi
if ! [[ $address =~ $addressReg ]]; then
  exit 2  # Invalid address
fi
if ! [[ $phone =~ $phoneReg ]]; then
  exit 3  # Invalid phone number
fi
if ! [[ $ssn =~ $ssnReg ]]; then
  exit 4  # Invalid SSN
fi
# Check if the username is already taken
if grep -q "^$username," "$customersCSV"; then
  exit 5  # Username already exists
fi
if ! [[ $password =~ $passwordReg ]]; then
  exit 6  # Password does not meet standards
fi


# Generate Customer ID
if [ ! -f "$customersCSV" ]; then
  echo "Username,Password,CustomerID,SSN" > "$customersCSV"
  customer_id=1
else
  customer_id=$(($(tail -n +2 "$customersCSV" | wc -l) + 1))
fi

# Store in persons.csv
if [ ! -f "$personsCSV" ]; then
  echo "UserType,LastName,FirstName,Address,PhoneNum,SSN" > "$personsCSV"
fi

echo "$username,$password,$customer_id,$ssn" >> "$customersCSV"
echo "Customer,$lastName,$firstName,$address,$phone,$ssn" >> "$personsCSV"
