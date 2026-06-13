import os
import sys

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import (
    ACCENT, DANGER, DARK,
    chart_layout, filter_context, insight, decision, page_header,
    read, sidebar, story, theme_colors,
)

st.set_page_config(page_title="Showing Up", layout="wide")
sidebar()
ss, kpi, sel_courses, sel_groups = filter_context()

page_header(
    "Chapter 1 · Showing Up",
    "*Before grades or engagement matter, students have to walk through the door — "
    "this chapter follows who shows up, who doesn't, and when the whole cohort went quiet.*",
)

# ── Scene 1 ───────────────────────────────────────────────────────────────
story(
    "One group fell off the cliff",
    "Most groups cluster between 78–85% attendance. **Group 07** is the outlier — "
    "well below everyone else and below the platform average. That gap is not noise; "
    "it is the first warning sign before grades slip.",
)

g_att = read("group_attendance").sort_values("attendance_rate", ascending=True)
if sel_groups:
    g_att = g_att[g_att["group_name"].isin(sel_groups)]
platform_avg = kpi.get("platform_attendance", round(g_att["attendance_rate"].mean(), 1))
t = theme_colors()

fig = px.bar(
    g_att, x="attendance_rate", y="group_name", orientation="h", text="attendance_rate",
    color_discrete_sequence=[DARK],
    title="Attendance across groups — one line tells the average story",
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
fig.update_layout(**chart_layout(title="Attendance across groups — one line tells the average story"), showlegend=False)
st.plotly_chart(fig, use_container_width=True)

insight(
    "Group 07 sits near **66–68%** — the only group severely below the platform average. "
    "Group 10’s rate looks middling but reflects just one real student after data cleaning."
)
decision("Investigate Group 07 immediately — low attendance is a leading indicator of the grade deficit in Chapter 2.")

st.divider()

# ── Scene 2 ───────────────────────────────────────────────────────────────
story(
    "March was the month everything dipped",
    "Attendance and engagement do not move independently. In **March 2026** both collapsed together — "
    "a cohort-wide signal, not a single bad group.",
)

ts = read("time_series").sort_values("month")

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=ts["month"], y=ts["attendance_rate"],
    mode="lines+markers+text",
    name="Attendance Rate (%)",
    line=dict(color=DARK, width=3),
    marker=dict(size=9, color=DARK),
    text=ts["attendance_rate"].astype(str),
    textposition="top center",
    textfont=dict(size=9),
    yaxis="y1",
))
fig.add_trace(go.Bar(
    x=ts["month"], y=ts["event_count"],
    name="Engagement Events",
    marker_color=ACCENT,
    opacity=0.5,
    yaxis="y2",
))

layout = chart_layout(title="The March dip — attendance and engagement fell together", legend_y=-0.22)
layout["yaxis"] = dict(title="Attendance (%)", range=[50, 95], gridcolor=t["grid"])
layout["yaxis2"] = dict(title="Engagement Events", overlaying="y", side="right", gridcolor=t["grid"])
fig.update_layout(**layout)

fig.add_annotation(
    x="2026-03", y=62.2,
    text="March: 62.2%\n(both metrics fall)",
    font=dict(size=11, color=DANGER),
    showarrow=True, arrowcolor=DANGER,
    bgcolor=t["annotation_bg"], bordercolor=DANGER, borderpad=5,
)
st.plotly_chart(fig, use_container_width=True)

insight(
    "Every other month sits between **78–81%** attendance. March dropped to **62.2%** "
    "while engagement events fell in the same window — likely Ramadan or exam overlap."
)
decision("Provide recorded sessions and async alternatives before the next known disruption window.")
