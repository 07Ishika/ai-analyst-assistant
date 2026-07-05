import pandas as pd
import streamlit as st

def load_data(uploaded_file):
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
            return df
        elif uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file, engine='openpyxl')
            return df
        elif uploaded_file.name.endswith('.xls'):
            df = pd.read_excel(uploaded_file, engine='xlrd')
            return df
    except Exception as e:
        st.error(f"⚠️ Error reading file — {str(e)}")
        st.info("💡 Please try saving your file as CSV and uploading again.")
        st.stop()
        
# List of sensitive column keywords
SENSITIVE_KEYWORDS = [
    'password', 'passwd', 'pwd',
    'phone', 'mobile', 'contact', 'telephone',
    'email', 'mail',
    'ssn', 'aadhar', 'pan', 'passport',
    'credit_card', 'card_number', 'cvv',
    'address', 'street', 'pincode', 'zipcode',
    'dob', 'birth', 'age',
    'salary', 'income', 'bank_account',
    'gender', 'race', 'religion'
]

def detect_sensitive_columns(df):
    sensitive_cols = []
    for col in df.columns:
        col_lower = col.lower()
        for keyword in SENSITIVE_KEYWORDS:
            if keyword in col_lower:
                sensitive_cols.append(col)
                break
    return sensitive_cols

def get_safe_df(df):
    sensitive_cols = detect_sensitive_columns(df)
    safe_df = df.drop(columns=sensitive_cols, errors='ignore')
    return safe_df, sensitive_cols

def get_data_summary(df):
    summary = {
        "rows": df.shape[0],
        "columns": df.shape[1],
        "column_names": df.columns.tolist(),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "null_counts": df.isnull().sum().to_dict(),
        "sample_data": df.head(3).to_string()
    }
    return summary