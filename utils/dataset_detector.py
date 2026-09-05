import json
from utils.groq_helper import ask_groq

DATASET_TYPES = [
    "timeseries",
    "crm",
    "hr",
    "transactional",
    "marketing",
    "performance",
    "healthcare",
    "general"
]

def detect_dataset_type(df):
    """
    Uses AI to detect what type of dataset this is.
    Returns type string and what stats to calculate.
    """
    prompt = f"""
You are a data analyst expert. Look at this dataset and determine what type it is.

Column names: {df.columns.tolist()}
Data types: {df.dtypes.astype(str).to_dict()}
Sample data (3 rows): {df.head(3).to_string()}
Shape: {df.shape}

Dataset types to choose from:
- timeseries: stock prices, sales over time, weather, any data with dates and numeric trends
- crm: customer data, demographics, location, purchase history, churn
- hr: employee data, salary, department, tenure, attrition, performance ratings
- transactional: orders, payments, invoices, e-commerce, bank transactions
- marketing: campaigns, impressions, clicks, conversions, spend, channel performance
- performance: student scores, assessment results, attendance, grades, KPIs
- healthcare: patient data, diagnosis, treatment, vitals, medical records
- general: anything that doesn't fit above categories

Think step by step:
STEP 1 - What do the column names suggest?
STEP 2 - What does the sample data look like?
STEP 3 - What business domain does this belong to?
STEP 4 - What type fits best?

Return ONLY this JSON object:
{{
  "dataset_type": "one of the types above",
  "confidence": "high or medium or low",
  "reasoning": "one sentence why you chose this type",
  "primary_date_col": "name of date column if exists or null",
  "primary_metric_col": "most important numeric column for analysis",
  "primary_category_col": "most important categorical column for grouping or null",
  "key_business_question": "what question this dataset is typically used to answer"
}}

Return ONLY the JSON object.
    """
    
    response = ask_groq(
        prompt,
        system_message="You are a data classification expert. You only output valid JSON objects.",
        temperature=0.0
    )
    
    try:
        clean = response.strip()
        if "```json" in clean:
            clean = clean.split("```json")[1].split("```")[0]
        elif "```" in clean:
            clean = clean.split("```")[1].split("```")[0]
        start = clean.find("{")
        end = clean.rfind("}") + 1
        clean = clean[start:end]
        result = json.loads(clean)
        return result
    except Exception as e:
        return {
            "dataset_type": "general",
            "confidence": "low",
            "reasoning": "Could not detect type automatically",
            "primary_date_col": None,
            "primary_metric_col": df.select_dtypes(include=['float64','int64']).columns[0] if len(df.select_dtypes(include=['float64','int64']).columns) > 0 else None,
            "primary_category_col": None,
            "key_business_question": "What insights can be derived from this data?"
        }
        