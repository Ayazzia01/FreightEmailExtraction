By Ayaz Zia Ansari

---

# Freight Forwarding Email Extraction System

This repository contains an LLM-powered pipeline designed to extract structured shipment data from unstructured freight forwarding inquiry emails. It utilizes **Llama 3.3 70B** via the Groq API and a robust Python-based reconciliation layer to ensure high accuracy against UN/LOCODE standards.

## 1. Setup Instructions

1. **Clone the repository:**
```bash
git clone https://github.com/Ayazzia01/FreightEmailExtraction.git
cd FreightEmailExtraction

```


2. **Install Dependencies:**
```bash
pip install -r requirements.txt

```


3. **Configure Environment:**
Create a `.env` file in the root directory and add your Groq API key:
```env
GROQ_API_KEY=your_actual_api_key_here

```


4. **Run the Pipeline:**
```bash
python extract.py   # Processes emails and generates output.json
python evaluate.py  # Calculates accuracy against ground_truth.json

```



---

## 2. Prompt Evolution Log

Note: I developed the workflow in a jupyter notebook. Iterating over prompts and tuning them for specific cases. Broadly, the following is the versioning.

### v1: Basic Extraction

* **Accuracy:** NA
* **Issue:** First iteration of prompts. Did not extract all the origin_port_name and destination_port_name separated by '/' (multi-port). Struggled with CBM (Revenue Ton mentioned).
* **Example:** `EMAIL_007` extracted "Chennai" but failed to map it to `INMAA`.

### v2: Logic & Unit Handling

* **Accuracy:** ~78%
* **Issue:** Extracted multi-port, but only as (MAA / HYD / BLR). Handled port names in post-processing and returned proper port code and port name.
* **Example:** `EMAIL_015` missed the inland container depot (ICD) context.

### v3: Robust Reconciliation (Final)

* **Accuracy:** **94.00% (Current)**
* **Improvement:** Multi-port logic had issues that INBLR was getting matched for MAA / HYD / BLR. Updated it for exact string matching first and added a scoring logic. Cargo weights had an issue - all weights were being summed. Fix: Filtered largest weight. Introduced a Python-based reconciliation layer with a word-level abbreviation map (e.g., `MAA` -> `Chennai`) for product_line (Example: `EMAIL_30`) .
* **Result:** Successfully handles complex slashes (`JED / DAM / RUH`) and enforces canonical naming according to `port_codes_reference.json`.

---

## 3. Accuracy Metrics (Current)

| Field | Accuracy |
| --- | --- |
| **Product Line** | 100.00% |
| **Origin Port Code** | 94.00% |
| **Origin Port Name** | 94.00% |
| **Destination Port Code** | 90.00% |
| **Destination Port Name** | 82.00% |
| **Incoterm** | 96.00% |
| **Cargo Weight (kg)** | 92.00% |
| **Cargo CBM** | 98.00% |
| **Is Dangerous** | 100.00% |
| **Overall Accuracy** | **94.00%** |

---

## 4. Edge Cases Handled

1. **Multi-Port Reconciliation (EMAIL_044):** * **Problem:** Email listed "MAA / BLR / HYD".
* **Solution:** Implemented a word-by-word abbreviation mapper that converts "MAA" to "Chennai" before matching against the 47-port reference list.


2. **Body vs. Subject Conflict:**
* **Problem:** Subject mentioned "FOB" but the Body requested "CIF terms".
* **Solution:** Explicitly instructed the LLM that Body content has priority over Subject content.


3. **Unit Normalization:**
* **Problem:** Mixed units like "5 MT" or "500 lbs".
* **Solution:** Built-in conversion factors in the system prompt to ensure all weights are converted to `kg` and rounded to 2 decimal places.



---

## 5. System Design Questions

### 1. Scale

To process 10,000 emails/day with a 99% 5-minute SLA, I would move from a synchronous script to an asynchronous queue. We can also Batch the inputs together and process it in one go. This will reduce API cost.

This saves LLM costs and improves latency and allows us to scale horizontally by adding more worker nodes without exceeding the $500/month budget.

### 2. Monitoring

I would implement a **Confidence Scoring** mechanism where the LLM outputs its own certainty level. If the average confidence or the "Port Match Success Rate" drops below a threshold (e.g., from 90% to 70%), it triggers an alert. To investigate, I would log "Drift Samples"—randomly selected emails where the LLM output doesn't match a port in our reference file, for manual review to see if new ports need to be added to our data.

### 3. Multilingual

To handle Mandarin and Hindi, I would use the same extraction pipeline without translation. Llama 3.3 and other modern LLMs are natively capable of translating the context into English while preserving technical logistics terms.

To evaluate accuracy, I would create a "Cross-Lingual Set" (emails in Mandarin/Hindi with English ground truths) and use a consistency check: the extracted values (weights, dimensions, codes) should be identical regardless of the input language.

---