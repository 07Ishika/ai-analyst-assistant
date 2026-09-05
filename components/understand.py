import streamlit as st
from utils.groq_helper import ask_groq
from utils.data_helper import get_data_summary

def show_understand(df):
    st.header("Step 2 — Understand Your Data")
    
    summary = get_data_summary(df)
    
    # Show basic stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Rows", summary["rows"])
    with col2:
        st.metric("Total Columns", summary["columns"])
    with col3:
        null_cols = sum(1 for v in summary["null_counts"].values() if v > 0)
        st.metric("Columns with Nulls", null_cols)

    st.subheader("Column Information")
    st.dataframe(df.dtypes.reset_index().rename(
        columns={"index": "Column", 0: "Data Type"}
    ))

    st.subheader("AI Understanding")
    if st.button("🤖 Ask AI to Understand My Data"):
        with st.spinner("AI is analyzing your data..."):
                        # Get detected dataset type from session state
            dataset_info = st.session_state.get("dataset_info", {})
            dataset_type = dataset_info.get("dataset_type", "general")
            
            type_specific_instructions = {
                "timeseries": """
                - Focus on explaining the time/date columns and what period this data covers
                - Explain what metrics are tracked over time
                - Note any gaps or irregularities in the time series
                - Suggest what trends or patterns can be analyzed
                """,
                "hr": """
                - Focus on explaining employee related columns — attrition, salary, department, tenure
                - Highlight any sensitive columns like salary that need careful handling
                - Explain what workforce insights can be derived
                - Note any data quality issues specific to HR data
                """,
                "crm": """
                - Focus on explaining customer related columns — demographics, location, purchase history
                - Highlight customer segmentation possibilities
                - Explain what customer behavior insights can be derived
                - Note any PII columns that need careful handling
                """,
                "transactional": """
                - Focus on explaining transaction columns — amount, category, date, status
                - Explain what revenue and sales insights can be derived
                - Note any currency or amount formatting issues
                - Suggest what business performance analysis is possible
                """,
                "marketing": """
                - Focus on explaining campaign metrics — impressions, clicks, conversions, spend
                - Explain what ROI and channel performance insights can be derived
                - Note any metric calculation possibilities
                - Suggest what campaign optimization analysis is possible
                """,
                "performance": """
                - Focus on explaining score and assessment columns
                - Explain what performance and risk insights can be derived
                - Note passing thresholds if visible in data
                - Suggest what intervention analysis is possible
                """,
                "healthcare": """
                - Focus on explaining clinical columns — diagnosis, treatment, outcomes, vitals
                - Highlight sensitive patient data that needs careful handling
                - Explain what health outcome insights can be derived
                - Note any medical coding or terminology in the data
                """,
                "general": """
                - Explain what this dataset is about based on column names
                - What each column means
                - Any interesting observations about data quality
                - What kind of analysis can be done
                """
            }

            instructions = type_specific_instructions.get(
                dataset_type,
                type_specific_instructions["general"]
            )

            prompt = f"""
You are a senior data analyst explaining a dataset to a junior analyst.

DATASET TYPE: {dataset_type}
{dataset_info.get('reasoning', '')}

Based on this being a {dataset_type} dataset, focus your explanation on:
{instructions}

Also cover:
1. What this dataset is about — one clear sentence
2. What each column means — in simple business language
3. Data quality observations specific to this type of dataset
4. What analysis is most valuable for this type of data

Dataset Info:
Rows: {summary['rows']}
Columns: {summary['columns']}
Column names and types: {summary['dtypes']}
Null counts: {summary['null_counts']}
Sample data: {summary['sample_data']}

Write in clear simple English. No technical jargon.
Format with clear sections and bullet points.
            """
            response = ask_groq(prompt, temperature=0.2)
            st.session_state.ai_understanding = response
    
    if "ai_understanding" in st.session_state:
        st.markdown(st.session_state.ai_understanding)
        
        if st.button("Proceed to Clean & Transform →"):
            st.session_state.current_step = 3
            st.rerun()
            