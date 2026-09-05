import pandas as pd
import json
from utils.groq_helper import ask_groq

def calculate_stats(df, dataset_info):
    """
    Calculates type-specific statistics based on detected dataset type.
    Returns a dict of meaningful stats — small enough for token limits.
    """
    
    dataset_type = dataset_info.get("dataset_type", "general")
    date_col = dataset_info.get("primary_date_col")
    metric_col = dataset_info.get("primary_metric_col")
    category_col = dataset_info.get("primary_category_col")
    
    stats = {}
    stats["shape"] = {"rows": df.shape[0], "columns": df.shape[1]}
    stats["null_counts"] = df.isnull().sum().to_dict()
    
    if dataset_type == "timeseries":
        stats = calculate_timeseries_stats(df, date_col, metric_col, stats)
        
    elif dataset_type == "crm":
        stats = calculate_crm_stats(df, category_col, metric_col, stats)
        
    elif dataset_type == "hr":
        stats = calculate_hr_stats(df, category_col, metric_col, stats)
        
    elif dataset_type == "transactional":
        stats = calculate_transactional_stats(df, category_col, metric_col, stats)
        
    elif dataset_type == "marketing":
        stats = calculate_marketing_stats(df, category_col, metric_col, stats)
        
    elif dataset_type == "performance":
        stats = calculate_performance_stats(df, category_col, metric_col, stats)
        
    elif dataset_type == "healthcare":
        stats = calculate_healthcare_stats(df, category_col, metric_col, stats)
        
    else:
        stats = calculate_general_stats(df, stats)
    
    return stats


def calculate_timeseries_stats(df, date_col, metric_col, stats):
    """Time series — trends, peaks, dips, period averages"""
    try:
        numeric_cols = df.select_dtypes(include=['float64','int64']).columns.tolist()
        
        for col in numeric_cols[:5]:
            stats[f"{col}_stats"] = {
                "mean": round(df[col].mean(), 2),
                "min": round(df[col].min(), 2),
                "max": round(df[col].max(), 2),
                "first_value": round(df[col].iloc[0], 2),
                "last_value": round(df[col].iloc[-1], 2),
                "overall_change": round(df[col].iloc[-1] - df[col].iloc[0], 2),
                "pct_change": round(((df[col].iloc[-1] - df[col].iloc[0]) / df[col].iloc[0]) * 100, 2) if df[col].iloc[0] != 0 else 0
            }
        
        # Period averages if date column exists
        if date_col and date_col in df.columns:
            try:
                df[date_col] = pd.to_datetime(df[date_col])
                df['_year_month'] = df[date_col].dt.to_period('M')
                if metric_col and metric_col in df.columns:
                    monthly = df.groupby('_year_month')[metric_col].mean().round(2)
                    stats['monthly_averages'] = {
                        "best_month": str(monthly.idxmax()),
                        "worst_month": str(monthly.idxmin()),
                        "best_value": round(monthly.max(), 2),
                        "worst_value": round(monthly.min(), 2)
                    }
                df.drop('_year_month', axis=1, inplace=True, errors='ignore')
            except:
                pass
                
    except Exception as e:
        stats['error'] = str(e)
    return stats


def calculate_crm_stats(df, category_col, metric_col, stats):
    """CRM — customer segments, locations, value distributions"""
    try:
        # Categorical distributions
        cat_cols = [c for c in df.select_dtypes(include=['object']).columns 
                   if df[c].nunique() < 30][:4]
        
        for col in cat_cols:
            counts = df[col].value_counts().head(10)
            pcts = (df[col].value_counts(normalize=True) * 100).round(1).head(10)
            stats[f"{col}_distribution"] = {
                str(k): f"{v} ({pcts[k]}%)" 
                for k, v in counts.items()
            }
        
        # Numeric stats
        num_cols = df.select_dtypes(include=['float64','int64']).columns.tolist()[:4]
        for col in num_cols:
            stats[f"{col}_stats"] = {
                "mean": round(df[col].mean(), 2),
                "min": round(df[col].min(), 2),
                "max": round(df[col].max(), 2),
                "median": round(df[col].median(), 2)
            }
            
        # Cross stats
        if category_col and category_col in df.columns and metric_col and metric_col in df.columns:
            if df[category_col].nunique() < 30:
                cross = df.groupby(category_col)[metric_col].mean().round(2).sort_values(ascending=False)
                stats[f"avg_{metric_col}_by_{category_col}"] = cross.to_dict()
                
    except Exception as e:
        stats['error'] = str(e)
    return stats


def calculate_hr_stats(df, category_col, metric_col, stats):
    """HR — attrition, salary, department, tenure analysis"""
    try:
        # Find common HR columns
        all_cols = [c.lower() for c in df.columns]
        
        # Department distribution
        dept_col = next((c for c in df.columns if any(d in c.lower() 
                        for d in ['dept', 'department', 'team', 'division'])), category_col)
        
        if dept_col and dept_col in df.columns and df[dept_col].nunique() < 30:
            counts = df[dept_col].value_counts()
            stats['department_distribution'] = counts.to_dict()
        
        # Attrition analysis
        attrition_col = next((c for c in df.columns if 'attrit' in c.lower() 
                             or 'churn' in c.lower() or 'left' in c.lower()), None)
        if attrition_col:
            stats['attrition_rate'] = {
                "total": len(df),
                "attrited": int(df[attrition_col].sum()) if df[attrition_col].dtype in ['int64','float64'] else int((df[attrition_col] == 'Yes').sum()),
                "rate": round((df[attrition_col] == 'Yes').mean() * 100, 1) if df[attrition_col].dtype == 'object' else round(df[attrition_col].mean() * 100, 1)
            }
        
        # Salary analysis
        salary_col = next((c for c in df.columns if 'salary' in c.lower() 
                          or 'income' in c.lower() or 'pay' in c.lower()), metric_col)
        if salary_col and salary_col in df.columns:
            stats['salary_stats'] = {
                "mean": round(df[salary_col].mean(), 2),
                "min": round(df[salary_col].min(), 2),
                "max": round(df[salary_col].max(), 2),
                "median": round(df[salary_col].median(), 2)
            }
            if dept_col and dept_col in df.columns and df[dept_col].nunique() < 30:
                stats['avg_salary_by_dept'] = df.groupby(dept_col)[salary_col].mean().round(2).sort_values(ascending=False).to_dict()
        
        # Numeric stats for remaining columns
        num_cols = df.select_dtypes(include=['float64','int64']).columns.tolist()[:4]
        for col in num_cols:
            if col not in str(stats):
                stats[f"{col}_stats"] = {
                    "mean": round(df[col].mean(), 2),
                    "min": round(df[col].min(), 2),
                    "max": round(df[col].max(), 2)
                }
                
    except Exception as e:
        stats['error'] = str(e)
    return stats


def calculate_transactional_stats(df, category_col, metric_col, stats):
    """Transactional — revenue, top products, order patterns"""
    try:
        # Revenue/amount column
        amount_col = next((c for c in df.columns if any(a in c.lower() 
                          for a in ['amount','price','revenue','sales','total','value','payment'])), metric_col)
        
        if amount_col and amount_col in df.columns:
            stats['revenue_stats'] = {
                "total": round(df[amount_col].sum(), 2),
                "mean": round(df[amount_col].mean(), 2),
                "min": round(df[amount_col].min(), 2),
                "max": round(df[amount_col].max(), 2),
                "median": round(df[amount_col].median(), 2)
            }
        
        # Category analysis
        cat_cols = [c for c in df.select_dtypes(include=['object']).columns 
                   if df[c].nunique() < 50 and 'id' not in c.lower()][:3]
        
        for col in cat_cols:
            counts = df[col].value_counts().head(10)
            stats[f"{col}_distribution"] = counts.to_dict()
            
            if amount_col and amount_col in df.columns:
                revenue_by_cat = df.groupby(col)[amount_col].sum().round(2).sort_values(ascending=False).head(10)
                stats[f"revenue_by_{col}"] = revenue_by_cat.to_dict()
                
    except Exception as e:
        stats['error'] = str(e)
    return stats


def calculate_marketing_stats(df, category_col, metric_col, stats):
    """Marketing — campaign performance, ROI, channel analysis"""
    try:
        # Common marketing metrics
        spend_col = next((c for c in df.columns if any(s in c.lower() 
                         for s in ['spend','cost','budget','investment'])), None)
        conversion_col = next((c for c in df.columns if any(c2 in c.lower() 
                               for c2 in ['conversion','revenue','sales','return'])), metric_col)
        channel_col = next((c for c in df.columns if any(ch in c.lower() 
                           for ch in ['channel','source','medium','platform','campaign'])), category_col)
        
        if spend_col and spend_col in df.columns:
            stats['spend_stats'] = {
                "total": round(df[spend_col].sum(), 2),
                "mean": round(df[spend_col].mean(), 2),
                "max": round(df[spend_col].max(), 2)
            }
        
        if channel_col and channel_col in df.columns and df[channel_col].nunique() < 30:
            counts = df[channel_col].value_counts()
            stats['channel_distribution'] = counts.to_dict()
            
            if conversion_col and conversion_col in df.columns:
                perf = df.groupby(channel_col)[conversion_col].sum().round(2).sort_values(ascending=False)
                stats['performance_by_channel'] = perf.to_dict()
        
        # All numeric stats
        num_cols = df.select_dtypes(include=['float64','int64']).columns.tolist()[:5]
        for col in num_cols:
            stats[f"{col}_stats"] = {
                "total": round(df[col].sum(), 2),
                "mean": round(df[col].mean(), 2),
                "max": round(df[col].max(), 2)
            }
            
    except Exception as e:
        stats['error'] = str(e)
    return stats


def calculate_performance_stats(df, category_col, metric_col, stats):
    """Performance — score distributions, risk groups, attendance"""
    try:
        # Score column
        score_col = next((c for c in df.columns if any(s in c.lower() 
                         for s in ['score','mark','grade','result','point'])), metric_col)
        
        if score_col and score_col in df.columns:
            stats['score_stats'] = {
                "mean": round(df[score_col].mean(), 2),
                "min": round(df[score_col].min(), 2),
                "max": round(df[score_col].max(), 2),
                "median": round(df[score_col].median(), 2)
            }
            
            # Score distribution
            score_dist = df[score_col].value_counts().sort_index()
            pcts = (df[score_col].value_counts(normalize=True) * 100).round(1)
            stats['score_distribution'] = {
                str(k): f"{v} ({pcts.get(k, 0)}%)" 
                for k, v in score_dist.items()
            }
        
        # Category groupings
        cat_cols = [c for c in df.select_dtypes(include=['object']).columns 
                   if df[c].nunique() < 30][:3]
        
        for col in cat_cols:
            counts = df[col].value_counts()
            pcts = (df[col].value_counts(normalize=True) * 100).round(1)
            stats[f"{col}_distribution"] = {
                str(k): f"{v} ({pcts[k]}%)" 
                for k, v in counts.items()
            }
            
            if score_col and score_col in df.columns:
                avg_score = df.groupby(col)[score_col].mean().round(2).sort_values()
                stats[f"avg_score_by_{col}"] = avg_score.to_dict()
        
        # Attendance
        attendance_col = next((c for c in df.columns if 'attend' in c.lower()), None)
        if attendance_col and attendance_col in df.columns:
            stats['attendance_stats'] = {
                "mean": round(df[attendance_col].mean(), 2),
                "distribution": df[attendance_col].value_counts().to_dict()
            }
            
    except Exception as e:
        stats['error'] = str(e)
    return stats


def calculate_healthcare_stats(df, category_col, metric_col, stats):
    """Healthcare — diagnosis distributions, treatment outcomes, vitals"""
    try:
        # Diagnosis/condition column
        diagnosis_col = next((c for c in df.columns if any(d in c.lower() 
                             for d in ['diagnosis','condition','disease','illness','disorder'])), category_col)
        
        if diagnosis_col and diagnosis_col in df.columns and df[diagnosis_col].nunique() < 50:
            counts = df[diagnosis_col].value_counts().head(10)
            pcts = (df[diagnosis_col].value_counts(normalize=True) * 100).round(1).head(10)
            stats['diagnosis_distribution'] = {
                str(k): f"{v} ({pcts[k]}%)" 
                for k, v in counts.items()
            }
        
        # Outcome analysis
        outcome_col = next((c for c in df.columns if any(o in c.lower() 
                           for o in ['outcome','result','status','recovery','discharge'])), None)
        if outcome_col and outcome_col in df.columns and df[outcome_col].nunique() < 20:
            stats['outcome_distribution'] = df[outcome_col].value_counts().to_dict()
        
        # Vitals/numeric stats
        num_cols = df.select_dtypes(include=['float64','int64']).columns.tolist()[:5]
        for col in num_cols:
            stats[f"{col}_stats"] = {
                "mean": round(df[col].mean(), 2),
                "min": round(df[col].min(), 2),
                "max": round(df[col].max(), 2),
                "median": round(df[col].median(), 2)
            }
            
    except Exception as e:
        stats['error'] = str(e)
    return stats


def calculate_general_stats(df, stats):
    """General — safe stats that work for any dataset"""
    try:
        # Only low cardinality categoricals
        cat_cols = [c for c in df.select_dtypes(include=['object']).columns 
                   if df[c].nunique() < 20][:3]
        
        for col in cat_cols:
            counts = df[col].value_counts().head(10)
            pcts = (df[col].value_counts(normalize=True) * 100).round(1).head(10)
            stats[f"{col}_distribution"] = {
                str(k): f"{v} ({pcts[k]}%)" 
                for k, v in counts.items()
            }
        
        # All numeric columns
        num_cols = df.select_dtypes(include=['float64','int64']).columns.tolist()[:5]
        for col in num_cols:
            stats[f"{col}_stats"] = {
                "mean": round(df[col].mean(), 2),
                "min": round(df[col].min(), 2),
                "max": round(df[col].max(), 2),
                "median": round(df[col].median(), 2)
            }
            
    except Exception as e:
        stats['error'] = str(e)
    return stats

