import os
import sys

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import (
    ACCENT, DANGER, DARK, GREEN, TYPE_COLORS,
    chart_layout, filter_context, insight, decision,
    load_grades_raw, page_header, read, sidebar, story, theme_colors,
)

st.set_page_config(page_title="How They Perform", layout="wide")
sidebar()
ss, kpi, sel_courses, sel_groups = filter_context()

page_header(
    "Chapter 2 · How They Perform",
    "*Grades tell us where the curriculum lands — which assessment types hurt, which courses lag, "
    "and whether any group is climbing or stuck.*",
)

t = theme_colors()

# ── Scene 1 ───────────────────────────────────────────────────────────────
story(
    "Assignments are the wild card",
    "Quizzes, practicals, and exams cluster tightly around **72–73%**. "
    "Assignments sit lower with the widest spread — students struggle most with take-home work.",
)

grades_clean = load_grades_raw()
if sel_courses and "course_name" in grades_clean.columns:
    grades_clean = grades_clean[grades_clean["course_name"].isin(sel_courses)]
if sel_groups and "group_name" in grades_clean.columns:
    grades_clean = grades_clean[grades_clean["group_name"].isin(sel_groups)]

type_summary = (
    grades_clean.groupby("type")["score_pct"]
    .agg(mean="mean", count="count").round(1).reset_index()
)

fig = px.box(
    grades_clean, x="type", y="score_pct", color="type",
    color_discrete_map=TYPE_COLORS,
    title="Score spread by assessment type — assignments carry the most risk",
    labels={"type": "Assessment Type", "score_pct": "Score (%)"},
    category_orders={"type": ["quiz", "assignment", "practical", "exam"]},
    points="outliers",
)
for _, row in type_summary.iterrows():
    fig.add_trace(go.Scatter(
        x=[row["type"]], y=[row["mean"]],
        mode="markers+text",
        marker=dict(symbol="line-ew", size=40, color=DANGER, line=dict(width=4, color=DANGER)),
        text=[f"avg {row['mean']:.1f}%"],
        textposition="top center",
        textfont=dict(size=12, color=t["text"]),
        showlegend=False,
    ))
    scores_max = grades_clean.groupby("type")["score_pct"].max()[row["type"]]
    fig.data[-1].y = [scores_max + 2]
fig.update_layout(**chart_layout(title="Score spread by assessment type — assignments carry the most risk"), showlegend=False)
st.plotly_chart(fig, use_container_width=True)

insight("Assignments average **65.3%** with the highest spread. Other types are stable.")
decision("Add mid-assignment check-ins and automated deadline reminders for take-home work.")

st.divider()

# ── Scene 2 ───────────────────────────────────────────────────────────────
story(
    "Digital Marketing is the course that needs attention",
    "Most courses sit in a tight band. **Digital Marketing** breaks away with a lower average score.",
)

course_grades = (
    grades_clean.groupby("course_name")["score_pct"]
    .agg(avg="mean").reset_index().round(1)
    .sort_values("avg", ascending=True)
)

fig = go.Figure()
fig.add_trace(go.Bar(
    y=course_grades["course_name"], x=course_grades["avg"], orientation="h",
    name="Avg Grade (%)", marker_color=ACCENT,
    text=[f"{v}%" for v in course_grades["avg"]],
    textposition="outside", textfont=dict(color=t["text"], size=11),
))
fig.update_xaxes(range=[0, 110], title="Score (%)")
fig.update_layout(
    **chart_layout(title="Course performance — average scores", legend_y=-0.18),
)
st.plotly_chart(fig, use_container_width=True)

insight(
    "Digital Marketing at **59.1%** is ~13 pp below the next course."
)
decision("Launch an immediate curriculum review for Digital Marketing.")

st.divider()

# ── Scene 3 ───────────────────────────────────────────────────────────────
story(
    "Most groups are flat — none are climbing",
    "Month-by-month grade trends reveal stability, not momentum. Group 07 stays lowest throughout.",
)

trends = read("group_grade_trends").sort_values("month")
if sel_groups:
    trends = trends[trends["group_name"].isin(sel_groups)]

fig = px.line(
    trends, x="month", y="score_pct", color="group_name", markers=True,
    title="Grade trajectories across the term — flat lines, no breakout",
    labels={"month": "Month", "score_pct": "Average Score (%)", "group_name": "Group"},
)
fig.update_layout(**chart_layout(title="Grade trajectories across the term — flat lines, no breakout", legend_y=-0.15))
st.plotly_chart(fig, use_container_width=True)

insight("No group trends strongly upward. Group 07 is consistently ~60%. The curriculum may not build progressively.")
decision("Introduce scaffolded assessments that reward improvement over time.")
