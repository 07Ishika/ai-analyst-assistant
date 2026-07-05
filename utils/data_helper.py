import pandas as pd
import streamlit as st
import re

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

def detect_pii_in_values(df):
    import re
    
    patterns = {
        'phone_number': r'\b[6-9]\d{9}\b',
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'aadhar': r'\b\d{4}\s?\d{4}\s?\d{4}\b',
        'pan': r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b',
        'credit_card': r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'
    }

    pii_found = {}
    for col in df.select_dtypes(include=['object']).columns:
        sample = df[col].dropna().head(100).astype(str)
        for pii_type, pattern in patterns.items():
            matches = sample.str.contains(pattern, regex=True).sum()
            if matches > 0:
                if col not in pii_found:
                    pii_found[col] = []
                pii_found[col].append(pii_type)

    return pii_found

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