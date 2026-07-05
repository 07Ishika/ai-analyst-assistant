import streamlit as st
from utils.data_helper import load_data
from components.understand import show_understand
from components.clean import show_clean
from components.insights import show_insights
from components.storytelling import show_storytelling
from components.export import show_export
import io

# Page configuration
st.set_page_config(
    page_title="AI Analyst Assistant",
    page_icon="📊",
    layout="wide"
)

# Main title
st.title("📊 AI Analyst Assistant")
st.markdown("*Your intelligent data analysis companion*")

# Session state initialization
if "df" not in st.session_state:
    st.session_state.df = None
if "current_step" not in st.session_state:
    st.session_state.current_step = 1

# Sidebar - Progress tracker
with st.sidebar:
    st.header("📍 Progress")
    steps = {
        1: "📁 Upload Data",
        2: "🔍 Understand",
        3: "🧹 Clean & Transform",
        4: "❓ Define Problem & Insights",
        5: "📖 Storytelling",
        6: "📤 Export"
    }
    for step_num, step_name in steps.items():
        if step_num == st.session_state.current_step:
            st.markdown(f"**→ {step_name}**")
        elif step_num < st.session_state.current_step:
            # Completed steps are clickable
            if st.button(f"✅ {step_name}", key=f"nav_{step_num}"):
                st.session_state.current_step = step_num
                st.rerun()
        else:
            st.markdown(f"{step_name}")

# Main content area
st.divider()

# Step 1 — Upload
if st.session_state.current_step == 1:
    st.header("Step 1 — Upload Your Data")
    st.write("Upload a CSV or Excel file to get started")

    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["csv", "xlsx", "xls"]
    )

    if uploaded_file is not None:
        df = load_data(uploaded_file)

        # Validation checks
        issues = []

        # Check 1 — too few rows
        if df.shape[0] < 50:
            issues.append(f"⚠️ Only {df.shape[0]} rows found. This looks like a summary report, not raw data. AI needs at least 50 rows for meaningful analysis.")

        # Check 2 — unnamed columns
        unnamed_cols = [col for col in df.columns if 'Unnamed' in str(col)]
        if len(unnamed_cols) > 0:
            issues.append(f"⚠️ {len(unnamed_cols)} columns have no proper names. Please check your file has proper column headers in the first row.")

        # Check 3 — too few columns
        if df.shape[1] < 2:
            issues.append("⚠️ Only 1 column found. A meaningful dataset needs at least 2 columns.")

        # Show issues or proceed
        if issues:
            st.error("**This file may not work well for analysis —**")
            for issue in issues:
                st.warning(issue)
            st.info("💡 **What to upload instead —** Raw transaction level data where each row is one record. For example — one row per order, one row per customer, one row per sale.")

            # Still allow proceeding but with warning
            if st.button("Proceed anyway →"):
                st.session_state.df = df
                st.session_state.current_step = 2
                st.rerun()

        else:
            st.session_state.df = df
            st.success("✅ File uploaded successfully!")
            st.write(f"**Rows:** {df.shape[0]} | **Columns:** {df.shape[1]}")
            st.dataframe(df.head(10))

            if st.button("Proceed to Understand →"):
                st.session_state.current_step = 2
                st.rerun()

# Step 2 — Understand
elif st.session_state.current_step == 2:
    show_understand(st.session_state.df)
    
    
elif st.session_state.current_step == 3:
    show_clean(st.session_state.df)
    
elif st.session_state.current_step == 4:
    show_insights(st.session_state.cleaned_df)
elif st.session_state.current_step == 5:
    show_storytelling(st.session_state.cleaned_df)
elif st.session_state.current_step == 6:
    show_export(st.session_state.df)