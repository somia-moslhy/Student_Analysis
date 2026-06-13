import os
import sys

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import (
    ACCENT, DANGER, DARK,
    chart_layout, filter_context, insight, decision,
    page_header, read, sidebar, story, theme_colors,
)

st.set_page_config(page_title="Where Learning Breaks", layout="wide")
sidebar()
ss, kpi, sel_courses, sel_groups = filter_context()

page_header(
    "Chapter 4 · Where Learning Breaks",
    "*Beyond averages, concept-level data shows exactly where the curriculum fails — "
    "and whether students are improving or stuck.*",
)

t = theme_colors()

# ── Scene 1 ───────────────────────────────────────────────────────────────
story(
    "Recursion is the concept that breaks the platform",
    "Failure rates across concepts reveal one dominant outlier. **Recursion** fails two-thirds of students — "
    "three times worse than anything else on the platform.",
)

cf = read("concept_failures").sort_values("fail_rate", ascending=True)
if sel_courses and "course_name" in cf.columns:
    cf = cf[cf["course_name"].isin(sel_courses)]

fig = px.bar(
    cf, x="fail_rate", y="concept_name", orientation="h",
    color="course_name", text="fail_rate",
    title="Concept failure landscape — one concept dominates the risk",
    labels={"concept_name": "", "fail_rate": "Failure Rate (%)", "course_name": "Course"},
)
fig.update_traces(texttemplate="%{text}%", textposition="outside", textfont_color=t["text"])
fig.update_xaxes(range=[0, 80])
fig.update_layout(**chart_layout(title="Concept failure landscape — one concept dominates the risk"))
st.plotly_chart(fig, use_container_width=True)

st.error(
    "Recursion (Python Programming) fails **66.7%** of students — "
    "the single biggest curriculum weak spot."
)
decision(
    "Redesign the Recursion module: more worked examples, dedicated practice sessions, "
    "and a checkpoint quiz before students move on."
)

st.divider()

# ── Scene 2 ───────────────────────────────────────────────────────────────
story(
    "Recursion mastery is flat — students are not catching up",
    "Month after month, average mastery and pass rate stay below the 50% threshold. "
    "This is not a one-time difficulty spike; the teaching approach is not working.",
)

rt = read("recursion_trend").sort_values("month")

fig = go.Figure()
fig.add_trace(go.Bar(
    x=rt["month"], y=rt["pass_rate"],
    name="Pass Rate (%)", marker_color=ACCENT, opacity=0.5,
))
fig.add_trace(go.Scatter(
    x=rt["month"], y=rt["avg_mastery"],
    mode="lines+markers+text",
    name="Avg Mastery Score",
    line=dict(color=DANGER, width=3),
    marker=dict(size=9, color=DANGER),
    text=rt["avg_mastery"].astype(str),
    textposition="top center",
    textfont=dict(color=t["text"], size=10),
))
fig.add_hline(
    y=50, line_dash="dash", line_color=t["vline"],
    annotation_text="Pass threshold (50%)",
    annotation_position="top right",
    annotation_font_color=t["text"],
)
fig.update_layout(
    **chart_layout(title="Recursion over time — flat lines below the pass bar", legend_y=-0.2),
    xaxis_title="Month", yaxis_title="%",
)
st.plotly_chart(fig, use_container_width=True)

insight(
    "Both average mastery and pass rate remain flat and below threshold throughout the term. "
    "Students are not improving."
)
decision("Restructure and retest the Recursion module before end of term.")
