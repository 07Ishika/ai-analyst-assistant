import streamlit as st
import pandas as pd
from datetime import datetime
import base64
import io
import re

def md_to_html(text):
    if not text:
        return ""
    # Bold
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    # Italic
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
    # Convert bullet points
    lines = text.split('\n')
    html_lines = []
    in_list = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('* ') or stripped.startswith('- '):
            if not in_list:
                html_lines.append('<ul>')
                in_list = True
            html_lines.append(f"<li>{stripped[2:]}</li>")
        else:
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            if stripped:
                html_lines.append(f"<p>{stripped}</p>")
    if in_list:
        html_lines.append('</ul>')
    return '\n'.join(html_lines)

def generate_report_html(df, session_state):

    now = datetime.now().strftime("%B %d, %Y %I:%M %p")
    cleaned_df = session_state.get('cleaned_df', df)
    business_problem = session_state.get('business_problem', 'Not defined')
    ai_understanding = session_state.get('ai_understanding', 'Not generated')
    applied_actions = session_state.get('applied_actions', [])
    ai_insights = session_state.get('ai_insights', {})
    story = session_state.get('story', {})
    business_context = session_state.get('business_context', {})

    # Cleaning actions
    cleaning_rows = ""
    if applied_actions:
        for action in applied_actions:
            parts = action.split("_", 1)
            if len(parts) == 2:
                cleaning_rows += f"<tr><td>{parts[1]}</td><td>{parts[0]}</td><td>✅ Applied</td></tr>"
    else:
        cleaning_rows = "<tr><td colspan='3'>No cleaning actions applied</td></tr>"

    # Insights sections
    def build_insight_section(title, emoji, color, border, items):
        if not items:
            return ""
        items_html = "".join([f"<li>{item}</li>" for item in items])
        return f"""
        <div style='background:{color}; border-left:5px solid {border}; 
        padding:15px; border-radius:8px; margin:10px 0'>
        <h4 style='margin:0 0 10px 0'>{emoji} {title}</h4>
        <ul style='margin:0; padding-left:20px'>{items_html}</ul>
        </div>
        """

    insights_html = ""
    if ai_insights:
        insights_html += build_insight_section("Key Insights", "💡", "#E3F2FD", "#2196F3", ai_insights.get("key_insights", []))
        insights_html += build_insight_section("Patterns & Trends", "📈", "#F3E5F5", "#9C27B0", ai_insights.get("patterns", []))
        insights_html += build_insight_section("Anomalies", "⚠️", "#FFEBEE", "#F44336", ai_insights.get("anomalies", []))
        insights_html += build_insight_section("Recommendations", "✅", "#E8F5E9", "#4CAF50", ai_insights.get("recommendations", []))

    # Story section
    story_html = ""
    if story:
        story_html = f"""
        <div style='background:#1E3A5F; padding:20px; border-radius:10px; 
        text-align:center; margin:15px 0'>
        <h2 style='color:white; margin:0'>{story.get('headline','')}</h2>
        </div>

        <div style='display:grid; grid-template-columns:1fr 1fr 1fr; gap:15px; margin:15px 0'>
        <div style='background:#E3F2FD; padding:15px; border-radius:10px; text-align:center'>
        <p style='color:#1565C0; font-size:11px; margin:0; font-weight:bold'>
        {story.get('key_number_1_label','').upper()}</p>
        <h1 style='color:#1565C0; margin:5px 0'>{story.get('key_number_1_value','-')}</h1>
        </div>
        <div style='background:#F3E5F5; padding:15px; border-radius:10px; text-align:center'>
        <p style='color:#6A1B9A; font-size:11px; margin:0; font-weight:bold'>
        {story.get('key_number_2_label','').upper()}</p>
        <h1 style='color:#6A1B9A; margin:5px 0'>{story.get('key_number_2_value','-')}</h1>
        </div>
        <div style='background:#E8F5E9; padding:15px; border-radius:10px; text-align:center'>
        <p style='color:#2E7D32; font-size:11px; margin:0; font-weight:bold'>
        {story.get('key_number_3_label','').upper()}</p>
        <h1 style='color:#2E7D32; margin:5px 0'>{story.get('key_number_3_value','-')}</h1>
        </div>
        </div>

        <div style='background:#E3F2FD; padding:15px; border-radius:10px; margin:10px 0'>
        <p style='color:#1565C0; font-size:11px; font-weight:bold; margin:0'>🔍 WHAT WE FOUND</p>
        <p style='margin:8px 0 0 0'>{story.get('what_we_found','')}</p>
        </div>

        <div style='background:#FFF3E0; padding:15px; border-radius:10px; margin:10px 0'>
        <p style='color:#E65100; font-size:11px; font-weight:bold; margin:0'>⚡ WHY IT MATTERS</p>
        <p style='margin:8px 0 0 0'>{story.get('why_it_matters','')}</p>
        </div>

        <div style='background:#E8F5E9; padding:15px; border-radius:10px; margin:10px 0'>
        <p style='color:#2E7D32; font-size:11px; font-weight:bold; margin:0'>✅ WHAT TO DO</p>
        <p style='margin:8px 0 0 0'>{story.get('what_to_do','')}</p>
        </div>

        <div style='background:#1E3A5F; padding:15px; border-radius:10px; 
        margin:10px 0; text-align:center'>
        <p style='color:#90CAF9; font-size:11px; font-weight:bold; margin:0'>
        💡 EXPECTED OUTCOME</p>
        <p style='color:white; font-style:italic; margin:8px 0 0 0'>
        {story.get('expected_outcome','')}</p>
        </div>
        """

    # Column table
    col_rows = "".join([
        f"<tr><td>{col}</td><td>{str(df[col].dtype)}</td><td>{df[col].isnull().sum()}</td></tr>"
        for col in df.columns
    ])

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8">
    <title>AI Analyst Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 30px;
            color: #333;
            background: white;
        }}
        h1, h2, h3, h4 {{ color: #1E3A5F; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
            font-size: 13px;
        }}
        th {{
            background: #1E3A5F;
            color: white;
            padding: 10px;
            text-align: left;
        }}
        td {{
            padding: 8px 10px;
            border-bottom: 1px solid #e0e0e0;
        }}
        tr:nth-child(even) {{ background: #f8f9fa; }}
        .step-header {{
            background: #1E3A5F;
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            margin: 25px 0 15px 0;
        }}
        .step-header h3 {{ color: white; margin: 0; }}
        .divider {{
            border: none;
            border-top: 2px solid #e0e0e0;
            margin: 25px 0;
        }}
        .stat-box {{
            display: inline-block;
            background: #f8f9fa;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px 25px;
            margin: 5px;
            text-align: center;
            min-width: 120px;
        }}
        .stat-box h2 {{
            color: #1E3A5F;
            margin: 5px 0;
            font-size: 28px;
        }}
        .stat-box p {{
            color: #666;
            margin: 0;
            font-size: 12px;
        }}
        ul {{ line-height: 1.8; }}
        p {{ line-height: 1.7; }}
        @media print {{
            .no-print {{ display: none; }}
            body {{ padding: 15px; }}
        }}
    </style>
    </head>
    <body>

    <!-- Report Header -->
    <div style='background:#1E3A5F; color:white; padding:30px; 
    border-radius:15px; text-align:center; margin-bottom:30px'>
    <h1 style='color:white; margin:0; font-size:28px'>📊 AI Analyst Report</h1>
    <p style='margin:10px 0 0 0; opacity:0.8'>Generated on {now}</p>
    </div>

    <!-- Step 1 — Dataset Overview -->
    <div class='step-header'><h3>📁 Step 1 — Dataset Overview</h3></div>

    <div>
    <div class='stat-box'>
        <p>Total Rows</p>
        <h2>{df.shape[0]:,}</h2>
    </div>
    <div class='stat-box'>
        <p>Total Columns</p>
        <h2>{df.shape[1]}</h2>
    </div>
    <div class='stat-box'>
        <p>Missing Values</p>
        <h2>{df.isnull().sum().sum()}</h2>
    </div>
    <div class='stat-box'>
        <p>Duplicate Rows</p>
        <h2>{df.duplicated().sum()}</h2>
    </div>
    </div>

    <h4>Column Details</h4>
    <table>
    <tr><th>Column Name</th><th>Data Type</th><th>Missing Values</th></tr>
    {col_rows}
    </table>

    <hr class='divider'>

    <!-- Step 2 — AI Understanding -->
    <div class='step-header'><h3>🔍 Step 2 — AI Understanding</h3></div>
    <div style='background:#f8f9fa; padding:15px; border-radius:8px; line-height:1.7'>
    {md_to_html(ai_understanding)}
    </div>

    <hr class='divider'>

    <!-- Step 3 — Cleaning -->
    <div class='step-header'><h3>🧹 Step 3 — Cleaning & Transformation</h3></div>

    <div>
    <div class='stat-box'>
        <p>Original Rows</p>
        <h2>{df.shape[0]:,}</h2>
    </div>
    <div class='stat-box'>
        <p>After Cleaning</p>
        <h2>{cleaned_df.shape[0]:,}</h2>
    </div>
    <div class='stat-box'>
        <p>Rows Removed</p>
        <h2>{df.shape[0] - cleaned_df.shape[0]}</h2>
    </div>
    </div>

    <h4>Cleaning Actions Taken</h4>
    <table>
    <tr><th>Column</th><th>Action Applied</th><th>Status</th></tr>
    {cleaning_rows}
    </table>

    <hr class='divider'>

    <!-- Step 4 — Business Problem & Insights -->
    <div class='step-header'><h3>❓ Step 4 — Business Problem & Insights</h3></div>

    <div style='background:#E3F2FD; border-left:5px solid #2196F3; 
    padding:15px; border-radius:8px; margin:15px 0'>
    <p style='color:#1565C0; font-size:11px; margin:0; font-weight:bold'>
    BUSINESS QUESTION</p>
    <p style='font-size:16px; margin:8px 0 0 0; font-style:italic'>
    {business_problem}</p>
    </div>

    <div style='background:#f8f9fa; padding:15px; border-radius:8px; margin:15px 0'>
    <h4 style='margin:0 0 10px 0'>Business Context</h4>
    <p><b>High value means:</b> {business_context.get('high_means', 'Not specified')}</p>
    <p><b>Low value means:</b> {business_context.get('low_means', 'Not specified')}</p>
    <p><b>Audience:</b> {business_context.get('audience', 'Not specified')}</p>
    <p><b>Decisions:</b> {business_context.get('decisions', 'Not specified')}</p>
    <p><b>Additional context:</b> {business_context.get('additional_context', 'Not specified')}</p>
    <p><b>Passing threshold:</b> {business_context.get('passing_threshold', 'Not specified')}</p>
    </div>

    {insights_html}

    <hr class='divider'>

    <!-- Step 5 — Business Story -->
    <div class='step-header'><h3>📖 Step 5 — Business Story</h3></div>
    {story_html}

    <!-- Footer -->
    <hr class='divider'>
    <div style='text-align:center; color:#888; font-size:12px'>
    <p>Generated by AI Analyst Assistant</p>
    <p>This report contains AI generated insights — please verify before making business decisions</p>
    </div>

    </body>
    </html>
    """
    return html

def show_export(df):
    st.header("Step 6 — Export")
    st.write("Download your clean data and complete analysis report")

    cleaned_df = st.session_state.get('cleaned_df', df)

    st.divider()

    # Export 1 — Clean Data for Power BI
    st.subheader("1️⃣ Export Clean Data for Power BI")
    st.write("Download the cleaned dataset ready to import into Power BI")

    st.markdown("""
    <div style='background:#E3F2FD; padding:15px; border-radius:10px; 
    border-left:5px solid #2196F3; margin:10px 0'>
    <h4 style='margin:0 0 10px 0'>📋 How to import into Power BI</h4>
    <ol style='margin:0; padding-left:20px'>
    <li>Download the CSV file below</li>
    <li>Open Power BI Desktop</li>
    <li>Click <b>Home → Get Data → Text/CSV</b></li>
    <li>Select the downloaded CSV file</li>
    <li>Click <b>Load</b></li>
    <li>Your clean data is ready to visualize! 🎉</li>
    </ol>
    </div>
    """, unsafe_allow_html=True)

    st.link_button(
        "🚀 Open Power BI Website",
        "https://app.powerbi.com",
        help="Open Power BI in browser — then import your downloaded file"
    )

    col1, col2 = st.columns(2)
    with col1:
        csv = cleaned_df.to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"cleaned_data_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
        st.caption("Recommended for Power BI import")

    with col2:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            cleaned_df.to_excel(writer, index=False, sheet_name='Cleaned Data')
        buffer.seek(0)
        st.download_button(
            label="📥 Download as Excel",
            data=buffer,
            file_name=f"cleaned_data_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.caption("Alternative Excel format")

    st.write(f"**Clean data preview — {cleaned_df.shape[0]:,} rows × {cleaned_df.shape[1]} columns**")
    st.dataframe(cleaned_df.head(5))

    st.divider()

    # Export 2 — Full Analysis Report
    st.subheader("2️⃣ Download Full Analysis Report")
    st.write("Complete report of everything — dataset overview, cleaning, insights and business story")

    has_insights = "ai_insights" in st.session_state
    has_story = "story" in st.session_state
    has_understanding = "ai_understanding" in st.session_state

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"{'✅' if has_understanding else '❌'} AI Understanding")
    with col2:
        st.markdown(f"{'✅' if has_insights else '❌'} Insights")
    with col3:
        st.markdown(f"{'✅' if has_story else '❌'} Business Story")

    if not has_insights:
        st.warning("⚠️ Complete Step 4 — Insights for a full report")
    if not has_story:
        st.warning("⚠️ Complete Step 5 — Storytelling for a full report")

    if st.button("📄 Generate Report"):
        with st.spinner("Generating your complete analysis report..."):
            html_report = generate_report_html(df, st.session_state)
            st.session_state.html_report = html_report
            st.success("✅ Report generated!")

    if "html_report" in st.session_state:
        st.download_button(
            label="📥 Download Report (Open in browser → Print → Save as PDF)",
            data=st.session_state.html_report,
            file_name=f"analysis_report_{datetime.now().strftime('%Y%m%d')}.html",
            mime="text/html"
        )
        st.info("💡 How to save as PDF — Download → Open in Chrome → Ctrl+P → Save as PDF")

        st.subheader("Preview")
        st.components.v1.html(
            st.session_state.html_report,
            height=600,
            scrolling=True
        )
        