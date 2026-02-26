import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, inspect, text, Table, Column, MetaData, String

from services.excel_processor import process_student_excel

# ─────────────────────────────────────────────────────
# Database (SQLite — direct access, no API server)
# ─────────────────────────────────────────────────────
DB_PATH = "saveetha.db"
DATABASE_URL = f"sqlite:///./{DB_PATH}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def db_get_tables():
    return inspect(engine).get_table_names()


def db_get_all_data(table_name: str) -> pd.DataFrame:
    try:
        return pd.read_sql_table(table_name, engine)
    except Exception:
        return pd.DataFrame()


def db_get_student(table_name: str, roll_no: str):
    try:
        query = text(f"SELECT * FROM {table_name} WHERE roll_no_ = :roll")
        with engine.connect() as conn:
            result = conn.execute(query, {"roll": roll_no})
            row = result.fetchone()
        if row:
            return dict(row._mapping)
    except Exception:
        pass
    return None


def db_upload(df: pd.DataFrame, table_name: str):
    metadata = MetaData()
    columns = [Column(col, String) for col in df.columns]
    Table(table_name, metadata, *columns)
    metadata.create_all(engine)
    df.to_sql(table_name, engine, if_exists="append", index=False)


# ─────────────────────────────────────────────────────
# Page Config
# ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="Student Performance Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────
# Color Palette
# ─────────────────────────────────────────────────────
COLORS = {
    "card": "#1a1f2e",
    "accent": "#6c63ff",
    "accent2": "#00d4aa",
    "accent3": "#ff6b6b",
    "gradient1": "linear-gradient(135deg, #6c63ff 0%, #3b82f6 100%)",
    "gradient2": "linear-gradient(135deg, #00d4aa 0%, #00b894 100%)",
    "gradient3": "linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%)",
    "gradient4": "linear-gradient(135deg, #ffd93d 0%, #f39c12 100%)",
}

CHART_COLORS = [
    "#6c63ff", "#00d4aa", "#ff6b6b", "#ffd93d", "#3b82f6",
    "#e056cd", "#00b894", "#fd9644", "#a29bfe", "#55efc4",
]

PLOTLY_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#e0e0e0"),
    margin=dict(l=40, r=40, t=50, b=40),
    title_font_size=16,
    title_font_color="#ffffff",
)

# ─────────────────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    .stApp { font-family: 'Inter', sans-serif; }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f1320 0%, #161b2e 100%);
        border-right: 1px solid #2a3050;
    }
    section[data-testid="stSidebar"] .stMarkdown h1 {
        background: linear-gradient(135deg, #6c63ff, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800; font-size: 1.6rem;
    }

    .kpi-card {
        border-radius: 16px; padding: 24px 20px; text-align: center;
        border: 1px solid rgba(255,255,255,0.06);
        backdrop-filter: blur(12px);
        transition: transform 0.25s ease, box-shadow 0.25s ease;
        position: relative; overflow: hidden;
    }
    .kpi-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(108,99,255,0.15);
    }
    .kpi-icon { font-size: 2rem; margin-bottom: 6px; }
    .kpi-value { font-size: 2rem; font-weight: 800; letter-spacing: -1px; margin-bottom: 4px; }
    .kpi-label { font-size: 0.82rem; text-transform: uppercase; letter-spacing: 1.5px; color: #8892a0; }

    .section-header {
        font-size: 1.25rem; font-weight: 700; color: #ffffff;
        margin: 2rem 0 1rem 0; padding-bottom: 8px;
        border-bottom: 2px solid #6c63ff; display: inline-block;
    }

    .student-card {
        background: linear-gradient(135deg, #1a1f2e 0%, #1e2640 100%);
        border: 1px solid #2a3050; border-radius: 16px; padding: 28px; margin: 16px 0;
    }
    .student-card h3 { color: #6c63ff; margin-bottom: 16px; font-weight: 700; }
    .student-field {
        display: flex; justify-content: space-between;
        padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.04);
    }
    .student-field-key { color: #8892a0; text-transform: capitalize; font-size: 0.9rem; }
    .student-field-val { color: #e0e0e0; font-weight: 600; }

    .top-student {
        background: #1a1f2e; border: 1px solid #2a3050; border-radius: 12px;
        padding: 14px 18px; margin-bottom: 8px;
        display: flex; align-items: center; gap: 14px;
    }
    .rank-badge {
        width: 36px; height: 36px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-weight: 800; font-size: 0.9rem; color: #fff; flex-shrink: 0;
    }
    .rank-1 { background: linear-gradient(135deg, #ffd93d, #f39c12); }
    .rank-2 { background: linear-gradient(135deg, #b0b0b0, #888); }
    .rank-3 { background: linear-gradient(135deg, #cd7f32, #a0522d); }

    .custom-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, #2a3050, transparent);
        margin: 2rem 0;
    }

    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }

    .stTabs [data-baseweb="tab-list"] {
        gap: 4px; background: #1a1f2e; border-radius: 12px; padding: 4px;
    }
    .stTabs [data-baseweb="tab"] { border-radius: 10px; color: #8892a0; font-weight: 500; }
    .stTabs [aria-selected="true"] { background: #6c63ff !important; color: white !important; }
</style>
""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════
#  SIDEBAR
# ═════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("# 🎓 Student Analytics")
    st.caption("Upload & explore student performance data")

    st.markdown("---")
    st.markdown("#### 📤 Upload Dataset")

    uploaded_file = st.file_uploader(
        "Upload an Excel (.xlsx) file",
        type=["xlsx"],
        label_visibility="collapsed",
    )

    if uploaded_file is not None:
        with st.spinner("⏳ Processing upload..."):
            try:
                import os
                df_upload = process_student_excel(uploaded_file)
                table_name = os.path.splitext(uploaded_file.name)[0].lower().replace(" ", "_")
                db_upload(df_upload, table_name)
                st.success(f"✅ Uploaded **{table_name}** — {len(df_upload)} rows")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Upload failed: {e}")

    st.markdown("---")
    st.markdown("#### 📂 Datasets")

    tables = db_get_tables()

    if not tables:
        st.info("No datasets found. Upload a file above.")
        st.stop()

    selected_table = st.radio(
        "Choose a dataset",
        tables,
        label_visibility="collapsed",
    )


# ═════════════════════════════════════════════════════
#  LOAD DATA
# ═════════════════════════════════════════════════════
df = db_get_all_data(selected_table)

if df.empty:
    st.warning("No data available for this table.")
    st.stop()

# clean column names
df.columns = (
    df.columns.str.strip()
    .str.lower()
    .str.replace(" ", "_")
    .str.replace("\n", "")
)

# numeric conversion
for col in ["grade_q1", "grade_q2", "grade_q3", "overall_grade"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# pass / fail
if "overall_grade" in df.columns:
    df["result"] = df["overall_grade"].apply(
        lambda x: "Pass" if pd.notna(x) and x >= 60 else "Fail"
    )


# ═════════════════════════════════════════════════════
#  HEADER
# ═════════════════════════════════════════════════════
display_name = selected_table.replace("_", " ").title()
course_name = str(df["course"].iloc[0]) if "course" in df.columns and not df.empty else "—"

st.markdown(f"""
<div style="margin-bottom: 0.5rem;">
    <h1 style="margin:0; font-weight:800; font-size:2rem;
        background: linear-gradient(135deg, #6c63ff, #00d4aa);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        {display_name}
    </h1>
    <p style="color:#8892a0; font-size:1rem; margin-top:4px;">
        Course: <strong style="color:#e0e0e0;">{course_name}</strong>
    </p>
</div>
""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════
#  KPI CARDS
# ═════════════════════════════════════════════════════
if "overall_grade" in df.columns:
    total = len(df)
    avg = round(df["overall_grade"].mean(), 1)
    top = df["overall_grade"].max()
    low = df["overall_grade"].min()
    pass_rate = round((df["result"] == "Pass").mean() * 100, 1) if "result" in df.columns else "—"

    c1, c2, c3, c4, c5 = st.columns(5)

    def kpi_html(icon, value, label, gradient):
        return f"""
        <div class="kpi-card" style="background:{COLORS['card']};">
            <div style="position:absolute;top:0;left:0;right:0;height:3px;
                background:{gradient};border-radius:16px 16px 0 0;"></div>
            <div class="kpi-icon">{icon}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-label">{label}</div>
        </div>"""

    c1.markdown(kpi_html("👥", total, "Students", COLORS["gradient1"]), unsafe_allow_html=True)
    c2.markdown(kpi_html("📊", avg, "Avg Score", COLORS["gradient2"]), unsafe_allow_html=True)
    c3.markdown(kpi_html("🏆", top, "Top Score", COLORS["gradient4"]), unsafe_allow_html=True)
    c4.markdown(kpi_html("📉", low, "Lowest", COLORS["gradient3"]), unsafe_allow_html=True)
    c5.markdown(kpi_html("✅", f"{pass_rate}%", "Pass Rate", COLORS["gradient2"]), unsafe_allow_html=True)

st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)


# ═════════════════════════════════════════════════════
#  TABS
# ═════════════════════════════════════════════════════
tab_overview, tab_departments, tab_students = st.tabs([
    "📈  Overview", "🏫  Departments", "🔍  Students"
])


# ─────────────────────────────────────────────────────
#  TAB 1 — OVERVIEW
# ─────────────────────────────────────────────────────
with tab_overview:

    col1, col2 = st.columns(2)

    with col1:
        if "overall_grade" in df.columns:
            fig = px.histogram(
                df, x="overall_grade", nbins=20,
                color_discrete_sequence=[COLORS["accent"]],
                title="Overall Grade Distribution",
            )
            fig.update_layout(**PLOTLY_LAYOUT)
            fig.update_traces(marker_line_width=0, opacity=0.85)
            st.plotly_chart(fig, width="stretch")

    with col2:
        if "department" in df.columns and "overall_grade" in df.columns:
            dept_avg = df.groupby("department")["overall_grade"].mean().reset_index()
            dept_avg = dept_avg.sort_values("overall_grade", ascending=True)
            fig = px.bar(
                dept_avg, x="overall_grade", y="department",
                orientation="h", color="overall_grade",
                color_continuous_scale=["#6c63ff", "#00d4aa"],
                title="Department Wise Average",
            )
            fig.update_layout(**PLOTLY_LAYOUT, showlegend=False, coloraxis_showscale=False)
            st.plotly_chart(fig, width="stretch")

    col1, col2, col3 = st.columns(3)

    with col1:
        if "result" in df.columns:
            counts = df["result"].value_counts().reset_index()
            counts.columns = ["Result", "Count"]
            fig = px.pie(
                counts, names="Result", values="Count", title="Pass vs Fail",
                color_discrete_sequence=[COLORS["accent2"], COLORS["accent3"]], hole=0.45,
            )
            fig.update_layout(**PLOTLY_LAYOUT)
            fig.update_traces(textposition="inside", textinfo="percent+label", textfont_size=13)
            st.plotly_chart(fig, width="stretch")

    with col2:
        if "result" in df.columns and "department" in df.columns:
            dept_pass = df[df["result"] == "Pass"]["department"].value_counts().reset_index()
            dept_pass.columns = ["Department", "Count"]
            fig = px.pie(
                dept_pass, names="Department", values="Count",
                title="Pass by Department",
                color_discrete_sequence=CHART_COLORS, hole=0.45,
            )
            fig.update_layout(**PLOTLY_LAYOUT)
            fig.update_traces(textposition="inside", textinfo="percent+label", textfont_size=12)
            st.plotly_chart(fig, width="stretch")

    with col3:
        if "result" in df.columns and "department" in df.columns:
            dept_fail = df[df["result"] == "Fail"]["department"].value_counts().reset_index()
            dept_fail.columns = ["Department", "Count"]
            if not dept_fail.empty:
                fig = px.pie(
                    dept_fail, names="Department", values="Count",
                    title="Fail by Department",
                    color_discrete_sequence=CHART_COLORS[::-1], hole=0.45,
                )
            else:
                fig = go.Figure()
                fig.add_annotation(text="No failures 🎉", showarrow=False,
                                   font=dict(size=18, color="#00d4aa"))
                fig.update_layout(title="Fail by Department")
            fig.update_layout(**PLOTLY_LAYOUT)
            st.plotly_chart(fig, width="stretch")

    # Q1, Q2, Q3
    grade_cols = [c for c in ["grade_q1", "grade_q2", "grade_q3"] if c in df.columns]
    if grade_cols:
        st.markdown('<div class="section-header">📝 Exam Wise Distribution</div>',
                    unsafe_allow_html=True)
        cols = st.columns(len(grade_cols))
        labels = {"grade_q1": "Q1 (out of 100)", "grade_q2": "Q2 (out of 100)",
                  "grade_q3": "Q3 (out of 100)"}
        for i, gc in enumerate(grade_cols):
            with cols[i]:
                fig = px.histogram(
                    df, x=gc, nbins=15, title=labels.get(gc, gc),
                    color_discrete_sequence=[CHART_COLORS[i + 3]],
                )
                fig.update_layout(**PLOTLY_LAYOUT)
                fig.update_traces(marker_line_width=0, opacity=0.85)
                st.plotly_chart(fig, width="stretch")

    # Exam comparison
    if grade_cols:
        means = df[grade_cols].mean()
        fig = go.Figure()
        for i, gc in enumerate(grade_cols):
            fig.add_trace(go.Bar(
                name=labels.get(gc, gc), x=[labels.get(gc, gc)], y=[means[gc]],
                marker_color=CHART_COLORS[i + 3],
                text=[f"{means[gc]:.1f}"], textposition="outside",
            ))
        fig.update_layout(
            **PLOTLY_LAYOUT, title="Exam Performance Comparison",
            showlegend=False, barmode="group", yaxis_title="Average Score",
        )
        st.plotly_chart(fig, width="stretch")


# ─────────────────────────────────────────────────────
#  TAB 2 — DEPARTMENTS
# ─────────────────────────────────────────────────────
with tab_departments:
    if "department" not in df.columns:
        st.info("No department column found.")
    else:
        for dept in sorted(df["department"].dropna().unique()):
            dept_df = df[df["department"] == dept]

            st.markdown(f'<div class="section-header">🏫 {dept}</div>',
                        unsafe_allow_html=True)

            col1, col2 = st.columns([2, 1])

            with col1:
                fig = px.histogram(
                    dept_df, x="overall_grade", nbins=15,
                    color_discrete_sequence=[COLORS["accent"]],
                    title=f"{dept} — Grade Distribution",
                )
                fig.update_layout(**PLOTLY_LAYOUT)
                fig.update_traces(marker_line_width=0, opacity=0.85)
                st.plotly_chart(fig, width="stretch")

            with col2:
                st.markdown("**🏅 Top 3 Students**")
                top3 = dept_df.sort_values("overall_grade", ascending=False).head(3)
                for rank, (_, row) in enumerate(top3.iterrows(), 1):
                    name = row.get("student_name", "—")
                    grade = row.get("overall_grade", "—")
                    rank_class = f"rank-{rank}" if rank <= 3 else ""
                    st.markdown(f"""
                    <div class="top-student">
                        <div class="rank-badge {rank_class}">#{rank}</div>
                        <div>
                            <div style="font-weight:600;color:#e0e0e0;">{name}</div>
                            <div style="color:#8892a0;font-size:0.85rem;">Score: {grade}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────
#  TAB 3 — STUDENTS
# ─────────────────────────────────────────────────────
with tab_students:

    st.markdown('<div class="section-header">🔍 Search Student</div>',
                unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col1:
        roll_no = st.text_input(
            "Roll Number",
            placeholder="e.g. 21CS001",
            label_visibility="collapsed",
        )
    with col2:
        search_btn = st.button("🔎  Search", use_container_width=True)

    if search_btn and roll_no:
        student = db_get_student(selected_table, roll_no)
        if student:
            st.markdown('<div class="student-card">', unsafe_allow_html=True)
            st.markdown(f"### 👤 {student.get('student_name', 'Student')}")

            keys = list(student.keys())
            mid = len(keys) // 2
            c1, c2 = st.columns(2)

            with c1:
                for k in keys[:mid]:
                    v = student[k]
                    label = k.replace("_", " ").title()
                    st.markdown(f"""
                    <div class="student-field">
                        <span class="student-field-key">{label}</span>
                        <span class="student-field-val">{v}</span>
                    </div>""", unsafe_allow_html=True)
            with c2:
                for k in keys[mid:]:
                    v = student[k]
                    label = k.replace("_", " ").title()
                    st.markdown(f"""
                    <div class="student-field">
                        <span class="student-field-key">{label}</span>
                        <span class="student-field-val">{v}</span>
                    </div>""", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

            # Radar chart
            grade_data = {}
            for gc in ["grade_q1", "grade_q2", "grade_q3"]:
                if gc in student:
                    grade_data[gc.replace("grade_", "").upper()] = float(student[gc]) if student[gc] else 0

            if grade_data:
                categories = list(grade_data.keys())
                values = list(grade_data.values())
                categories.append(categories[0])
                values.append(values[0])

                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(
                    r=values, theta=categories, fill="toself",
                    fillcolor="rgba(108,99,255,0.2)",
                    line_color=COLORS["accent"], name="Score",
                ))
                fig.update_layout(
                    **PLOTLY_LAYOUT, title="Exam Performance Radar",
                    polar=dict(
                        bgcolor="rgba(0,0,0,0)",
                        radialaxis=dict(visible=True, range=[0, 100], gridcolor="#2a3050"),
                        angularaxis=dict(gridcolor="#2a3050"),
                    ),
                )
                st.plotly_chart(fig, width="stretch")
        else:
            st.error("❌ Student not found. Check the Roll number.")
    elif search_btn:
        st.warning("Please enter a roll number.")

    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

    # All students table
    st.markdown('<div class="section-header">📋 All Students</div>',
                unsafe_allow_html=True)

    display_cols = [c for c in ["student_name", "roll_no_", "register_no_",
                                "department", "year", "overall_grade", "result"]
                    if c in df.columns]

    if display_cols:
        styled_df = df[display_cols].copy()
        styled_df.columns = [c.replace("_", " ").title() for c in display_cols]
        st.dataframe(styled_df, width="stretch", height=500)
    else:
        st.info("No student columns found.")
