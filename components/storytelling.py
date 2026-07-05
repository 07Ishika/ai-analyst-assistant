import streamlit as st
from utils.groq_helper import ask_groq
import json
import plotly.graph_objects as go
import plotly.express as px

def get_storytelling(df, problem, insights, business_context):
    prompt = f"""
You are a senior data analyst presenting findings to a non-technical business audience.

Business Problem: {problem}

Business Context:
- High value means: {business_context.get('high_means', 'not specified')}
- Low value means: {business_context.get('low_means', 'not specified')}
- Audience: {business_context.get('audience', 'business stakeholders')}
- Decisions to be made: {business_context.get('decisions', 'not specified')}

Key Insights found: {insights}

Dataset info:
Columns: {df.columns.tolist()}
Shape: {df.shape}

Return ONLY this JSON object — write everything in simple plain English a 10 year old can understand:
{{
  "headline": "one powerful sentence — the single most important finding",
  "what_we_found": "2 sentences — what the data clearly shows, use simple words",
  "why_it_matters": "2 sentences — why this is important for the business right now",
  "what_to_do": "2 sentences — exactly what action should be taken",
  "expected_outcome": "1 sentence — what good thing will happen if action is taken",
  "urgency": "high or medium or low",
  "urgency_reason": "one sentence why this urgency level",
  "key_number_1_label": "short label for most important metric",
  "key_number_1_value": "the actual number or value",
  "key_number_2_label": "short label for second important metric",
  "key_number_2_value": "the actual number or value",
  "key_number_3_label": "short label for third important metric",
  "key_number_3_value": "the actual number or value"
}}

Rules:
- Use words a non technical manager would use
- No jargon like correlation, regression, distribution
- Every sentence must be actionable or informative
- Key numbers must come from actual data
- Return ONLY the JSON object
    """
    response = ask_groq(
        prompt,
        system_message="""You are a business storyteller. 
        You explain data findings in the simplest possible language.
        You only output valid JSON objects.""",
        temperature=0.3
    )
    return response

def show_urgency_badge(urgency, reason):
    colors = {
        "high": ("#FF4444", "🔴 HIGH URGENCY"),
        "medium": ("#FF8C00", "🟡 MEDIUM URGENCY"),
        "low": ("#00CC44", "🟢 LOW URGENCY")
    }
    color, label = colors.get(urgency.lower(), ("#888888", "⚪ UNKNOWN"))
    st.markdown(f"""
    <div style='background-color: {color}; padding: 10px 20px; 
    border-radius: 25px; display: inline-block; margin: 10px 0'>
    <span style='color: white; font-weight: bold; font-size: 16px'>{label}</span>
    </div>
    <p style='color: {color}; font-size: 14px; margin-top: 5px'>{reason}</p>
    """, unsafe_allow_html=True)

def show_storytelling(df):
    st.header("Step 5 — Business Story Dashboard")
    st.write("Your insights presented as a clear business dashboard")

    # Check if insights exist
    if "ai_insights" not in st.session_state:
        st.warning("⚠️ Please complete Step 4 — Insights first!")
        if st.button("← Go back to Insights"):
            st.session_state.current_step = 4
            st.rerun()
        return

    if "business_problem" not in st.session_state:
        st.warning("⚠️ Please define your business problem in Step 4 first!")
        if st.button("← Go back to Define Problem"):
            st.session_state.current_step = 4
            st.rerun()
        return

    # Problem statement banner
    st.markdown(f"""
    <div style='background-color: #f8f9fa; padding: 15px; 
    border-radius: 10px; border-left: 5px solid #2196F3; margin: 10px 0'>
    <p style='margin: 0; color: #666; font-size: 12px'>BUSINESS QUESTION</p>
    <h4 style='margin: 5px 0 0 0'>{st.session_state.business_problem}</h4>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    if st.button("✨ Generate Business Dashboard"):
        with st.spinner("AI is creating your business story..."):
            raw_response = get_storytelling(
                df,
                st.session_state.business_problem,
                st.session_state.ai_insights,
                st.session_state.get('business_context', {})
            )
            try:
                clean_response = raw_response.strip()
                if "```json" in clean_response:
                    clean_response = clean_response.split("```json")[1].split("```")[0]
                elif "```" in clean_response:
                    clean_response = clean_response.split("```")[1].split("```")[0]
                start = clean_response.find("{")
                end = clean_response.rfind("}") + 1
                if start != -1 and end != 0:
                    clean_response = clean_response[start:end]
                story = json.loads(clean_response)
                st.session_state.story = story
            except Exception as e:
                st.error(f"Could not parse story: {e}")
                st.write("Raw response:", raw_response)

    if "story" in st.session_state:
        story = st.session_state.story

        # Section 1 — Headline + Urgency
        st.markdown(f"""
        <div style='background-color: #1E3A5F; padding: 25px; 
        border-radius: 15px; margin: 15px 0; text-align: center'>
        <p style='color: #90CAF9; margin: 0; font-size: 13px; letter-spacing: 2px'>MAIN FINDING</p>
        <h2 style='color: white; margin: 10px 0 0 0; line-height: 1.4'>
        {story.get('headline', '')}
        </h2>
        </div>
        """, unsafe_allow_html=True)

        # Urgency badge
        show_urgency_badge(
            story.get('urgency', 'medium'),
            story.get('urgency_reason', '')
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # Section 2 — Key Numbers (big and visual)
        st.markdown("### 📊 Key Numbers at a Glance")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"""
            <div style='background-color: #E3F2FD; padding: 20px; 
            border-radius: 15px; text-align: center; border: 2px solid #2196F3'>
            <p style='color: #1565C0; font-size: 13px; margin: 0; font-weight: bold'>
            {story.get('key_number_1_label', '').upper()}</p>
            <h1 style='color: #1565C0; margin: 10px 0; font-size: 36px'>
            {story.get('key_number_1_value', '-')}</h1>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div style='background-color: #F3E5F5; padding: 20px; 
            border-radius: 15px; text-align: center; border: 2px solid #9C27B0'>
            <p style='color: #6A1B9A; font-size: 13px; margin: 0; font-weight: bold'>
            {story.get('key_number_2_label', '').upper()}</p>
            <h1 style='color: #6A1B9A; margin: 10px 0; font-size: 36px'>
            {story.get('key_number_2_value', '-')}</h1>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div style='background-color: #E8F5E9; padding: 20px; 
            border-radius: 15px; text-align: center; border: 2px solid #4CAF50'>
            <p style='color: #2E7D32; font-size: 13px; margin: 0; font-weight: bold'>
            {story.get('key_number_3_label', '').upper()}</p>
            <h1 style='color: #2E7D32; margin: 10px 0; font-size: 36px'>
            {story.get('key_number_3_value', '-')}</h1>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Section 3 — Story Cards
        st.markdown("### 📖 The Full Story")

        st.markdown(f"""
        <div style='background-color: #E3F2FD; padding: 20px; 
        border-radius: 12px; margin: 10px 0'>
        <p style='color: #1565C0; font-size: 12px; font-weight: bold; 
        margin: 0; letter-spacing: 1px'>🔍 WHAT WE FOUND</p>
        <p style='font-size: 16px; margin: 10px 0 0 0; line-height: 1.6'>
        {story.get('what_we_found', '')}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style='background-color: #FFF3E0; padding: 20px; 
        border-radius: 12px; margin: 10px 0'>
        <p style='color: #E65100; font-size: 12px; font-weight: bold; 
        margin: 0; letter-spacing: 1px'>⚡ WHY IT MATTERS</p>
        <p style='font-size: 16px; margin: 10px 0 0 0; line-height: 1.6'>
        {story.get('why_it_matters', '')}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style='background-color: #E8F5E9; padding: 20px; 
        border-radius: 12px; margin: 10px 0'>
        <p style='color: #2E7D32; font-size: 12px; font-weight: bold; 
        margin: 0; letter-spacing: 1px'>✅ WHAT TO DO</p>
        <p style='font-size: 16px; margin: 10px 0 0 0; line-height: 1.6'>
        {story.get('what_to_do', '')}</p>
        </div>
        """, unsafe_allow_html=True)

        # Expected outcome
        st.markdown(f"""
        <div style='background-color: #1E3A5F; padding: 20px; 
        border-radius: 12px; margin: 10px 0; text-align: center'>
        <p style='color: #90CAF9; font-size: 12px; font-weight: bold; 
        margin: 0; letter-spacing: 1px'>💡 EXPECTED OUTCOME</p>
        <p style='color: white; font-size: 18px; margin: 10px 0 0 0; 
        font-style: italic; line-height: 1.6'>
        {story.get('expected_outcome', '')}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Section 4 — Copy ready summary
        st.markdown("### 📄 Ready to Share")
        st.write("Copy this summary for your email or presentation")

        full_story = f"""
📊 BUSINESS ANALYSIS REPORT
{'='*50}

❓ BUSINESS QUESTION:
{st.session_state.business_problem}

📰 MAIN FINDING:
{story.get('headline', '')}

🔍 WHAT WE FOUND:
{story.get('what_we_found', '')}

⚡ WHY IT MATTERS:
{story.get('why_it_matters', '')}

✅ WHAT TO DO:
{story.get('what_to_do', '')}

💡 EXPECTED OUTCOME:
{story.get('expected_outcome', '')}

📊 KEY NUMBERS:
- {story.get('key_number_1_label', '')}: {story.get('key_number_1_value', '')}
- {story.get('key_number_2_label', '')}: {story.get('key_number_2_value', '')}
- {story.get('key_number_3_label', '')}: {story.get('key_number_3_value', '')}

🚨 URGENCY: {story.get('urgency', '').upper()}
{story.get('urgency_reason', '')}
        """

        st.text_area(
            "Copy this report",
            value=full_story,
            height=400
        )

        st.divider()
        if st.button("Proceed to Export →"):
            st.session_state.current_step = 6
            st.rerun()
            