# SHG Guardian AI: User Handbook

This handbook provides instructions to operate the SHG Guardian AI web application dashboard.

---

### Accessing the Dashboard
1. Open your web browser (e.g., Google Chrome, Firefox, or Safari).
2. Navigate to the local server address: **[http://127.0.0.1:7860](http://127.0.0.1:7860)** or your live Hugging Face Space URL.
3. The interface will load.

---

### Ledger Ingestion & Processing
1. Navigate to the **Ledger Upload** tab.
2. Drag and drop or browse to select a member list CSV file from the **`Sample_test_dat`** directory.
3. Specify the reporting month in the **Reporting Month** input (default is `2026-06`).
4. Click **Start Automated Review**.
5. The panel on the right displays the live system work logs as the planner, evaluator, and worker agents execute the audit.

---

### Reviewing Analytics & Performance
1. Select the **Analytics Dashboard** tab.
2. View key indicators at the top, including:
   * **Total Members**: Count of records processed.
   * **Payment Collection Rate**: Percentage of planned monthly due amounts recovered.
   * **Risky Members**: Count of accounts flagged in the critical category.
   * **Warnings & Errors**: Count of anomalous data points.
3. Review the visual representations:
   * **Payment Collection Rates**: Displays amount due versus amount paid per member.
   * **Risk Level Categories**: Displays the proportion of low, medium, and high-risk members.
4. Scroll to view the **Detailed Review of All Members** table, which contains detailed AI risk score justifications.

---

### Auditing Data Quality Warnings
1. Navigate to the **Anomaly Report** tab.
2. Review the data entries flagged for errors, such as:
   * Negative saving or loan values.
   * Disproportionately high loan-to-savings ratios.
   * Input formatting mismatches or missing values.
   * Duplicate member ID values.

---

### Managing the Verification Queue
1. Navigate to the **Verification Queue** tab.
2. Review the list of accounts flagged for audit.
3. To take review action:
   * Locate the target **Member ID** (e.g., `SHG008`) or its corresponding **Record ID** (e.g., `13`) in the table.
   * Enter this ID in the **Record ID or Member ID to Review** input field.
   * Select your role: **Field Officer** (Level 1) or **Regional Coordinator** (Level 2).
   * Specify the audit action: **APPROVED**, **REJECTED**, or **NEEDS FIELD ESCALATION**.
   * Enter notes in the **Reviewer Notes** field and click **Submit Decision**.
   * Click **Refresh Escalation List** to view the updated status columns in the table.

---

### Interacting with the AI Financial Assistant
1. Navigate to the **AI Financial Assistant** tab.
2. Enter natural language questions in the text bar to search the database. Example queries:
   * *`Why is member SHG001 flagged?`*
   * *`Show high risk members`*
   * *`Who has missed payments?`*
   * *`Which village has the lowest recovery rate?`*
