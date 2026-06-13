# ╔══════════════════════════════════════════════════════════╗
# ║  STEP 5a — PRECOMPUTE & UPLOAD TO MONGODB ATLAS        ║
# ║  Run this ONCE in Colab after Step 4                   ║
# ╚══════════════════════════════════════════════════════════╝

# !pip install pymongo -q

from pymongo import MongoClient
import pandas as pd
import numpy as np

# ── Connect to Atlas ──────────────────────────────────────
MONGO_URI = "mongodb+srv://somiamoslhy_db_user:1bzHBIfg6Q5KOW9e@cluster0.dfjsase.mongodb.net/"
client = MongoClient(MONGO_URI)
db     = client["kayfa_analytics"]

def upload(collection_name, df, msg=True):
    """Drop collection and re-insert all rows."""
    col = db[collection_name]
    col.drop()
    if len(df) > 0:
        col.insert_many(df.to_dict('records'))
    if msg:
        print(f"  Uploaded {collection_name}: {len(df)} rows")


# ══════════════════════════════════════════════════════════
# 1. KPIs — single-document summary
# ══════════════════════════════════════════════════════════
kpis = {
    "total_students"      : int(len(students)),
    "total_groups"        : int(len(groups)),
    "total_courses"       : int(len(courses)),
    "platform_attendance" : round(float(attendance_full['attended_flag'].mean() * 100), 1),
    "platform_avg_grade"  : round(float(grades_full[grades_full['orphan']==False]['score_pct'].mean()), 1),
    "total_events"        : int(len(eng_full)),
    "at_risk_count"       : int((student_summary['segment'] == 'At-Risk').sum()),
}
db["kpis"].drop()
db["kpis"].insert_one(kpis)
print("  Uploaded kpis: 1 document")


# ══════════════════════════════════════════════════════════
# 2. Group attendance summary (Q1)
# ══════════════════════════════════════════════════════════
g_att = attendance_full.copy()
g_att['attended_flag'] = (g_att['status'] == 'attended').astype(int)

group_att = (
    g_att.groupby(['group_name'])['attended_flag']
    .agg(attendance_rate='mean', total_sessions='count')
    .reset_index()
)
group_att['attendance_rate'] = (group_att['attendance_rate'] * 100).round(1)
group_att = group_att.merge(
    groups[['group_name','course_id','instructor']], on='group_name', how='left'
)
upload("group_attendance", group_att)


# ══════════════════════════════════════════════════════════
# 3. Grade summaries by course and type (Q2, Q3)
# ══════════════════════════════════════════════════════════
grades_clean = grades_full[grades_full['orphan'] == False].copy()

# by course
course_grades = (
    grades_clean.groupby('course_name')['score_pct']
    .agg(avg_grade='mean', std_grade='std', count='count')
    .reset_index().round(2)
)
upload("grade_by_course", course_grades)

# by assessment type
type_grades = (
    grades_clean.groupby('type')['score_pct']
    .agg(avg_grade='mean', std_grade='std', count='count')
    .reset_index().round(2)
)
upload("grade_by_type", type_grades)


# ══════════════════════════════════════════════════════════
# 4. Student summary table (Q4, Q5, Q10, Q11, Q14)
# ══════════════════════════════════════════════════════════
summary_cols = [
    'student_id','full_name','age','gender','city','group_id','group_name',
    'course_name','attendance_rate','avg_grade','login_count',
    'total_video_mins','failed_concept_count','segment','risk_score',
    'age_group'
]
# convert categoricals to string for MongoDB
ss_upload = student_summary[summary_cols].copy()
ss_upload['age_group'] = ss_upload['age_group'].astype(str)
ss_upload = ss_upload.fillna(0)
upload("student_summary", ss_upload)


# ══════════════════════════════════════════════════════════
# 5. Concept failure rates (Q6, Q7)
# ══════════════════════════════════════════════════════════
concept_fail = (
    cp_full.groupby(['concept_name','course_id'])['mastery_status']
    .apply(lambda x: round((x=='failed').sum() / len(x) * 100, 1))
    .reset_index()
)
concept_fail.columns = ['concept_name','course_id','fail_rate']
concept_fail = concept_fail.merge(
    courses[['course_id','course_name']], on='course_id', how='left'
)
upload("concept_failures", concept_fail)

# Recursion trend over time (Q7)
recursion = cp_full[cp_full['concept_name'] == 'Recursion'].copy()
recursion['timestamp'] = pd.to_datetime(recursion['timestamp'], errors='coerce')
recursion['month'] = recursion['timestamp'].dt.to_period('M').astype(str)
rec_trend = (
    recursion.groupby('month')
    .agg(avg_mastery=('score_pct','mean'), pass_rate=('mastery_status', lambda x: round((x=='passed').sum()/len(x)*100,1)))
    .reset_index().round(1)
)
upload("recursion_trend", rec_trend)


# ══════════════════════════════════════════════════════════
# 6. Late submission analysis (Q8)
# ══════════════════════════════════════════════════════════
subs_upload = subs_full[
    ['student_id','assessment_id','course_name','group_name',
     'is_late','hours_before_deadline','grade_score_pct','time_spent_minutes']
].dropna(subset=['grade_score_pct']).copy()
subs_upload['is_late'] = subs_upload['is_late'].astype(bool)
subs_upload['hours_before_deadline'] = subs_upload['hours_before_deadline'].fillna(0)
upload("submission_analysis", subs_upload)


# ══════════════════════════════════════════════════════════
# 7. Monthly time series — attendance + engagement (Q9)
# ══════════════════════════════════════════════════════════
att_time = attendance_full.copy()
att_time['session_datetime'] = pd.to_datetime(att_time['session_datetime'], errors='coerce')
att_time['month'] = att_time['session_datetime'].dt.to_period('M').astype(str)
att_monthly = (
    att_time[att_time['month'].between('2025-12','2026-06')]
    .groupby('month')['attended_flag']
    .mean().reset_index()
)
att_monthly['attendance_rate'] = (att_monthly['attended_flag'] * 100).round(1)

eng_monthly = (
    eng_full[eng_full['event_month'].between('2025-12','2026-06')]
    .groupby('event_month').size().reset_index(name='event_count')
    .rename(columns={'event_month':'month'})
)
time_series = att_monthly[['month','attendance_rate']].merge(
    eng_monthly, on='month', how='outer'
).sort_values('month').fillna(0)
upload("time_series", time_series)


# ══════════════════════════════════════════════════════════
# 8. Group size discrepancies (Q12)
# ══════════════════════════════════════════════════════════
real_counts = (
    students[students['group_id'].notna()]
    .groupby('group_id').size().reset_index(name='real_count')
)
q12 = groups.merge(real_counts, on='group_id', how='left').fillna(0)
q12['real_count'] = q12['real_count'].astype(int)
q12['diff'] = q12['real_count'] - q12['stated_num_students']
q12['flag'] = q12['diff'].apply(
    lambda d: 'Under-reported' if d > 5 else ('Over-reported' if d < -5 else 'Accurate')
)
upload("group_size_audit", q12[['group_id','group_name','stated_num_students','real_count','diff','flag']])


# ══════════════════════════════════════════════════════════
# 9. Top 10 at-risk students (Q14)
# ══════════════════════════════════════════════════════════
top10 = student_summary.nlargest(10, 'risk_score')[
    ['student_id','full_name','group_name','course_name',
     'attendance_rate','avg_grade','login_count',
     'failed_concept_count','risk_score']
].copy()
top10['rank'] = range(1, 11)
upload("at_risk_top10", top10)


# ══════════════════════════════════════════════════════════
# 10. Group grade trends (Q15)
# ══════════════════════════════════════════════════════════
grades_full['date']  = pd.to_datetime(grades_full['date'],  errors='coerce')
grades_full['month'] = grades_full['date'].dt.to_period('M').astype(str)
g_trends = (
    grades_full[grades_full['orphan'] == False]
    .groupby(['group_name','month'])['score_pct']
    .mean().reset_index().round(1)
)
g_trends = g_trends[g_trends['month'].between('2025-12','2026-06')]
upload("group_grade_trends", g_trends)


# ══════════════════════════════════════════════════════════
# DONE
# ══════════════════════════════════════════════════════════
print("\nAll collections uploaded to MongoDB Atlas:")
for col in db.list_collection_names():
    print(f"  {col}: {db[col].count_documents({})} documents")

client.close()