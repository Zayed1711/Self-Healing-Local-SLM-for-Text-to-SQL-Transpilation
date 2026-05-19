# Self-Healing Local SLM for Text-to-SQL Transpilation

An edge-deployable, privacy-preserving Natural Language to SQL interface built for low-resource environments (CPU-only, 8GB RAM). 

## 📖 Research Overview
This project explores the efficacy of Small Language Models (SLMs) in semantic database querying. By utilizing a 1.5B parameter model (`qwen2.5-coder:1.5b`) running entirely locally, this system eliminates cloud computing costs and API data privacy concerns. 

To overcome the inherent hallucination risks of SLMs, this project introduces an **Iterative Schema-Aware Self-Correction** methodology.

### ✨ Key Features
* **100% Local Execution:** No data leaves the machine. Runs smoothly on standard i5 CPUs via Ollama.
* **Iterative Self-Correction:** The Python backend intercepts SQLite syntax/logic errors and invisibly prompts the AI to debug its own code before presenting a final answer.
* **Contextual Memory:** The Streamlit UI maintains chat history, allowing users to ask follow-up filtering questions naturally.
* **Hallucination "Escape Hatch":** The model is strictly engineered to output `UNANSWERABLE` if the requested data falls outside the defined schema, preventing dangerous query generation.

## 🚀 Quick Start

**1. Clone the repository and install dependencies:**
```bash
pip install -r requirements.txt

**2. Setup the Local Database:**
Run the reset script to generate the local SQLite database (inventory_database.db) with dummy data.
```bash
python reset_db.py

**3. Run the Benchmark Tests (Optional):**
To see the self-correction engine in action via the terminal:
```bash
python benchmark.py

**4. Launch the Web Interface:**
```bash
streamlit run app.py

🛠️ Tech Stack

>UI: Streamlit

>AI Engine: Ollama (qwen2.5-coder:1.5b)

>Database: SQLite3

>Language: Python 3.x