import os
import sys
import pandas as pd

import plotly.express as px
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import (
    ACCENT, DANGER, DARK,
    chart_layout, filter_context, insight, decision, load_grades_raw,
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

c1, c2 = st.columns(2)
with c1:
    if not ss.empty and "group_name" in ss.columns:
        group_counts = ss[ss["group_name"] != 0]["group_name"].value_counts().reset_index()
        group_counts.columns = ["group_name", "count"]
        group_counts = group_counts.sort_values("count", ascending=True)

        colors = [DANGER if "10" in str(g) else DARK for g in group_counts["group_name"]]

        fig = px.bar(
            group_counts, x="count", y="group_name", orientation="h",
            text="count",
            title="Enrolled students per group — G10 is empty",
            labels={"group_name": "", "count": "Enrolled Students"},
        )
        fig.update_traces(marker_color=colors, textposition="outside")
        fig.update_layout(**chart_layout(title="Enrolled students per group — G10 is empty"))
        st.plotly_chart(fig, use_container_width=True)

with c2:
    if not ss.empty and "group_name" in ss.columns:
        # 1. Filter out phantom groups (0, '0', NaN) from the student summary.
        ss_filtered = ss[~ss["group_name"].isin([0, "0", pd.NA, None, ""])].copy()

        g10_mask = ss_filtered["group_name"].astype(str).str.contains("10")
        student_g10 = ss_filtered[g10_mask]

        if not student_g10.empty and 'failed_concept_count' in student_g10.columns and 'course_name' in student_g10.columns:
            # 2. Extract the course_name and failed concept count of Group 10.
            g10_course = student_g10["course_name"].iloc[0]
            g10_failed_concepts = student_g10["failed_concept_count"].iloc[0]

            # Get other groups and calculate their average failed concepts.
            other_groups = ss_filtered[~g10_mask]
            group_avg_failed = other_groups.groupby(["group_name", "course_name"])["failed_concept_count"].mean().reset_index()
            group_avg_failed.columns = ["group_name", "course_name", "avg_failed_concepts"]

            # 4. Calculate the profile distance (difference in failed concepts).
            group_avg_failed["diff"] = (group_avg_failed["avg_failed_concepts"] - g10_failed_concepts).abs()

            # 3. Identify groups in the same course and create a display name.
            group_avg_failed["is_same_course"] = group_avg_failed["course_name"] == g10_course
            group_avg_failed["display_name"] = group_avg_failed.apply(
                lambda row: f"{row['group_name']} (Same Course)" if row["is_same_course"] else row["group_name"],
                axis=1
            )

            # 5. Sort to prioritize same-course groups and shortest distance at the bottom.
            group_avg_failed = group_avg_failed.sort_values(by=["is_same_course", "diff"], ascending=[True, False])

            # 6. Set colors to highlight Group 09.
            colors = [ACCENT if "09" in str(g) else DARK for g in group_avg_failed["group_name"]]

            # 7. Create the plot with the new title and labels.
            fig_dist = px.bar(
                group_avg_failed, x='diff', y='display_name', orientation='h', text='diff',
                title="Evidence: G09 is the closest match in the SAME course",
                labels={'display_name': '', 'diff': 'Difference in Avg Failed Concepts'}
            )
            fig_dist.update_traces(marker_color=colors, texttemplate='%{text:.1f}', textposition='outside')
            fig_dist.update_layout(**chart_layout(title="Evidence: G09 is the closest match in the SAME course"))
            st.plotly_chart(fig_dist, use_container_width=True)
        else:
            st.info("Evidence chart could not be generated. Required data (Group 10 student or failed concept counts) is missing.")
    else:
        st.info("Evidence chart could not be generated because student summary data is missing.")


st.error(
    "**Recommendation:** Dissolve G10. Transfer the single student to Group 09. "
    "We chose Group 09 because their performance and concept profile is the closest match, "
    "not just because it's the same course. Update group_id in students.csv and notify both instructors."
)

st.divider()

# ── Scene 2: Top 10 at-risk ─────────────────────────────────────────────────
st.markdown(
    "Risk score blends **35% attendance + 35% grade + "
    "15% engagement + 15% failed concepts**. "
    "**7 of the top 10** sit in Group 07 — "
    "this is a group-level crisis, not isolated cases."
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
            label=row["full_name"],
            value=row["group_name"],
            delta=f'{row["risk_score"]:.3f}',
            delta_color="inverse",
        )
    st.caption(
        "Hover the chart for full details (attendance, grade, failed concepts). "
        "Top 5 shown above — chart holds all 10."
    )

g07_count = int((top10["group_name"].str.contains("07", na=False)).sum()) if not top10.empty else 0
insight(f"**{g07_count} of the top 10** at-risk students are in Group 07.")

st.error("""
**Action:**
1. Contact all 10 students this week 
2. Schedule a Group 07 intervention session 
3. Alert the Group 07 instructor today 
""")
