import os
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import (
    ACCENT, DANGER, DARK, GREEN, FLAG_COLORS, SEGMENT_COLORS,
    chart_layout, filter_context, insight, decision,
    page_header, read, sidebar, story, theme_colors,
)

st.set_page_config(page_title="Who They Are", layout="wide")
sidebar()
ss, kpi, sel_courses, sel_groups = filter_context()

page_header(
    "Chapter 5 · Who They Are",
    "*Students are not one homogeneous group — age, behaviour, and even roster data "
    "tell us who thrives, who struggles, and where our records lie.*",
)

t = theme_colors()

# ── Scene 1: Age bands ────────────────────────────────────────────────────
story(
    "Age shapes outcomes — quietly but visibly",
    "The **28–35** band leads on grades, attendance, and video engagement. "
    "Younger students (18–22) struggle most with showing up.",
)

if not ss.empty:
    age_g = ss.groupby("age_group", observed=True).agg(
        avg_grade=("avg_grade", "mean"),
        attendance_rate=("attendance_rate", "mean"),
        count=("student_id", "count"),
    ).reset_index().round(1)

    video_max = ss["total_video_mins"].max() or 1
    age_video = ss.groupby("age_group", observed=True)["total_video_mins"].mean().reset_index()
    age_video["video_pct"] = (age_video["total_video_mins"] / video_max * 100).round(1)
    age_g = age_g.merge(age_video[["age_group", "video_pct"]], on="age_group")

    fig = px.bar(
        age_g.melt(id_vars="age_group", value_vars=["avg_grade", "attendance_rate", "video_pct"]),
        x="age_group", y="value", color="variable", barmode="group", text="value",
        color_discrete_map={"avg_grade": DARK, "attendance_rate": ACCENT, "video_pct": GREEN},
        title="How age bands compare across three signals",
        labels={"age_group": "Age Group", "value": "Score / %", "variable": "Metric"},
    )
    fig.update_traces(texttemplate="%{text:.0f}", textposition="outside", textfont_color=t["text"])
    newnames = {
        "avg_grade": "Avg Grade (%)",
        "attendance_rate": "Attendance (%)",
        "video_pct": "Video Engagement (norm)",
    }
    fig.for_each_trace(lambda tr: tr.update(name=newnames.get(tr.name, tr.name)))
    fig.update_layout(**chart_layout(title="How age bands compare across three signals"))
    st.plotly_chart(fig, use_container_width=True)

    insight("28–35 performs best across all three metrics. 18–22 is weakest on attendance.")
    decision("Younger students need attendance nudges; older students need flexible scheduling.")

st.divider()

# ── Scene 2: Segmentation ─────────────────────────────────────────────────
story(
    "Four segments — one needs us now",
    "Clustering reveals **High Achievers**, **Average Engaged**, **At-Risk**, and a single **Outlier**. "
    "Bubble size reflects failed concepts — At-Risk students carry the heaviest load.",
)

if not ss.empty and "segment" in ss.columns:
    segment_map = {
        "High Achievers":    GREEN,
        "Average Engaged":   ACCENT,
        "Silent Strugglers": "#ff9f6b",
        "At-Risk":           DANGER,
    }

    fig = px.scatter(
        ss, x="attendance_rate", y="avg_grade",
        color="segment", size="failed_concept_count", size_max=20,
        hover_data=["full_name", "group_name", "login_count", "total_video_mins"],
        color_discrete_map=segment_map,
        title="Student landscape — four clusters, one danger zone",
        labels={
            "attendance_rate": "Attendance (%)",
            "avg_grade": "Avg Grade (%)",
            "segment": "Segment",
            "failed_concept_count": "Failed Concepts",
        },
        opacity=0.8,
    )
    fig.update_layout(**chart_layout(title="Student landscape — four clusters, one danger zone"))
    st.plotly_chart(fig, use_container_width=True)

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("High Achievers",    "192", "avg 76.3%")
    c2.metric("Average Engaged",   "172", "avg 71.3%")
    c3.metric("Silent Strugglers", "69", "avg 64.1%")
    c4.metric("At-Risk",           "67", "avg 58.4%")
    
    st.info("""
**4 segments — Real numbers:**
- **High Achievers** (192 students): 84.4% attendance, 76.3% grade, 0.6 failed concepts
- **Average Engaged** (172 students): 73.3% attendance, 71.3% grade, 0.7 failed concepts
- **Silent Strugglers** (69 students): 80.3% attendance, 64.1% grade, 3.3 failed concepts
  — They attend regularly but struggle to understand. They need learning support, not attendance reminders
- **At-Risk** (67 students): 60.5% attendance, 58.4% grade, 3.3 failed concepts
  — They don't attend and struggle — highest priority

**Action:** Start with the 67 At-Risk students immediately. Then apply learning intervention for the 69 Silent Strugglers.
""")

st.divider()

# ── Scene 3: Data quality ───────────────────────────────────────────────────
story(
    "Our roster data has phantom students",
    "Comparing stated group sizes against real enrolment reveals **over-reporting** "
    "that distorts workload planning — G10 is the extreme case.",
)

q12 = read("group_size_audit").sort_values("diff", ascending=True)

fig = px.bar(
    q12, x="diff", y="group_name", orientation="h",
    text="diff", color="flag",
    color_discrete_map=FLAG_COLORS,
    title="Roster truth check — real count minus stated count",
    labels={"group_name": "", "diff": "Difference (Real − Stated)", "flag": "Status"},
)
fig.update_traces(texttemplate="%{text:+d}", textposition="outside", textfont_color=t["text"])
fig.add_vline(x=0, line_color=t["vline"], line_width=1.5)
fig.update_xaxes(range=[-35, 10])
fig.update_layout(**chart_layout(title="Roster truth check — real count minus stated count"))
st.plotly_chart(fig, use_container_width=True)

worst = q12.loc[q12["diff"].idxmin()] if not q12.empty else None
if worst is not None:
    insight(
        f"**{worst['group_name']}** stated {int(worst['stated_num_students'])} but has "
        f"only **{int(worst['real_count'])}** real students ({int(worst['diff']):+d})."
    )
decision("Run monthly roster reconciliation using students.csv as the single source of truth.")
