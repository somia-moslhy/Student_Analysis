import streamlit as st

home = st.Page("home.py", title="Executive Brief", icon="🏠", default=True)
ch1  = st.Page("pages/1_Attendance.py",  title="01 · Showing Up")
ch2  = st.Page("pages/2_Grades.py",      title="02 · How They Perform")
ch3  = st.Page("pages/3_Engagement.py",  title="03 · Staying Connected")
ch4  = st.Page("pages/4_Concepts.py",    title="04 · Where Learning Breaks")
ch5  = st.Page("pages/5_Students.py",    title="05 · Who They Are")
ch6  = st.Page("pages/6_AtRisk.py",      title="06 · Who Needs Us Now")

pg = st.navigation({
    "Leadership": [home],
    "The Story": [ch1, ch2, ch3, ch4, ch5, ch6],
})
pg.run()
