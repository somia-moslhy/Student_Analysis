import os
import sys

import plotly.express as px
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import (
    ACCENT, DANGER, DARK,
    chart_layout, filter_context, insight, decision,
    page_header, read, sidebar, story, theme_colors,
)

st.set_page_config(page_title="Who Needs Us Now", layout="wide")
sidebar()
ss, kpi, sel_courses, sel_groups = filter_context()

page_header(
    "Chapter 6 · Who Needs Us Now",
    "*The story ends with action — which groups cannot continue as-is, "
    "and which students leadership should contact first.*",
)

t = theme_colors()

# ── Scene 1: Non-viable group ───────────────────────────────────────────────
story(
    "Group 10 cannot function as a cohort",
    "Cybersecurity Essentials (G10) lists **31 students** but only **1** actually enrolled. "
    "No meaningful group learning can happen at that scale.",
)

if not ss.empty and "group_name" in ss.columns:
    group_counts = ss[ss["group_name"] != 0]["group_name"].value_counts().reset_index()
    group_counts.columns = ["group_name", "count"]
    group_counts = group_counts.sort_values("count", ascending=True)
    
    colors = [DANGER if "10" in str(g) else DARK for g in group_counts["group_name"]]
    
    fig = px.bar(
        group_counts, x="count", y="group_name", orientation="h",
        text="count",
        title="Enrolled students per group — G10 is effectively empty",
        labels={"group_name": "", "count": "Enrolled Students"},
    )
    fig.update_traces(marker_color=colors, textposition="outside")
    fig.update_layout(**chart_layout(title="Enrolled students per group — G10 is effectively empty"))
    st.plotly_chart(fig, use_container_width=True)

st.error(
    "**Recommendation:** Dissolve G10. Transfer the single student to **Group 09** "
    "(Machine Learning Basics — closest concept profile). "
    "Update `group_id` in students.csv and notify both instructors."
)

st.divider()

# ── Scene 2: Top 10 at-risk ─────────────────────────────────────────────────
story(
    "These ten students need a call this week",
    "Risk score blends **35% attendance + 35% grade + 15% engagement + 15% failed concepts**. "
    "Seven of the top ten sit in Group 07 — this is a group-level crisis, not isolated cases.",
)

top10 = read("at_risk_top10")
if sel_groups and "group_name" in top10.columns:
    top10 = top10[top10["group_name"].isin(sel_groups)]
if sel_courses and "course_name" in top10.columns:
    top10 = top10[top10["course_name"].isin(sel_courses)]

top10 = top10.sort_values("risk_score", ascending=True)

fig = px.bar(
    top10, x="risk_score", y="full_name", orientation="h",
    color="group_name", text="risk_score",
    hover_data=["group_name", "attendance_rate", "avg_grade", "failed_concept_count"],
    title="Priority contact list — highest composite risk",
    labels={"full_name": "", "risk_score": "Risk Score", "group_name": "Group"},
)
fig.update_traces(texttemplate="%{text:.3f}", textposition="outside", textfont_color=t["text"])
fig.update_xaxes(range=[0, 0.75])
fig.update_layout(**chart_layout(title="Priority contact list — highest composite risk"))
st.plotly_chart(fig, use_container_width=True)

# Mini-cards instead of table
if not top10.empty:
    top10_sorted = top10.sort_values("risk_score", ascending=False).head(5)
    cols = st.columns(5)
    for col, (_, row) in zip(cols, top10_sorted.iterrows()):
        col.metric(
            row["full_name"].split()[0] if isinstance(row["full_name"], str) else "Student",
            f"{row['risk_score']:.3f}",
            delta=f"{row['group_name']}",
            delta_color="off",
        )
    st.caption(
        "Hover the chart for full details (attendance, grade, failed concepts). "
        "Top 5 shown above — chart holds all 10."
    )

g07_count = int((top10["group_name"].str.contains("07", na=False)).sum()) if not top10.empty else 0
insight(f"**{g07_count} of the top 10** at-risk students are in Group 07.")
decision(
    "1) Contact all 10 students this week. "
    "2) Schedule a Group 07 intervention session. "
    "3) Alert the Group 07 instructor today."
)

st.divider()

# ── Scene 3: Filtered at-risk landscape ─────────────────────────────────────
if not ss.empty and "segment" in ss.columns:
    story(
        "The full at-risk picture in your current scope",
        f"With your filters applied, **{kpi['at_risk_count']} students** fall in the At-Risk segment "
        f"out of **{kpi['total_students']}** in view.",
    )

    at_risk = ss[ss["segment"] == "At-Risk"]
    if not at_risk.empty:
        fig = px.scatter(
            at_risk, x="attendance_rate", y="avg_grade",
            size="failed_concept_count", color="group_name",
            hover_data=["full_name", "login_count", "risk_score"],
            title="At-risk students in scope — where they sit",
            labels={
                "attendance_rate": "Attendance (%)",
                "avg_grade": "Avg Grade (%)",
                "failed_concept_count": "Failed Concepts",
            },
            opacity=0.85,
        )
        fig.update_layout(**chart_layout(title="At-risk students in scope — where they sit", legend_y=-0.15))
        st.plotly_chart(fig, use_container_width=True)

        decision(
            f"Prioritise the {kpi['at_risk_count']} at-risk students visible under current filters — "
            "start with lowest attendance × lowest grade quadrant."
        )
