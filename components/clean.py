import streamlit as st
import pandas as pd
import json
from utils.groq_helper import ask_groq
from utils.data_helper import detect_sensitive_columns, get_safe_df

def get_ai_suggestions(df):
    prompt = f"""
You are a senior data analyst guiding a junior analyst.
Analyze this dataset and return ONLY a JSON array. No other text.

For each issue found, return this exact structure:
[
  {{
    "issue": "short title of the problem",
    "column": "exact column name or all",
    "problem": "what exactly is wrong in this specific dataset",
    "risk": "what bad thing will happen in analysis if not fixed",
    "benefit": "what good thing happens after fixing",
    "action": "one of: lowercase, strip_whitespace, drop_duplicates, fill_mean, fill_mode, drop_nulls"
  }}
]

Base everything on this actual dataset — be specific to these columns and this data:
Columns: {df.columns.tolist()}
Data Types: {df.dtypes.astype(str).to_dict()}
Sample Data: {df.head(5).to_string()}
Null Counts: {df.isnull().sum().to_dict()}
Duplicate Count: {df.duplicated().sum()}

Rules:
- problem, risk, benefit must be specific to THIS dataset and THESE columns
- Do not use generic statements
- Maximum 3 suggestions
- Return ONLY the JSON array
- Wide range in numeric columns is NORMAL — do not suggest it as an issue
- Only suggest fill_mean or fill_mode if null count for that column is greater than 0
- Only suggest drop_nulls if null count for that column is greater than 0
- Attendance values like 0,1,2,3 are valid scale values — not inconsistent
- Do not suggest cleaning for columns that have no actual data quality issues
    """
    response = ask_groq(
        prompt,
        system_message="You are a senior data analyst. You only respond with valid JSON arrays based on actual data provided. Never use generic examples.",
        temperature=0.0
    )
    return response

def apply_action(df, action, column):
    try:
        if action == "lowercase" and column != "all":
            df[column] = df[column].str.lower()
        elif action == "strip_whitespace" and column != "all":
            df[column] = df[column].str.strip()
        elif action == "drop_duplicates":
            df = df.drop_duplicates()
        elif action == "fill_mean" and column != "all":
            df[column] = df[column].fillna(df[column].mean())
        elif action == "fill_mode" and column != "all":
            df[column] = df[column].fillna(df[column].mode()[0])
        elif action == "drop_nulls" and column != "all":
            df = df.dropna(subset=[column])
        return df
    except Exception as e:
        st.error(f"Could not apply action: {e}")
        return df

def show_clean(df):
    st.header("Step 3 — Clean & Transform")
    st.write("AI will suggest cleaning actions — you approve or skip each one")

# PII Detection — before anything else
    sensitive_cols = detect_sensitive_columns(df)
    
    # Value level PII detection
    from utils.data_helper import detect_pii_in_values
    value_pii = detect_pii_in_values(df)
    
    # Combine both detections
    all_sensitive = list(set(sensitive_cols + list(value_pii.keys())))

    if all_sensitive:
        st.markdown(f"""
        <div style='background-color: #fde8e8; padding: 15px; 
        border-radius: 10px; border-left: 5px solid #F44336; margin: 10px 0'>
        <h4>🔒 Privacy Warning — Sensitive Data Detected</h4>
        <p><b>Columns flagged by name:</b> {', '.join(sensitive_cols) if sensitive_cols else 'None'}</p>
        <p><b>Columns flagged by value scan:</b> {', '.join(value_pii.keys()) if value_pii else 'None'}</p>
        """, unsafe_allow_html=True)

        # Show what PII types were found in values
        if value_pii:
            for col, pii_types in value_pii.items():
                st.markdown(f"""
                <div style='background-color: #fff5f5; padding: 8px 15px; 
                border-radius: 6px; margin: 5px 0'>
                ⚠️ Column <b>{col}</b> contains — {', '.join(pii_types)}
                </div>
                """, unsafe_allow_html=True)

        st.markdown("""
        <p>These columns are <b>excluded from AI analysis</b> to protect privacy.</p>
        <p>Do not modify or share these columns without proper authorization.</p>
        </div>
        """, unsafe_allow_html=True)

        safe_df, _ = get_safe_df(df)
        # Also remove value-level PII from safe_df
        safe_df = safe_df.drop(columns=[c for c in value_pii.keys() if c in safe_df.columns], errors='ignore')
        st.info(f"✅ AI will only analyze {safe_df.shape[1]} safe columns out of {df.shape[1]} total columns.")
    else:
        safe_df = df.copy()
        st.success("✅ No sensitive data detected in this dataset!")

    # Initialize session state
    if "cleaned_df" not in st.session_state:
        st.session_state.cleaned_df = df.copy()

    if "suggestions" not in st.session_state:
        st.session_state.suggestions = []

    if "applied_actions" not in st.session_state:
        st.session_state.applied_actions = []

    # Section 1 — Auto Data Quality Check
    st.subheader("1️⃣ Automatic Data Quality Check")
    col1, col2, col3 = st.columns(3)
    with col1:
        null_count = st.session_state.cleaned_df.isnull().sum().sum()
        st.metric("Total Null Values", null_count)
    with col2:
        duplicate_count = st.session_state.cleaned_df.duplicated().sum()
        st.metric("Duplicate Rows", duplicate_count)
    with col3:
        st.metric("Total Rows", st.session_state.cleaned_df.shape[0])

    # Section 2 — AI Suggestions with Approve/Skip
    st.subheader("2️⃣ AI Suggestions — Approve or Skip Each")

    if st.button("🤖 Get AI Cleaning Suggestions"):
        with st.spinner("AI is analyzing your data..."):
            # Pass safe_df to AI — no sensitive columns
            raw_response = get_ai_suggestions(safe_df)
            try:
                clean_response = raw_response.strip()
                if "```json" in clean_response:
                    clean_response = clean_response.split("```json")[1].split("```")[0]
                elif "```" in clean_response:
                    clean_response = clean_response.split("```")[1].split("```")[0]
                start = clean_response.find("[")
                end = clean_response.rfind("]") + 1
                if start != -1 and end != 0:
                    clean_response = clean_response[start:end]
                suggestions = json.loads(clean_response)
                # Filter invalid actions
                suggestions = [s for s in suggestions if s['action'] != 'none']
                # Filter irrelevant suggestions
                null_counts = st.session_state.cleaned_df.isnull().sum().to_dict()
                duplicate_count = st.session_state.cleaned_df.duplicated().sum()

                def is_valid_suggestion(s):
                        col = s['column']
                        action = s['action']

                        # Skip if no nulls but action is null related
                        if action in ['drop_nulls', 'fill_mean', 'fill_mode']:
                            if col == 'all':
                                return st.session_state.cleaned_df.isnull().sum().sum() > 0
                            return null_counts.get(col, 0) > 0

                        # Skip drop_duplicates if no duplicates
                        if action == 'drop_duplicates':
                            return duplicate_count > 0

                        # Skip none actions
                        if action == 'none':
                            return False

                        # Skip lowercase/strip for numeric columns
                        if action in ['lowercase', 'strip_whitespace']:
                            if col in st.session_state.cleaned_df.columns:
                                if st.session_state.cleaned_df[col].dtype in ['int64', 'float64']:
                                    return False

                        return True

                suggestions = [s for s in suggestions if is_valid_suggestion(s)]
                st.session_state.suggestions = suggestions
                st.success(f"✅ Found {len(suggestions)} suggestions!")
            except Exception as e:
                st.error(f"Could not parse AI response. Error: {e}")
                st.write("Raw response:", raw_response)

    # Show suggestion cards with Approve/Skip
    if st.session_state.suggestions:
        for i, suggestion in enumerate(st.session_state.suggestions):
            action_key = f"{suggestion['action']}_{suggestion['column']}"

            if action_key in st.session_state.applied_actions:
                st.success(f"✅ Done — {suggestion['issue']}")
                continue

            with st.container():
                st.markdown(f"""
                <div style='background-color: #f0f2f6; padding: 15px; 
                border-radius: 10px; margin: 10px 0px'>
                <h4>💡 {suggestion['issue']}</h4>
                <p><b>📌 Column:</b> {suggestion['column']}</p>
                <p><b>⚠️ Problem:</b> {suggestion['problem']}</p>
                <p><b>🚨 Risk if not fixed:</b> {suggestion['risk']}</p>
                <p><b>✅ Benefit after fixing:</b> {suggestion['benefit']}</p>
                <p><b>🔧 Action:</b> {suggestion['action']}</p>
                </div>
                """, unsafe_allow_html=True)

                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("✅ Approve", key=f"approve_{i}"):
                        st.session_state.cleaned_df = apply_action(
                            st.session_state.cleaned_df,
                            suggestion['action'],
                            suggestion['column']
                        )
                        st.session_state.applied_actions.append(action_key)
                        st.rerun()
                with col2:
                    if st.button("⏭️ Skip", key=f"skip_{i}"):
                        st.session_state.applied_actions.append(action_key)
                        st.rerun()

    # Section 3 — Cleaning Summary
    st.subheader("3️⃣ Cleaning Summary")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Original Rows", df.shape[0])
        st.metric("Original Columns", df.shape[1])
    with col2:
        st.metric("Current Rows", st.session_state.cleaned_df.shape[0])
        st.metric("Current Columns", st.session_state.cleaned_df.shape[1])

    st.write("**Preview of Cleaned Data**")
    st.dataframe(st.session_state.cleaned_df.head(10))

    st.divider()
    if st.button("Proceed to Define Problem →"):
        st.session_state.current_step = 4
        st.rerun()
        
        