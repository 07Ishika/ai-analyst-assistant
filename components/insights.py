import streamlit as st
import plotly.express as px
import json
from utils.groq_helper import ask_groq

def get_chart_suggestions(df):
    prompt = f"""
You are a senior data analyst. Think step by step before suggesting charts.

For each column in this dataset, think:
STEP 1 - What kind of column is this? (identifier, categorical, numeric, date)
STEP 2 - Is this column meaningful to visualize? (IDs, unique identifiers, zip codes with too many values are NOT meaningful)
STEP 3 - If meaningful, what chart type makes most sense?
STEP 4 - What business question does this chart answer?
STEP 5 - What should the analyst look for in this chart?

After thinking, return ONLY a JSON array of meaningful charts.
Skip any column that is an ID, unique identifier, or has too many unique values to be meaningful.

Return this exact structure:
[
  {{
    "column": "exact column name",
    "chart_type": "bar or histogram or pie",
    "title": "meaningful chart title",
    "what_it_shows": "one sentence what this chart shows",
    "what_to_look_for": "one sentence what analyst should look for",
    "business_value": "one sentence why this matters for business"
  }}
]

Dataset Info:
Columns: {df.columns.tolist()}
Data Types: {df.dtypes.astype(str).to_dict()}
Sample Data: {df.head(5).to_string()}
Unique counts per column: {df.nunique().to_dict()}
Total rows: {df.shape[0]}

Rules:
- If unique count of a column is more than 50% of total rows — it is likely an ID or code — SKIP IT
- Zip codes, postal codes, ID columns — always SKIP
- Only suggest maximum 3 most valuable charts
- Return ONLY the JSON array, no other text
    """
    response = ask_groq(
        prompt,
        system_message="""You are a senior data analyst and visualization expert. 
        You think carefully about which charts actually add business value. 
        You never suggest charts for ID columns, zip codes, or columns with too many unique values.
        You only output valid JSON arrays.""",
        temperature=0.0
    )
    return response

def get_relevant_columns(df, problem):
    prompt = f"""
You are a data analyst. Given this business problem and dataset columns, 
identify which columns are most relevant to answer the problem.

Business Problem: {problem}

Available Columns: {df.columns.tolist()}
Data Types: {df.dtypes.astype(str).to_dict()}
Sample Data: {df.head(3).to_string()}

Return ONLY a JSON object:
{{
  "primary_column": "the single most important column to answer this problem",
  "secondary_columns": ["other relevant column 1", "other relevant column 2"],
  "numeric_columns": ["numeric columns relevant to this problem"]
}}

Rules:
- Primary column must directly relate to the business problem
- Maximum 2 secondary columns
- Maximum 2 numeric columns
- Return ONLY the JSON object
    """
    response = ask_groq(
        prompt,
        system_message="You are a data analyst. You only output valid JSON objects.",
        temperature=0.0
    )
    return response

def get_ai_insights(df, problem, business_context):

    # Step 1 — Find relevant columns for this specific problem
    try:
        raw_cols = get_relevant_columns(df, problem)
        clean = raw_cols.strip()
        if "```json" in clean:
            clean = clean.split("```json")[1].split("```")[0]
        elif "```" in clean:
            clean = clean.split("```")[1].split("```")[0]
        start = clean.find("{")
        end = clean.rfind("}") + 1
        clean = clean[start:end]
        relevant = json.loads(clean)
        primary_col = relevant.get("primary_column", "")
        secondary_cols = relevant.get("secondary_columns", [])
        numeric_cols = relevant.get("numeric_columns", [])
    except:
        # Fallback to auto detection
        primary_col = df.select_dtypes(include=['object']).columns[0] if len(df.select_dtypes(include=['object']).columns) > 0 else ""
        secondary_cols = []
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()[:2]

    # Step 2 — Calculate focused stats for relevant columns
    focused_stats = {}

    # Primary column stats
    if primary_col and primary_col in df.columns:
        counts = df[primary_col].value_counts()
        percentages = (df[primary_col].value_counts(normalize=True) * 100).round(1)
        focused_stats[f"{primary_col}_distribution"] = {
            str(k): f"{v} donors ({percentages[k]}%)"
            for k, v in counts.items()
        }

        # Cross stats — primary column vs numeric columns
        for num_col in numeric_cols:
            if num_col in df.columns:
                cross = df.groupby(primary_col)[num_col].mean().round(2).sort_values()
                cross_dict = cross.to_dict()
                # Add clear highest and lowest labels
                cross_dict['__lowest__'] = f"{cross.index[0]} ({cross.iloc[0]})"
                cross_dict['__highest__'] = f"{cross.index[-1]} ({cross.iloc[-1]})"
                focused_stats[f"avg_{num_col}_by_{primary_col}"] = cross_dict
                
    # Secondary columns stats
    for col in secondary_cols:
        if col in df.columns and df[col].nunique() < 50:
            counts = df[col].value_counts()
            percentages = (df[col].value_counts(normalize=True) * 100).round(1)
            focused_stats[f"{col}_distribution"] = {
                str(k): f"{v} ({percentages[k]}%)"
                for k, v in counts.items()
            }

    # Overall numeric stats
    overall_numeric = {}
    for col in numeric_cols:
        if col in df.columns:
            overall_numeric[col] = {
                "mean": round(df[col].mean(), 2),
                "min": round(df[col].min(), 2),
                "max": round(df[col].max(), 2),
                "median": round(df[col].median(), 2)
            }

    prompt = f"""
You are a senior data analyst AND business strategist.
Your ONLY job is to answer this specific business problem using real data.

BUSINESS PROBLEM: {problem}

Business Context:
- High value means: {business_context.get('high_means', 'not specified')}
- Low value means: {business_context.get('low_means', 'not specified')}
- Audience: {business_context.get('audience', 'business stakeholders')}
- Decisions to be made: {business_context.get('decisions', 'not specified')}
- Additional context: {business_context.get('additional_context', 'none')}

MOST RELEVANT COLUMN FOR THIS PROBLEM: {primary_col}
SUPPORTING COLUMNS: {secondary_cols}

FOCUSED STATISTICS — use ONLY these numbers:
{focused_stats}

OVERALL NUMERIC STATS:
{overall_numeric}

Total rows: {df.shape[0]}

Return ONLY this JSON object:
{{
  "key_insights": [
    "insight directly answering the business problem with real numbers",
    "insight 2 with real numbers from focused stats",
    "insight 3 with real numbers"
  ],
  "patterns": [
    "pattern directly related to business problem with real numbers",
    "pattern 2"
  ],
  "anomalies": [
    "anomaly related to business problem in plain business language",
    "anomaly 2"
  ],
  "recommendations": [
    "recommendation directly addressing business problem with evidence",
    "recommendation 2",
    "recommendation 3"
  ]
}}

Rules:
- EVERY insight must directly relate to the business problem
- ONLY use numbers from focused statistics above
- Never make up numbers
- Plain business language — no jargon
- Return ONLY the JSON object
    """
    response = ask_groq(
        prompt,
        system_message="""You are a senior data analyst.
        You ONLY answer the specific business problem asked.
        You ONLY use real numbers from provided statistics.
        You NEVER hallucinate or make up numbers.
        You only output valid JSON objects.""",
        temperature=0.1
    )
    return response

def parse_json_response(raw_response, expected_type="array"):
    clean_response = raw_response.strip()
    if "```json" in clean_response:
        clean_response = clean_response.split("```json")[1].split("```")[0]
    elif "```" in clean_response:
        clean_response = clean_response.split("```")[1].split("```")[0]
    if expected_type == "array":
        start = clean_response.find("[")
        end = clean_response.rfind("]") + 1
    else:
        start = clean_response.find("{")
        end = clean_response.rfind("}") + 1
    if start != -1 and end != 0:
        clean_response = clean_response[start:end]
    return json.loads(clean_response)

def show_chart(df, suggestion):
    col = suggestion['column']
    chart_type = suggestion['chart_type']
    st.markdown(f"""
    <div style='background-color: #f8f9fa; padding: 12px; 
    border-radius: 8px; border-left: 4px solid #636EFA; margin: 10px 0'>
    <h4>📊 {suggestion['title']}</h4>
    <p><b>What it shows:</b> {suggestion['what_it_shows']}</p>
    <p><b>What to look for:</b> {suggestion['what_to_look_for']}</p>
    <p><b>Business value:</b> {suggestion['business_value']}</p>
    </div>
    """, unsafe_allow_html=True)
    try:
        if chart_type == "histogram":
            fig = px.histogram(df, x=col, title=suggestion['title'],
                color_discrete_sequence=["#636EFA"])
            st.plotly_chart(fig, use_container_width=True)
        elif chart_type == "bar":
            top_values = df[col].value_counts().head(10)
            fig = px.bar(x=top_values.index, y=top_values.values,
                title=suggestion['title'],
                labels={"x": col, "y": "Count"},
                color_discrete_sequence=["#00CC96"])
            st.plotly_chart(fig, use_container_width=True)
        elif chart_type == "pie":
            top_values = df[col].value_counts().head(8)
            fig = px.pie(values=top_values.values, names=top_values.index,
                title=suggestion['title'])
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Could not render chart for {col}: {e}")

def show_insights(df):
    st.header("Step 4 — Define Problem & Get Insights")

    # Section 1 — Define Business Problem
    st.subheader("1️⃣ Define Your Business Problem")
    st.info("💡 Tip — Be specific about what you want to find out. The more specific your problem, the better the insights!")
    problem = st.text_area(
        "What is the business problem or question you want to solve?",
        placeholder="Example: Which customer states have the most customers and which are underrepresented?",
        height=100
    )
    if problem:
        st.session_state.business_problem = problem

    st.divider()

    # Section 2 — Business Context
    st.subheader("2️⃣ Help AI Understand Your Business Context")
    st.write("This helps AI give insights that match YOUR business — not generic advice")
    col1, col2 = st.columns(2)
    with col1:
        high_means = st.text_input(
            "High value in your data means —",
            placeholder="e.g. already saturated market",
            key="high_means"
        )
        audience = st.text_input(
            "Who will read these insights?",
            placeholder="e.g. marketing team, CEO",
            key="audience"
        )
    with col2:
        low_means = st.text_input(
            "Low value in your data means —",
            placeholder="e.g. opportunity for growth",
            key="low_means"
        )
        decisions = st.text_input(
            "What decisions will be made from insights?",
            placeholder="e.g. where to spend marketing budget",
            key="decisions"
        )
    additional_context = st.text_area(
        "Any additional context AI should know? (optional)",
        placeholder="e.g. passing score is 5 out of 10, Q4 is peak season, O- blood is most critical...",
        height=80,
        key="additional_context"
    )

    if high_means and low_means and audience and decisions:
        st.session_state.business_context = {
            "high_means": high_means,
            "low_means": low_means,
            "audience": audience,
            "decisions": decisions,
            "additional_context": additional_context
        }
        st.success("✅ Business context saved!")

    st.divider()

    # Section 3 — Smart Charts
    st.subheader("3️⃣ Smart Visualizations")
    st.write("AI will decide which charts actually make sense for your data")
    if st.button("📊 Generate Smart Charts"):
        with st.spinner("AI is thinking about which charts make sense..."):
            raw_response = get_chart_suggestions(df)
            try:
                chart_suggestions = parse_json_response(raw_response, "array")
                filtered = []
                for s in chart_suggestions:
                    col = s['column']
                    if col in df.columns:
                        unique_ratio = df[col].nunique() / len(df)
                        if unique_ratio < 0.2:
                            filtered.append(s)
                st.session_state.chart_suggestions = filtered
                st.success(f"✅ Found {len(filtered)} meaningful charts!")
            except Exception as e:
                st.error(f"Could not parse chart suggestions: {e}")
                st.write("Raw response:", raw_response)

    if "chart_suggestions" in st.session_state:
        if len(st.session_state.chart_suggestions) == 0:
            st.warning("No meaningful charts found for this dataset.")
        else:
            for suggestion in st.session_state.chart_suggestions:
                show_chart(df, suggestion)

    st.divider()

    # Section 4 — AI Insights
    st.subheader("4️⃣ AI Insights Based on Your Problem")
    if st.button("🤖 Get AI Insights"):
        if "business_problem" not in st.session_state or not st.session_state.business_problem:
            st.error("⚠️ Please define your business problem first!")
        elif "business_context" not in st.session_state:
            st.error("⚠️ Please fill in the business context first!")
        else:
            with st.spinner("AI is analyzing your data step by step..."):
                raw_response = get_ai_insights(
                    df,
                    st.session_state.business_problem,
                    st.session_state.business_context
                )
                try:
                    insights = parse_json_response(raw_response, "object")
                    st.session_state.ai_insights = insights
                except Exception as e:
                    st.error(f"Could not parse insights: {e}")
                    st.write("Raw response:", raw_response)

    if "ai_insights" in st.session_state:
        insights = st.session_state.ai_insights

        # Key Insights — Blue
        if "key_insights" in insights:
            st.markdown("""
            <div style='background-color: #e8f4fd; padding: 15px; 
            border-radius: 10px; border-left: 5px solid #2196F3; margin: 10px 0'>
            <h4>💡 Key Insights</h4>
            </div>
            """, unsafe_allow_html=True)
            for insight in insights["key_insights"]:
                st.markdown(f"""
                <div style='background-color: #f0f8ff; padding: 10px; 
                border-radius: 6px; margin: 5px 0'>
                • {insight}
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Patterns — Purple
        if "patterns" in insights:
            st.markdown("""
            <div style='background-color: #f3e8fd; padding: 15px; 
            border-radius: 10px; border-left: 5px solid #9C27B0; margin: 10px 0'>
            <h4>📈 Patterns & Trends</h4>
            </div>
            """, unsafe_allow_html=True)
            for pattern in insights["patterns"]:
                st.markdown(f"""
                <div style='background-color: #faf0ff; padding: 10px; 
                border-radius: 6px; margin: 5px 0'>
                • {pattern}
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Anomalies — Red
        if "anomalies" in insights:
            st.markdown("""
            <div style='background-color: #fde8e8; padding: 15px; 
            border-radius: 10px; border-left: 5px solid #F44336; margin: 10px 0'>
            <h4>⚠️ Anomalies</h4>
            </div>
            """, unsafe_allow_html=True)
            for anomaly in insights["anomalies"]:
                st.markdown(f"""
                <div style='background-color: #fff5f5; padding: 10px; 
                border-radius: 6px; margin: 5px 0'>
                • {anomaly}
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Recommendations — Green
        if "recommendations" in insights:
            st.markdown("""
            <div style='background-color: #e8fde8; padding: 15px; 
            border-radius: 10px; border-left: 5px solid #4CAF50; margin: 10px 0'>
            <h4>✅ Recommendations</h4>
            </div>
            """, unsafe_allow_html=True)
            for rec in insights["recommendations"]:
                st.markdown(f"""
                <div style='background-color: #f0fff0; padding: 10px; 
                border-radius: 6px; margin: 5px 0'>
                • {rec}
                </div>
                """, unsafe_allow_html=True)

        st.divider()
        if st.button("Proceed to Storytelling →"):
            st.session_state.current_step = 5
            st.rerun()