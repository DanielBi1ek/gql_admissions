# Admission Lifecycle

## Overview

This document describes the end-to-end lifecycle of an admission from the
initial user login through application acceptance by the study office.

## 1) Applicant Profile Initialization

- The user logs in and calls `admissionApplicantInit`.
- Required input: `street`, `houseNumber`, `city`, `phoneNumber`, `email`.
- Optional input: `databoxNumber`.
- The system auto-fills:
  - `applicant_user_id` from the authenticated user.
  - `firstname` and `lastname` from user context (`name`/`surname`).
- If an applicant profile already exists for the user, the mutation fails.

## 2) Payment Templates Setup (Study Office)

- A bank account is created via `admissionBankAccountCreate`.
  - Required: `accountPrefix`, `accountNumber`, `bankCode`.
  - Validation: all values must be numeric.
- Bank accounts are listed via `admissionBankAccountPage`.
- A payment template is created via `admissionPaymentInfoCreate`.
  - Required: `requiredAmount`, `bankAccountId`.
  - Validation: referenced bank account must exist.
  - Validation: `requiredAmount` must be numeric.
- Payment templates are listed via `admissionPaymentInfoPage`.

## 3) Offer Creation (Study Office)

- A new offer is created via `admissionOfferCreate`.
  - Required: `programId`, `applicationStartDate`, `applicationEndDate`, `paymentInfoId`.
  - Validations:
    - Study program exists.
    - Payment info exists.
    - Only one offer per program.
    - End date is after start date, and not on the same day.

## 4) Offer Selection

- The user lists offers via `admissionOfferPage`.
- Each offer includes:
  - `applicationStartDate` and `applicationEndDate` (valid submission window).
  - `paymentInfo` (required amount + linked bank account).

## 5) Application Submission

- The user submits an application with `admissionApplicationSubmit`.
  - Existing applications can be listed via `admissionApplicationPage`.
- The system validates:
  - The current date is within the offer window.
  - The user has no existing application for the same offer.
  - The applicant profile exists for the current user.
- The system creates:
  - A new pending payment (`AdmissionPayment`) with `required_amount`.
  - A new application (`AdmissionApplication`) with:
    - `applicant_id`, `offer_id`, `payment_id`, `applied_date`.
    - `accepted = false`, `accepted_at = null`, `acceptedby_id = null`.

## 6) Application Acceptance (Study Office)

- The study office accepts the application via `admissionApplicationAccept`.
- The system updates:
  - `accepted = true`
  - `accepted_at` (current timestamp)
  - `acceptedby_id` (current user)
- The system creates a new `AdmissionProcess` linked to the payment and stores
  its ID in `process_id`.

## 7) Follow-up Actions

- Payment matching and further processing are handled through:
  - `AdmissionPayment` (pending vs. matched payments).
  - `BankStatement` (incoming payments to be paired).
  - `AdmissionProcess` (process state linked to the application).
