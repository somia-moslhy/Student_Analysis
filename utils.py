import json
import os

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from pymongo import MongoClient

# Brand palette (works on light & dark backgrounds)
DARK   = "#353b98"
ACCENT = "#8a91f2"
DANGER = "#ff6b6b"
GREEN  = "#43d9a0"
WHITE  = "#ffffff"

SEGMENT_COLORS = {
    "High Achievers": GREEN,
    "Average Engaged": ACCENT,
    "At-Risk": DANGER,
    "Outlier": DARK,
}

TYPE_COLORS = {
    "quiz": ACCENT,
    "assignment": DANGER,
    "practical": GREEN,
    "exam": DARK,
}

FLAG_COLORS = {
    "Accurate": GREEN,
    "Under-reported": ACCENT,
    "Over-reported": DANGER,
}


def theme_colors():
    return {
        "text": None,
        "muted": None,
        "bg": "rgba(0,0,0,0)",
        "paper": "rgba(0,0,0,0)",
        "grid": "rgba(128,128,128,0.2)",
        "annotation_bg": "rgba(128,128,128,0.1)",
        "heatmap_text": None,
        "vline": ACCENT,
    }


def chart_layout(title="", height=450, legend_y=-0.18):
    t = theme_colors()
    layout = dict(
        title=title,
        plot_bgcolor=t["bg"],
        paper_bgcolor=t["paper"],
        margin=dict(t=60, b=55, l=50, r=30),
        height=height,
    )
    if legend_y is not None:
        layout["legend"] = dict(orientation="h", y=legend_y)
    return layout


def style_fig(fig, title="", height=450, legend_y=-0.18):
    fig.update_layout(**chart_layout(title=title, height=height, legend_y=legend_y))
    return fig


def story(title, body):
    st.markdown(f"### {title}")
    st.markdown(body)


def insight(text):
    st.markdown(f"**What we learned:** {text}")


def decision(text):
    st.markdown(f"**Decision:** {text}")


@st.cache_resource
def get_db():
    client = MongoClient(st.secrets["MONGO_URI"])
    return client["kayfa_analytics"]


def read(collection, query=None, projection=None):
    db = get_db()
    if projection is None:
        projection = {"_id": 0}
    docs = list(db[collection].find(query or {}, projection))
    return pd.DataFrame(docs) if docs else pd.DataFrame()


def _clean_category_values(series: pd.Series) -> pd.Series:
    if series.empty:
        return pd.Series(dtype="object")
    cleaned = series.dropna()
    cleaned = cleaned[~cleaned.isin([0, "0", False])]
    cleaned = cleaned.astype(str).str.strip()
    cleaned = cleaned[cleaned != ""]
    return cleaned


def _sorted_unique_labels(series: pd.Series) -> list:
    return sorted(_clean_category_values(series).unique())


@st.cache_data
def load_grades_raw():
    df = read("grades_full")
    if not df.empty and "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


def apply_filters(df, courses, groups):
    if df.empty:
        return df
    out = df.copy()
    if courses and "course_name" in out.columns:
        out = out[out["course_name"].isin(courses)]
    if groups and "group_name" in out.columns:
        out = out[out["group_name"].isin(groups)]
    return out


def compute_kpis(ss, total_events=None):
    if ss.empty:
        return {k: 0 for k in [
            "total_students", "total_groups", "total_courses",
            "platform_attendance", "platform_avg_grade",
            "total_events", "at_risk_count",
        ]}
    return {
        "total_students": int(len(ss)),
        "total_groups": int(_clean_category_values(ss["group_name"]).nunique()) if "group_name" in ss.columns else 0,
        "total_courses": int(_clean_category_values(ss["course_name"]).nunique()) if "course_name" in ss.columns else 0,
        "platform_attendance": round(float(ss["attendance_rate"].mean()), 1),
        "platform_avg_grade": round(float(ss["avg_grade"].mean()), 1),
        "total_events": int(total_events if total_events is not None else ss["login_count"].sum()),
        "at_risk_count": int((ss["segment"] == "At-Risk").sum()) if "segment" in ss.columns else 0,
    }


def filter_context():
    ss = read("student_summary")
    
    # KPIs from Atlas
    kpis_cache = list(st.session_state.get("kpis_cache") or [])
    if not kpis_cache:
        db = get_db()
        kpi = db["kpis"].find_one({}, {'_id': 0}) or {}
    else:
        kpi = kpis_cache[0] if kpis_cache else {}
        
    # Fallback to direct fetch if missing
    if not kpi:
        db = get_db()
        kpi = db["kpis"].find_one({}, {'_id': 0}) or {}

    return ss, kpi, [], []


def sidebar():
    st.sidebar.image("kayfa_logo.png", use_container_width=True)
    st.sidebar.markdown("---")
    st.sidebar.caption("Kayfa · AI & Data Analytics · Student Story Dashboard\n\n**Week 2 Task 2**")


def page_header(title, subtitle):
    h1, h2 = st.columns([5, 1])
    with h1:
        st.markdown("##### KAYFA — AI & DATA ANALYTICS INTERNSHIP PROGRAM")
        st.title(title)
        st.markdown(subtitle)
    with h2:
        st.image("kayfa_logo.png", use_container_width=True)
    st.divider()


def kpi_row(kpi=None):
    # KPIs from Atlas
    kpis = list(st.session_state.get("kpis_cache") or [])
    if not kpis:
        from utils import get_db
        db = get_db()
        kpi = db["kpis"].find_one({}, {'_id': 0}) or {}
    else:
        kpi = {}

    from utils import get_db
    db  = get_db()
    kpi = db["kpis"].find_one({}, {'_id': 0}) or {}

    k1,k2,k3,k4,k5,k6,k7 = st.columns(7)
    k1.metric("Students",            f"{kpi.get('total_students',0):,}")
    k2.metric("Groups",              f"{kpi.get('total_groups',0)}")
    k3.metric("Courses",             f"{kpi.get('total_courses',0)}")
    k4.metric("Platform Attendance", f"{kpi.get('platform_attendance',0)}%")
    k5.metric("Platform Avg Grade",  f"{kpi.get('platform_avg_grade',0)}%")
    k6.metric("Total Events",        f"{kpi.get('total_events',0):,}")
    k7.metric("At-Risk Students",    f"{kpi.get('at_risk_count',0)}")

    st.divider()
