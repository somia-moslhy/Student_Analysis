import os
import sys

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import (
    ACCENT, DANGER, DARK, GREEN,
    chart_layout, filter_context, insight, decision,
    page_header, read, sidebar, story, theme_colors,
)

st.set_page_config(page_title="Staying Connected", layout="wide")
sidebar()
ss, kpi, sel_courses, sel_groups = filter_context()

page_header(
    "Chapter 3 · Staying Connected",
    "*Showing up is not enough — this chapter asks whether platform activity actually predicts success, "
    "and what happens when students rush their submissions.*",
)

t = theme_colors()
filtered_ss = ss

# ── Scene 1: Attendance alone is a weak signal ────────────────────────────
story(
    "Attendance alone won't save a student",
    "The scatter and heatmap below tell the same story: **high attendance does not guarantee strong grades**. "
    "67 students attend regularly yet still score below expectations.",
)

if not filtered_ss.empty:
    corr_val = filtered_ss[["attendance_rate", "avg_grade"]].corr().iloc[0, 1]

    c1, c2 = st.columns(2)
    with c1:
        fig = px.scatter(
            filtered_ss, x="attendance_rate", y="avg_grade",
            color="course_name", trendline="ols", trendline_scope="overall",
            title=f"Attendance vs grade — a weak link (r = {corr_val:.3f})",
            labels={"attendance_rate": "Attendance (%)", "avg_grade": "Avg Grade (%)", "course_name": "Course"},
            opacity=0.7,
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig.update_traces(line=dict(color=DARK, width=4), selector=dict(mode="lines"))
        fig.update_layout(**chart_layout(title=f"Attendance vs grade — a weak link (r = {corr_val:.3f})"))
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        tmp_box = filtered_ss.copy()
        tmp_box["att_category"] = pd.cut(
            tmp_box["attendance_rate"],
            bins=[-1, 25, 50, 75, 105],
            labels=["Very Low (0-25%)", "Low (26-50%)", "Medium (51-75%)", "High (76-100%)"],
        )
        fig = px.box(
            tmp_box, x="att_category", y="avg_grade", color="att_category",
            title="Grade spread by attendance level — boxes overlap heavily",
            labels={"att_category": "Attendance Level", "avg_grade": "Avg Grade (%)"},
            category_orders={"att_category": [
                "Very Low (0-25%)", "Low (26-50%)", "Medium (51-75%)", "High (76-100%)",
            ]},
        )
        fig.update_layout(**chart_layout(title="Grade spread by attendance level — boxes overlap heavily"), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    tmp = filtered_ss.copy()
    tmp["att_bin"] = pd.cut(
        tmp["attendance_rate"], bins=[-1, 60, 80, 105],
        labels=["Low (<60%)", "Medium (60-80%)", "High (>80%)"],
    )
    tmp["grade_bin"] = pd.cut(
        tmp["avg_grade"], bins=[-1, 55, 70, 105],
        labels=["Weak (<55%)", "Pass (55-70%)", "Strong (>70%)"],
    )
    hm = tmp.groupby(["grade_bin", "att_bin"], observed=True).size().reset_index(name="count")
    hm_pivot = hm.pivot(index="grade_bin", columns="att_bin", values="count").fillna(0)
    hm_pivot = hm_pivot.reindex(
        index=["Weak (<55%)", "Pass (55-70%)", "Strong (>70%)"],
        columns=["Low (<60%)", "Medium (60-80%)", "High (>80%)"],
    )
    fig = px.imshow(
        hm_pivot, text_auto=True,
        color_continuous_scale=px.colors.sequential.Blues,
        zmin=0,
        title="Who attends but still struggles",
        labels=dict(x="Attendance Level", y="Grade Level", color="Students"),
    )
    fig.update_layout(**chart_layout(title="Who attends but still struggles"))
    st.plotly_chart(fig, use_container_width=True)

    insight(
        "Attendance explains only ~5% of grade variance. "
        "High-attendance students are scattered across all grade bands — presence ≠ performance."
    )
    decision(
        "Shift retention focus from attendance nudges to learning support for students "
        "who show up but underperform."
    )

st.divider()

# ── Scene 2: Engagement drives outcomes ─────────────────────────────────
story(
    "Video time and logins tell a clearer story",
    "Unlike attendance, **platform engagement correlates moderately with grades** — "
    "students who watch more and log in more tend to score higher.",
)

if not filtered_ss.empty:
    r_video = filtered_ss[["total_video_mins", "avg_grade"]].corr().iloc[0, 1]
    r_login = filtered_ss[["login_count", "avg_grade"]].corr().iloc[0, 1]

    c1, c2 = st.columns(2)
    with c1:
        fig = px.scatter(
            filtered_ss, x="total_video_mins", y="avg_grade",
            color="attendance_rate",
            color_continuous_scale=[[0, DANGER], [0.5, ACCENT], [1, GREEN]],
            trendline="ols",
            title=f"Video watch time vs grade (r = {r_video:.3f})",
            labels={"total_video_mins": "Video Watch (mins)", "avg_grade": "Avg Grade (%)", "attendance_rate": "Attendance %"},
            opacity=0.7,
        )
        fig.update_traces(line=dict(color=DARK, width=3), selector=dict(mode="lines"))
        fig.update_layout(**chart_layout(title=f"Video watch time vs grade (r = {r_video:.3f})"))
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        fig = px.scatter(
            filtered_ss, x="login_count", y="avg_grade",
            color="total_video_mins",
            color_continuous_scale=[[0, ACCENT], [1, DARK]],
            trendline="ols",
            title=f"Login frequency vs grade (r = {r_login:.3f})",
            labels={"login_count": "Login Count", "avg_grade": "Avg Grade (%)", "total_video_mins": "Video Mins"},
            opacity=0.7,
        )
        fig.update_traces(line=dict(color=DANGER, width=3), selector=dict(mode="lines"))
        fig.update_layout(**chart_layout(title=f"Login frequency vs grade (r = {r_login:.3f})"))
        st.plotly_chart(fig, use_container_width=True)

    insight("Video time (r ≈ 0.41) and logins (r ≈ 0.38) both correlate moderately with grade.")
    decision("Track weekly video completion as an early-warning engagement metric.")

st.divider()

# ── Scene 3: The penalty of rushing ───────────────────────────────────────
story(
    "Late submitters pay a real price",
    "Students who miss the deadline or submit at the last minute lose **4–7 percentage points** on average. "
    "Early submitters consistently score higher.",
)

subs = read("submission_analysis")
if sel_courses and "course_name" in subs.columns:
    subs = subs[subs["course_name"].isin(sel_courses)]
if sel_groups and "group_name" in subs.columns:
    subs = subs[subs["group_name"].isin(sel_groups)]
subs = subs.dropna(subset=["grade_score_pct"]).copy()
subs["is_late"] = subs["is_late"].astype(bool)

late_avg = round(subs[subs["is_late"]]["grade_score_pct"].mean(), 1) if len(subs) else 0
early_avg = round(subs[~subs["is_late"]]["grade_score_pct"].mean(), 1) if len(subs) else 0
gap = round(early_avg - late_avg, 1)

m1, m2, m3 = st.columns(3)
m1.metric("On-time average", f"{early_avg}%")
m2.metric("Late average", f"{late_avg}%")
m3.metric("Gap", f"{gap} pp")

bins = [-np.inf, 0, 12, 48, np.inf]
labels = ["Late (< 0h)", "Last Minute (0-12h)", "On Time (12-48h)", "Early (> 48h)"]
subs["timing_category"] = pd.cut(subs["hours_before_deadline"], bins=bins, labels=labels)

c1, c2 = st.columns(2)
with c1:
    fig = px.scatter(
        subs, x="hours_before_deadline", y="grade_score_pct",
        color="is_late",
        color_discrete_map={True: DANGER, False: GREEN},
        trendline="ols",
        title="Every hour before the deadline counts",
        labels={"hours_before_deadline": "Hours Before Deadline", "grade_score_pct": "Score (%)", "is_late": "Late"},
        opacity=0.65,
    )
    fig.add_vline(x=0, line_dash="dash", line_color=t["vline"],
                  annotation_text="Deadline", annotation_position="top right",
                  annotation_font_color=t["text"])
    fig.update_layout(**chart_layout(title="Every hour before the deadline counts"))
    st.plotly_chart(fig, use_container_width=True)

with c2:
    fig = px.box(
        subs, x="timing_category", y="grade_score_pct", color="timing_category",
        title="The penalty of rushing — score by submission behaviour",
        labels={"timing_category": "Submission Behaviour", "grade_score_pct": "Score (%)"},
        category_orders={"timing_category": labels},
        color_discrete_sequence=[DANGER, "#FFA15A", GREEN, ACCENT],
    )
    fig.update_traces(boxmean="sd")
    fig.update_layout(**chart_layout(title="The penalty of rushing — score by submission behaviour"), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

insight(f"Late submissions average **{late_avg}%** vs **{early_avg}%** on-time — a **{gap} pp** gap.")
decision("Send automated reminders 48h and 24h before each assignment deadline.")
