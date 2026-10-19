# FATHER PRE-DESIGN · SECURITY / COMPLIANCE / MANDATORY DOMAIN BUDGET v0.1

**Purpose:** estimate the mandatory cost envelope before architecture begins.

This is not a procurement specification and not an exact quotation.
At Pre-Design stage the result is a justified budget range with assumptions, mandatory/optional classification and confidence.

---

# 1. Ownership

Primary coordinator: **Information Security**.

Contributors:
- Product Manager;
- Legal / Compliance;
- Domain specialist;
- Architect / Infrastructure;
- FinOps / procurement when available.

Information Security coordinates the first estimate because security, data class, regulated activity, trust boundaries and required controls strongly affect architecture and total cost.

---

# 2. Budget equation

```text
PRE-DESIGN MANDATORY BUDGET
=
SECURITY CONTROLS
+ SECURITY LICENSES
+ COMPLIANCE / ASSESSMENT
+ MANDATORY DOMAIN SERVICES
+ REQUIRED EXTERNAL SYSTEMS
+ INFRASTRUCTURE DELTA
+ INTEGRATION COST
+ OPERATIONS / STAFF
+ AUDIT / EVIDENCE RETENTION
+ RESERVE
```

The Product Manager receives both:

```text
PRODUCT VALUE
vs
MANDATORY COST ENVELOPE
```

---

# 3. Mandatory domain stack

FATHER must determine whether a product feature activates a domain profile.

Examples:

## COMMERCE / E-COMMERCE

Possible mandatory or practically unavoidable cost drivers, depending on jurisdiction and business model:

- payment provider / acquiring;
- bank/payment-system integration;
- fiscalization / receipt infrastructure where applicable;
- anti-fraud controls;
- refunds / chargeback process;
- payment reconciliation;
- identity/authentication requirements;
- personal-data controls;
- transaction logging and evidence;
- security assessment / PCI-related scope where applicable;
- accounting/ERP integration;
- customer notification channels.

## FINANCE / BANKING

- regulated payment/banking integrations;
- KYC/AML-related processes where applicable;
- stronger authentication;
- transaction monitoring;
- fraud controls;
- audit/evidence retention;
- cryptographic/key-management requirements;
- segregated environments;
- regulator/industry reporting;
- certified/approved protection products where required.

## HEALTHCARE

- sensitive/medical-data protection;
- consent/authority handling;
- stronger access control;
- audit trail;
- retention;
- data exchange standards/integrations;
- specialist/human review;
- high-assurance backup/recovery;
- regulated hosting/infrastructure constraints where applicable.

## GOVERNMENT / REGULATED INFORMATION SYSTEM

- classification/category determination;
- required security controls;
- certified protection products where applicable;
- assessment/attestation/conformity activities where applicable;
- logging/evidence requirements;
- protected network/integration constraints;
- operational security processes.

## CHILDREN / GUARDIANSHIP / CARE

- legal authority/delegation;
- guardian consent;
- age transition rules;
- sensitive-data restrictions;
- enhanced audit;
- restricted automation;
- emergency escalation/human controls.

Domain profiles are applicability candidates, not automatic legal conclusions.

---

# 4. Cost classes

Each cost item must be classified:

- MANDATORY_BY_LAW_OR_REGULATOR
- MANDATORY_BY_CONTRACT
- MANDATORY_BY_PAYMENT_OR_PLATFORM_PROVIDER
- MANDATORY_BY_SECURITY_RISK
- MANDATORY_FOR_OPERATION
- RECOMMENDED
- OPTIONAL

---

# 5. Cost dimensions

For every item:

- item_id;
- triggering_feature;
- domain_profile;
- requirement_source;
- cost_class;
- mandatory_status;
- one_time_cost_range;
- recurring_monthly_range;
- recurring_annual_range;
- transaction_or_usage_cost;
- implementation_effort;
- integration_effort;
- required_staff;
- audit_or_assessment_cost;
- evidence_retention_cost;
- infrastructure_delta;
- schedule_impact;
- vendor_lock_in_risk;
- alternative;
- confidence;
- assumptions.

---

# 6. Budget bands

Until quotes or architecture choices exist:

```text
UNKNOWN
LOW
MEDIUM
HIGH
VERY_HIGH
```

Or use a monetary range with:
- currency;
- basis/date;
- source or estimation method;
- confidence.

Exact unsupported price values are forbidden.

---

# 7. Feature economics loop

```text
FEATURE
  ↓
DOMAIN / DATA / ACTION CLASSIFICATION
  ↓
MANDATORY REQUIREMENTS
  ↓
MANDATORY STACK
  ↓
BUDGET IMPACT
  ↓
TIME-TO-MARKET IMPACT
  ↓
OPERATIONS IMPACT
  ↓
VALUE / COST REVIEW
  ↓
KEEP | REDESIGN | DEFER | DROP
```

---

# 8. Required Pre-Design output

The Information Security / Compliance stage must produce:

**SECURITY_COMPLIANCE_BUDGET_ENVELOPE**

with:

- base product cost impact;
- security cost impact;
- mandatory domain services;
- mandatory external systems;
- licensing/subscriptions;
- one-time cost range;
- recurring cost range;
- usage/transaction dependent cost;
- staffing/operations;
- audit/certification/assessment;
- reserve/uncertainty;
- major cost drivers;
- alternatives;
- recommendation.

---

# 9. Example: commerce feature

Feature:
"User can buy a paid service inside the product."

FATHER must not model this as only:

```text
BUTTON → PAYMENT API
```

Pre-Design must ask:

```text
Who is merchant?
Which jurisdiction?
Who processes payment data?
Are card details handled directly?
What payment/acquiring provider is used?
What fiscal/receipt obligations apply?
What refund/chargeback process exists?
What fraud controls are required?
What transaction evidence must be retained?
What personal data is created?
What provider fees are recurring?
What security/compliance scope is triggered?
```

Only after those answers may the feature proceed toward architecture.

---

# 10. Principle

A feature is not "cheap" because its code is small.

```text
REAL FEATURE COST
=
CODE
+ SECURITY
+ COMPLIANCE
+ LICENSES
+ EXTERNAL SERVICES
+ OPERATIONS
+ SUPPORT
+ AUDIT
+ LONG-TERM OPEX
```

FATHER must expose this before architecture.
