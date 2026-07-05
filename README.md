# AI Analyst Assistant 📊

> Your intelligent data analysis companion — from raw data to business insights in minutes.

---

## The Problem I Solved

As a data analyst, I noticed that most of the work happens *before* opening Power BI. Understanding what a dataset contains, cleaning messy data, finding meaningful patterns — this takes hours and requires deep focus.

I built this tool to make that process faster, smarter, and more guided — without removing the analyst from the decision making process.

---

## What It Does

Upload any CSV or Excel file and the tool walks you through a complete analysis journey —

**1. Understand Your Data**
AI reads your dataset and explains it in plain English — what each column means, data quality observations, and what kind of analysis is possible.

**2. Clean & Transform**
AI detects data quality issues and suggests fixes with full reasoning — what the problem is, what risk it creates, what benefit fixing it brings. You approve or skip each suggestion. Nothing happens without your decision.

**3. Define Your Problem**
Tell the tool what business question you are trying to answer. Provide context about your data — what high and low values mean in your business, who will read the insights, what decisions will be made.

**4. Get Insights**
AI generates focused insights that directly answer your business question — using real calculated statistics, not guesses. Every insight references actual column names and real numbers from your data.

**5. Business Story**
Insights are converted into a dashboard style narrative that any non-technical stakeholder can understand — with urgency indicators, key metrics, and clear recommendations.

**6. Export**
Download your clean data as CSV or Excel for Power BI. Generate a complete analysis report covering all steps — downloadable as PDF.

---

## Design Decisions Worth Knowing

**Human in the Loop**
AI never takes action without analyst approval. Every cleaning suggestion has an Approve and Skip button. This matters because data has business context that AI cannot know.

**Anti Hallucination**
Instead of sending raw data to AI, the tool pre-calculates aggregated statistics — value distributions, averages per category, cross analysis — and sends those. AI can only reference numbers that are explicitly provided.

**PII Protection**
Before any data reaches the AI, the tool scans column names and actual values for sensitive information — passwords, phone numbers, emails, Aadhar, PAN, credit card numbers. Detected columns are flagged with a privacy warning and excluded from AI analysis.

**Business Context**
Generic insights are useless. The analyst provides context — what high and low values mean in their specific business — so AI generates insights relevant to the actual decision being made.

**Chain of Thought Prompting**
AI is instructed to think step by step before giving suggestions. This significantly improves the quality and relevance of outputs compared to direct prompting.

---
## Architecture Diagram

<p style="align:center">
  <img src="images/image.png" alt="Architecture Diagram" width="900">
</p>

## Tech Stack


| Layer | Tool | Why |
|---|---|---|
| Frontend | Streamlit | Industry standard for data tools in Python |
| Data Processing | Pandas | Standard data manipulation library |
| Visualizations | Plotly | Interactive charts |
| AI Model | Llama 3.3 70B via Groq | Fast inference, generous free tier, strong reasoning |
| Language | Python 3.11 | Wide ecosystem, analyst friendly |



## Running Locally

```bash
git clone https://github.com/07Ishika/ai-analyst-assistant.git
cd ai-analyst-assistant
pip install -r requirements.txt
```

Create a `.env` file —
Get your free API key at https://console.groq.com — generous free tier, no credit card needed.

```bash
streamlit run app.py
```

---

## What I Learned Building This

**Prompt engineering matters more than model choice.**
Getting AI to return structured JSON, think step by step, and use only provided statistics — each required careful prompt design. Temperature, system messages, and example formats all changed output quality significantly.

**Human in the loop is a design principle, not a feature.**
Every time I tried to automate a decision, I found a case where the automation would be wrong. Keeping the analyst in control made the tool more reliable and more trusted.

**AI hallucination is a real problem in analytics.**
When AI makes up numbers, decisions get made on false information. Pre calculating statistics and explicitly instructing AI to only use provided numbers reduced this significantly.

---

## Roadmap

**V2 planned improvements —**
- Multi agent validation — a second AI agent reviews insights for business relevance before showing them
- LangChain integration for complex analysis chains
- Data masking before AI transmission for stronger privacy
- Analyst consent gate before any data leaves the local machine

---

## Datasets Tested With

- Brazilian E-Commerce (Olist) — 100K orders across 7 tables
- Blood Donor Dataset — 10K records
- Student Assessment Scores — academic performance analysis
- Customer Geographic Data — regional distribution analysis

---

*Built as a portfolio project while learning data analytics. Feedback welcome.*