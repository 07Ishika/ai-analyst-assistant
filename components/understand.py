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
            prompt = f"""
            Analyze this dataset and explain in simple English:
            - What this dataset is about
            - What each column means
            - Any interesting observations about the data quality
            - What kind of analysis can be done with this data
            
            Dataset Info:
            Rows: {summary['rows']}
            Columns: {summary['columns']}
            Column names and types: {summary['dtypes']}
            Null counts: {summary['null_counts']}
            Sample data: {summary['sample_data']}
            """
            response = ask_groq(prompt)
            st.session_state.ai_understanding = response
    
    if "ai_understanding" in st.session_state:
        st.markdown(st.session_state.ai_understanding)
        
        if st.button("Proceed to Clean & Transform →"):
            st.session_state.current_step = 3
            st.rerun()
            