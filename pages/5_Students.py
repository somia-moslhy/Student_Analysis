import os
import sys

import pandas as pd
import plotly.express as px
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
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
    valid_age = ss[~ss["age_group"].isin([0, "0"])]
    age_g = valid_age.groupby("age_group", observed=True).agg(
        avg_grade=("avg_grade", "mean"),
        attendance_rate=("attendance_rate", "mean"),
        count=("student_id", "count"),
    ).reset_index().round(1)

    video_max = valid_age["total_video_mins"].max() or 1
    age_video = valid_age.groupby("age_group", observed=True)["total_video_mins"].mean().reset_index()
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

if not ss.empty:
    # Perform clustering dynamically
    cluster_features = ['attendance_rate', 'avg_grade', 'login_count',
                        'total_video_mins', 'failed_concept_count']
    # Ensure all features are present, fill with 0 if not.
    for feature in cluster_features:
        if feature not in ss.columns:
            ss[feature] = 0

    X = ss[cluster_features].fillna(0)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
    ss['cluster'] = kmeans.fit_predict(X_scaled)

    # Dynamically label clusters based on their characteristics
    means = ss.groupby('cluster')[['avg_grade', 'attendance_rate']].mean()
    means = means.sort_values(by='avg_grade', ascending=False)
    cluster_ids_by_grade = means.index.tolist()

    high_achievers_idx = cluster_ids_by_grade[0]
    at_risk_idx = cluster_ids_by_grade[3]
    mid_idx_1, mid_idx_2 = cluster_ids_by_grade[1], cluster_ids_by_grade[2]

    # Differentiate middle clusters by attendance
    if means.loc[mid_idx_1, 'attendance_rate'] > means.loc[mid_idx_2, 'attendance_rate']:
        silent_strugglers_idx, avg_engaged_idx = mid_idx_1, mid_idx_2
    else:
        silent_strugglers_idx, avg_engaged_idx = mid_idx_2, mid_idx_1

    label_map = {
        high_achievers_idx: 'High Achievers',
        avg_engaged_idx: 'Average Engaged',
        silent_strugglers_idx: 'Silent Strugglers',
        at_risk_idx: 'At-Risk'
    }
    ss['segment'] = ss['cluster'].map(label_map)

    segment_order = ['High Achievers', 'Average Engaged', 'Silent Strugglers', 'At-Risk']
    ss['segment'] = pd.Categorical(ss['segment'], categories=segment_order, ordered=True)

    COLOR_MAP = {
        'High Achievers': GREEN,
        'Average Engaged': ACCENT,
        'Silent Strugglers': '#ff7f0e',
        'At-Risk': DANGER
    }

    fig = px.scatter(
        ss.sort_values('segment'),
        x='attendance_rate', y='avg_grade',
        color='segment', size='failed_concept_count',
        size_max=25,
        hover_data=["full_name", "group_name", "login_count", "total_video_mins"],
        color_discrete_map=COLOR_MAP,
        facet_col='segment',
        title='Student Segmentation: Behavior Breakdown',
        labels={
            'attendance_rate': 'Attendance (%)', 'avg_grade': 'Avg Grade (%)',
            'segment': 'Segment', 'failed_concept_count': 'Failed Concepts',
        },
        opacity=0.8,
    )
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    fig.update_traces(marker=dict(line=dict(width=1, color='DarkSlateGrey')))
    fig.update_layout(showlegend=False, title_x=0.5)
    st.plotly_chart(fig, use_container_width=True)

    # Dynamically calculate and display metrics and insights
    stats_list = []
    for segment in segment_order:
        segment_df = ss[ss['segment'] == segment]
        if not segment_df.empty:
            stats_list.append({
                "segment": segment, "count": len(segment_df),
                "avg_grade": segment_df['avg_grade'].mean(),
            })

    if stats_list:
        cols = st.columns(len(stats_list))
        for col, stat in zip(cols, stats_list):
            col.metric(label=stat["segment"], value=stat["count"], delta=f"avg {stat['avg_grade']:.1f}%")

        at_risk_count = next((s['count'] for s in stats_list if s['segment'] == 'At-Risk'), 0)
        silent_strugglers_count = next((s['count'] for s in stats_list if s['segment'] == 'Silent Strugglers'), 0)
        insight(
            f"Clustering reveals **{at_risk_count} At-Risk** students (low attendance & grade) and "
            f"**{silent_strugglers_count} Silent Strugglers** (high attendance, low grade)."
        )
        decision(
            "Prioritize outreach to the At-Risk group. "
            "Deploy targeted learning support, not attendance nudges, for the Silent Strugglers."
        )

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
