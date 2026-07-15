# Payroll (Django app) — Repository Overview

This repo’s `payroll/` Django app contains the data model and APIs for salary structures, tax slabs, deductions, payroll runs, generated payroll amounts, payslip generation, and bank disbursement tracking.

## Folder: `payroll/`

- `payroll/models.py`
  - Core database models for payroll calculations and generated outputs.
- `payroll/services.py`
  - Payroll calculation logic (service layer). Computes gross pay, tax (via progressive slabs), then deductions (including statutory + configured deductions).
- `payroll/serializers.py`
  - DRF serializers for models.
- `payroll/views.py`
  - DRF viewsets providing CRUD/read APIs and custom actions (generate/run payroll and payslip PDF generation).
- `payroll/urls.py`
  - Router wiring for the above viewsets.

## Data Model (`payroll/models.py`)

### 1) SalaryStructure
Represents an employee’s salary breakdown over time.
- `employee` (FK to `employees.Employee`)
- Monetary components:
  - `basic_salary`
  - `housing_allowance`
  - `transport_allowance`
  - `other_allowances`
- Effective dates:
  - `effective_from`
  - `effective_to` (nullable)

Only one “latest active” structure is used for calculations (see `services.py`).

### 2) TaxSlab
Progressive tax configuration used for computing tax.
- `label`
- `lower_bound` (inclusive)
- `upper_bound` (nullable => no upper limit)
- `rate_percent`
- `order_index`
- `is_active`

### 3) DeductionType
Configures deduction behavior.
- `name` (unique)
- `is_statutory` (flag)
- `calculation_type`:
  - `percentage`
  - `fixed`
- `rate_or_amount`
- `is_active`

### 4) PayrollRun
A payroll run groups payroll calculations for a specific month/year.
- `period_month`
- `period_year`
- `run_status`:
  - `draft`, `processing`, `completed`, `disbursed`
- `initiated_by` (FK to auth user)
- timestamps:
  - `created_at`, `completed_at`

Uniqueness:
- `(period_month, period_year)` must be unique.

### 5) Payroll
Represents computed payroll for an employee within a payroll run.
- `payroll_run` (FK)
- `employee` (FK)
- `salary_structure` (FK, nullable)
- totals:
  - `gross_pay`
  - `total_deductions`
  - `net_pay`
- optional metrics:
  - `days_worked`
  - `leave_deduction_days`

Uniqueness:
- `(payroll_run, employee)` must be unique.

### 6) PayrollDeduction
Line-items for each deduction applied to a payroll.
- `payroll` (FK)
- `deduction_type` (FK)
- `amount`
- `calculation_basis` (free text)

Ordering:
- by `deduction_type__name`.

### 7) Payslip
Stores generated payslip PDF path.
- `payroll` (OneToOne)
- `file_path`
- `generated_at`, `downloaded_at`

### 8) BankDisbursement
Tracks bank export/disbursement file generation for a payroll run.
- `payroll_run` (FK)
- `file_path`
- `total_amount`
- `status`:
  - generated, submitted, confirmed, failed
- `generated_at`, `confirmed_at`

## Payroll Calculation Logic (`payroll/services.py`)

The payroll engine is implemented in the **service layer** so the same rules can be triggered by API endpoints or batch jobs.

### Entry point
- **`run_payroll_for_run(payroll_run)`**
  - Selects only employees with `employment_status='active'`.
  - Iterates employee-by-employee and calls `run_payroll_for_employee(payroll_run, employee)`.

### Per-employee calculation (today’s model behavior)
1. **Pick the applicable salary structure**
   - Filters `SalaryStructure` rows for the employee.
   - Uses only structures where:
     - `effective_from <= today`
     - and (`effective_to` is null OR `effective_to >= today`)
   - Picks the **most recent** one by ordering `-effective_from`.

2. **Compute gross pay**
   - `gross_pay = basic_salary + housing_allowance + transport_allowance + other_allowances`

3. **Compute tax using progressive slabs**
   - Reads all `TaxSlab` rows where `is_active=True`, ordered by `order_index`.
   - For each slab, it calculates the “slice” of taxable income that falls into that slab range.
   - The slab tax is computed as:
     - `slab_tax = slab_taxable * (rate_percent / 100)`
   - Sums across slabs until the taxable amount is fully covered.

4. **Convert tax + configured deductions into deduction line-items**
   - The code currently creates a **synthetic PAYE deduction line** as one of the deduction rows (label: `"PAYE"`) using the computed progressive tax.
   - Then it adds all active `DeductionType` rules:
     - **percentage**: `(rate_or_amount% of gross_pay)`
     - **fixed**: `rate_or_amount`

5. **Persist results idempotently**
   - Inside a DB transaction:
     - `Payroll` for `(payroll_run, employee)` is created if missing, otherwise updated.
     - Existing `PayrollDeduction` line-items for that payroll are deleted.
     - New `PayrollDeduction` rows are created from the computed breakdown.

> Presentation note: in your demo, the “models” that matter most are the ones that store *configuration* (SalaryStructure, TaxSlab, DeductionType) and the ones that store *computed output* (Payroll, PayrollDeduction, Payslip).

## API Overview (`payroll/views.py`)

Uses DRF ViewSets + a `DefaultRouter` in `payroll/urls.py`.

### ViewSets
- `PayrollRunViewSet` (ModelViewSet)
  - Standard CRUD for `PayrollRun`.
  - Custom actions:
    - `POST /payroll-runs/run/` (action name `run`)
      - expects `payroll_run_id` in request body
      - runs payroll calculations for that run.
    - `POST /payroll-runs/generate_payslips/` (action name `generate_payslips`)
      - expects `payroll_run_id`
      - generates PDF payslips via ReportLab into `settings.MEDIA_ROOT/payslips/`
      - creates/updates `Payslip` rows.

- `PayrollViewSet` (ReadOnlyModelViewSet)
  - read-only access to computed `Payroll` rows.
  - supports query params:
    - `employee`
    - `payroll_run` / `payroll_run_id`

- `PayrollDeductionViewSet` (ReadOnlyModelViewSet)
  - read-only access to `PayrollDeduction` line-items.
  - supports query param:
    - `payroll`

## URL Wiring (`payroll/urls.py`)

Router registrations:
- `payroll-runs/` => `PayrollRunViewSet`
- `''` (root) => `PayrollViewSet` (this means payroll listing can appear at the app root route)
- `deductions/` => `PayrollDeductionViewSet`

## Notes / Gaps vs “Payroll & Finance” spec

This repo’s `payroll` app currently focuses on:
- salary structures
- tax slabs
- generic deduction types
- payroll runs and computed payroll totals
- payslip PDF generation
- bank disbursement tracking

If you need extra finance/payments features such as explicit `PayrollItem`, `PayrollApproval`, `PayrollHistory`, `Benefits CRUD`, `Bank Export` beyond the `BankDisbursement` model, or more detailed tax rule modeling, those may be in other apps or still missing from this repo’s current implementation.

