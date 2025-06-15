import streamlit as st

st.set_page_config(page_title='Reporting',layout='wide')

st.subheader('Reporting')

from Home import face_rec
name = 'attendance:logs'
def load_logs(name,end = -1):
    logs_list = face_rec.r.lrange(name,start = 0, end = end)
    return logs_list

#tabs to show the info
tab1,tab2 = st.tabs(['Registered data','Logs'])
with tab1:
    if st.button('Refresh data'):
    # Retrive data from redis
        with st.spinner('Retriving data from redis....'):
            redis_face_db = face_rec.retrive_data(name='academy:register')
            st.dataframe(redis_face_db[['Name','Role']])
with tab2:
    if st.button('Refresh logs'):
        st.write(load_logs(name=name))
