import streamlit as st

st.set_page_config(page_title= 'Attendance_System', layout='wide')

st.header('Face Recognition Attendance System')

with st.spinner("Loading models and connecting to redis db..."):
    import face_rec

st.success('Model loaded succesfully')
st.success('redis db connected succesfully')