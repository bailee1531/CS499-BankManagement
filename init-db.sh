#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<--EOSQL
-- Create table
  CREATE TYPE 'user-type' AS ENUM ('customer', 'employee');
  CREATE TYPE 'position' AS ENUM ('teller', 'administrator');
  CREATE TYPE 'loan-type' AS ENUM ('mortage', 'personal');
  CREATE TYPE 'account-type' AS ENUM ('checking', 'savings', 'money-market', 'credit-card');
  CREATE TYPE 'transaction-type' AS ENUM ('deposit', 'withdrawal', 'transfer');
  CREATE TABLE 'person' ('user-type' NOT NULL, 'firstName' TEXT NOT NULL, 'lastName' TEXT NOT NULL, address TEXT NOT NULL, 'phoneNum' TEXT, 'cellNum' TEXT NOT NULL, 'ssn' TEXT NOT NULL GENERATED ALWAYS AS IDENTITY);
  CREATE TABLE 'employee' ('position' NOT NULL, 'employeeID' INTEGER NOT NULL GENERATED ALWAYS AS IDENTITY);
  CREATE TABLE 'customer' ('customerID' INTEGER NOT NULL GENERATED ALWAYS AS IDENTITY);
  CREATE TABLE 'account' ('accountID' INTEGER NOT NULL GENERATED ALWAYS AS IDENTITY, 'account-type' NOT NULL, 'currentBal' DECIMAL(10, 2) NOT NULL, 'dateOpened' DATE NOT NULL);
  CREATE TABLE 'loan' ('loanID' INTEGER NOT NULL GENERATED ALWAYS AS IDENTITY, 'loan-type' NOT NULL, 'loanAmnt' DECIMAL(10,2) NOT NULL, 'interestRate' DECIMAL(10,2) NOT NULL, 'term' INTEGER NOT NULL, 'startDate' DATE NOT NULL, 'endDate' DATE NOT NULL);
  CREATE TABLE 'loan-payment' ('loanPaymentID' INTEGER NOT NULL GENERATED ALWAYS AS IDENTITY, 'scheduledPayDate' DATE NOT NULL, 'paymentAmount' DECIMAL(10,2) NOT NULL, 'principalPayment' DECIMAL(10,2) NOT NULL, 'interestPayment' DECIMAL(10,2) NOT NULL, 'paidAmount' DECIMAL(10,2) NOT NULL, 'paidDate' DATE NOT NULL);
  CREATE TABLE 'transactions' ('transactionID' INTEGER NOT NULL GENERATED ALWAYS AS IDENTITY, 'transaction-type' NOT NULL, 'amount' DECIMAL(10,2) NOT NULL, 'transactionDate' DATE NOT NULL);
-- Create a customer role and set permissions
  CREATE ROLE "customer" WITH NOLOGIN;
  GRANT CONNECT ON DATABASE bankTest TO "customer";
  GRANT USAGE ON SCHEMA public TO "customer";
  GRANT SELECT ON person, customer-id, account, loan, loan-payment, transactions TO "customer";
  GRANT INSERT ON person, customer-id, account, loan-payment, transactions TO "customer";
  GRANT UPDATE ON person, account TO "customer";
  REVOKE ALL PRIVILEGES ON employee TO "customer";
-- Create a teller role and set permissions
  CREATE ROLE "teller" WITH NOLOGIN;
  GRANT CONNECT ON DATABASE bankTest TO "teller";
  GRANT USAGE ON SCHEMA public TO "teller";
  GRANT SELECT ON ALL TABLES IN SCHEMA public TO "teller";
  GRANT INSERT ON account, loan, loan-payment, transactions TO "teller";
  GRANT UPDATE ON account, loan TO "teller";
-- Create an admin role and set permissions
  CREATE ROLE "administrator" WITH NOLOGIN;
  GRANT CONNECT ON DATABASE bankTest TO "customer";
  GRANT USAGE ON SCHEMA public TO "administrator";
  GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA public TO "administrator";
  GRANT UPDATE ON person, employee, customer-id, account, loan TO "administrator";
  GRANT DELETE ON person, employee, customer-id, account, loan, transactions TO "administrator";
  ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO "administrator";
-- Create users and assign roles
  CREATE USER "bailee" WITH PASSWORD 'asdf1234';
  GRANT "administrator" TO "bailee";
EOSQL