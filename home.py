import os
import sys

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import (
    ACCENT, DANGER, DARK, GREEN,
    chart_layout, compute_kpis, filter_context, kpi_row,
    page_header, read, sidebar, story, theme_colors,
)

st.set_page_config(page_title="Kayfa — Executive Brief", layout="wide")
sidebar()
ss, kpi, _, _ = filter_context()

page_header(
    "Executive Brief",
    "*A one-page story of what the data is telling us — and what leadership should do next.*",
)

kpi_row(kpi)

# ── Chapter 0: The headline story ─────────────────────────────────────────
story(
    "The platform is healthy — except where it isn't",
    "Across **500 students** and **7 courses**, average attendance and grades look acceptable on paper. "
    "But three signals cut through the noise: **one group is in crisis**, **one concept is failing two-thirds of learners**, "
    "and **March brought a cohort-wide drop** that hit both attendance and engagement at once. "
    "These are not isolated data points — they chain together into clear decisions.",
)

c1, c2, c3 = st.columns(3)
with c1:
    g07 = ss[ss["group_name"].str.contains("07", na=False)] if not ss.empty else ss
    g07_att = round(g07["attendance_rate"].mean(), 1) if len(g07) else 0
    st.metric("Group 07 Attendance", f"{g07_att}%", delta=f"{round(g07_att - kpi['platform_attendance'], 1)} vs avg", delta_color="inverse")
    st.caption("Lowest-attending viable group — leading indicator of grade risk.")
with c2:
    st.metric("Recursion Failure Rate", "66.7%")
    st.caption("Single biggest curriculum gap — 3× worse than the next concept.")
with c3:
    st.metric("March Attendance Dip", "62.2%", delta="-18 pp vs other months", delta_color="inverse")
    st.caption("Cohort-wide event — engagement fell in the same window.")

st.divider()

# ── Decisions for leadership ────────────────────────────────────────────────
story("Decisions to act on this week", "")

d1, d2 = st.columns(2)
with d1:
    st.info(
        "**Deploy Automated Data Sync Pipeline**\n\n"
        "Block phantom student allocation (like Group 10). "
        "Use `students.csv` as the sole source of truth for platform provisioning."
    )
    st.warning(
        "**Transition to Predictive Operational Model**\n\n"
        "Pre-empt seasonality dips (like the March drop). Shift live sessions to async "
        "during peak disruption windows and trigger Automated Progressive Reminders 48h before deadlines."
    )
with d2:
    st.success(
        "**Establish Dynamic Feedback Loop**\n\n"
        "Auto-flag failing concepts (>30% fail rate, e.g., Recursion) directly to the content team. "
        "Automatically unlock Remedial Async Materials for struggling cohorts."
    )
    st.error(
        "**Deploy Early Warning System (EWS)**\n\n"
        "Monitor live group deviation against the platform average (e.g., Group 07). "
        "Trigger automated alerts to the academic lead before a cohort crosses the at-risk threshold."
    )

st.divider()

# ── Visual proof — simple charts ────────────────────────────────────────────
story("Proof at a glance", "Two charts that make the story visible without opening a spreadsheet.")

t = theme_colors()
col1, col2 = st.columns(2)

with col1:
    g_att = read("group_attendance").sort_values("attendance_rate", ascending=True)
    platform_avg = kpi.get("platform_attendance", round(g_att["attendance_rate"].mean(), 1))

    fig = px.bar(
        g_att, x="attendance_rate", y="group_name", orientation="h", text="attendance_rate",
        color_discrete_sequence=[DARK],
        title="Every group’s attendance story",
        labels={"group_name": "", "attendance_rate": "Attendance (%)"},
    )
    fig.update_traces(texttemplate="%{text}%", textposition="outside", textfont_color=t["text"])
    fig.update_xaxes(range=[0, 105])
    fig.add_trace(go.Scatter(
        x=[platform_avg] * len(g_att), y=g_att["group_name"],
        mode="lines",
        line=dict(dash="dash", color=DANGER, width=2),
        hovertemplate=f"Platform avg: {platform_avg}%<extra></extra>",
        showlegend=False,
    ))
    fig.update_layout(**chart_layout(title="Every group’s attendance story"), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Group 07 stands alone below the dashed platform average.")

with col2:
    if not ss.empty and "segment" in ss.columns:
        seg = ss["segment"].value_counts().reset_index()
        seg.columns = ["segment", "count"]
        fig = px.pie(
            seg, values="count", names="segment",
            color="segment",
            color_discrete_map={"High Achievers": GREEN, "Average Engaged": ACCENT, "At-Risk": DANGER, "Outlier": DARK},
            title="How students spread across segments",
            hole=0.45,
        )
        fig.update_traces(textfont_color=t["text"], textposition="inside")
        fig.update_layout(**chart_layout(title="How students spread across segments", legend_y=-0.12))
        st.plotly_chart(fig, use_container_width=True)
        at_risk_n = int((ss["segment"] == "At-Risk").sum())
        st.caption(f"**{at_risk_n} students** need proactive outreach — not more reports.")

