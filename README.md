# Project Metronome: Behavioral API Traffic & Bot Detection Engine (MVP)
**Author:** Eugene Arkhipov  
**Project Status:** Functional MVP 

## 📌 Project Overview
**Project Metronome** is a lightweight Python data analytics utility designed to audit web service logs and detect automated bot activity by analyzing micro-behavioral interaction patterns. 

Unlike traditional static filters that rely on fragile signatures (like User-Agents), Metronome analyzes the temporal pacing and structural routing of requests. It integrates **Shannon Entropy**, **Stochastic Noise Resonance**, and multi-factor analytical scoring to isolate non-human script footprints that attempt to mimic human behavior.

### 🧠 Core Philosophy
A human operator navigates web systems with chaotic, naturally varying pauses. An automated script, conversely, operates rhythmically like a metronome or produces statistically degenerate sequences. This engine catches these micro-behavioral discrepancies to protect enterprise endpoints.

---

## 🔥 Key Features
* **Vectorized Path Masking:** Uses optimized Pandas and Regular Expressions to clean dynamic URLs, stripping query parameters and converting specific IDs/UUIDs into uniform endpoint templates (e.g., changing `/api/v1/user/123-abc/profile` into `/{id}`).
* **User Flow Transition Entropy:** Utilizes vectorized NumPy operations (`np.char.add`) to reconstruct consecutive application user-routing paths and measures the entropy of these navigation transitions. Bots usually follow rigid, repetitive routing graphs.
* **Stochastic Noise Resonance Test:** Measures interval distribution elasticity by adding adaptive Gaussian noise to click pauses. Regular bot intervals experience sharp entropy variations under noise, while organic human behaviors remain statistically stable.
* **Multi-Factor Behavioral Heuristics:** Evaluates transaction logs against four analytical checkpoints:
  * First-lag request autocorrelation (`autocorr_lag1`) to find rhythmic timers.
  * Coefficient of interval variation (`cv_interval`) to detect strict execution scripts.
  * Endpoint & sequence mapping complexity via Shannon Entropy.
  * Average transaction pacing speed.
* **Transparent Expert Scoring:** Synthesizes behavioral indicators through a weighted scoring matrix (`calculate_bot_score`), outputting risk levels ranked from 0 (Human) to 1 (Definite Bot).

---

## 🛠️ Tech Stack & Requirements
* **Language:** Python 3.8+
* **Libraries:** `pandas`, `numpy`, `scipy`, `tqdm`

To install dependencies:
```bash
pip install -r requirements.txt
```

---

## 🚀 Usage & Pipeline

### 1. Log File Placement
Before running the analyzer, you need to provide the raw infrastructure log file:
* **Filename:** The file must be named strictly **`raw_request.csv`**.
* **Location:** Place the `raw_request.csv` file directly into the **root directory** of the project (the same folder where `bot_detector.py` is located).
* **Data Schema:** The CSV file can be extracted from your API Gateway, Reverse Proxy (Nginx/Envoy), or SIEM system logs. It must include at least the following 5 columns (case-sensitive):
  * `userId` — Unique identifier of the authenticated user or session account.
  * `RequestId` — Unique transactional token assigned to each specific HTTP request event.
  * `timestamp` — Date and time of the request (standard timestamp format).
  * `RequestPath` — Raw URL endpoint pathway string.
  * `ipAddress` — Client's remote IP location metadata.

### 2. Execution
Run the main evaluation script from your terminal:
```bash
python bot_detector.py
```

### 3. Reviewing Deliverables
Once execution logs complete, check the repository folder for results:
* Comprehensive prioritize threat ranking and behavioral statistics are saved directly inside: **`final_bot_analysis_fixed.csv`**.

* ### 4. Interpreting the Results (Scoring Metrics)
The generated report links each `userId` to a computed **`bot_score`** ranging from `0.0` (organic human) to `1.0` (definite automated script). The scoring is compiled transparently based on the following engineering weights inside the script logic:

* **Autocorrelation Check (`autocorr_lag1`):** Adds up to `+0.5` to the score if consecutive click intervals are highly dependent and predictable (a strict metric for cyclical scripts).
* **Interval Consistency (`cv_interval`):** Adds `+0.3` if the coefficient of variance is under `0.5`, identifying "metronome-like" timers lacking natural human delays.
* **Pacing Evaluation (`mean_interval`):** Adds `+0.3` if the average time between actions is under 1.0 second, highlighting superhuman execution speeds.
* **Endpoint Monotony (`endpoint_entropy`):** Adds `+0.2` if routing path entropy drops under `0.8`, flagging repetitive single-endpoint abuse (typical for scrapers or brute-force bots).

#### 🛡️ Risk Tiers Guide:
* **`0.0 - 0.3` (Low Risk):** Legitimate human user. Demonstrates healthy behavioral chaos, natural time variances, and expected endpoint diversity.
* **`0.4 - 0.6` (Suspicious):** Gray zone. Could be an aggressive user navigating with hotkeys or a poorly optimized background browser extension. Worth continuous monitoring.
* **`0.7 - 1.0` (Critical Threat):** Confirmed bot activity. High speed, rigid automated rhythm, and degenerate structural pathways. Recommended for immediate blocking via WAF firewall rules.

