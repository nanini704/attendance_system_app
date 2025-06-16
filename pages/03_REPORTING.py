import streamlit as st
import pandas as pd
import datetime

#st.set_page_config(page_title='Reporting',layout='wide')

st.subheader('Reporting')

from Home import face_rec
name = 'attendance:logss'
def load_logs(name,end = -1):
    logs_list = face_rec.r.lrange(name,start = 0, end = end)
    return logs_list

#tabs to show the info
tab1,tab2,tab3 = st.tabs(['Registered data','Logs','Attendance Report'])
with tab1:
    if st.button('Refresh data'):
    # Retrive data from redis
        with st.spinner('Retriving data from redis....'):
            redis_face_db = face_rec.retrive_data(name='academy:register')
            st.dataframe(redis_face_db[['Name','Role']])
with tab2:
    if st.button('Refresh logs'):
        st.write(load_logs(name=name))

with tab3:
    st.subheader('Attendance Report')
    logs_list = load_logs(name=name)
    convert_byte_to_string = lambda x: x.decode('utf-8')
    logs_list_string = list(map(convert_byte_to_string,logs_list))
    
    split_string = lambda x: x.split('@')
    logs_list_nested = list(map(split_string,logs_list_string))
    
    
    logs_df = pd.DataFrame(logs_list_nested, columns = ['Name','Role','TimeStamp'])
    
    logs_df['TimeStamp'] = pd.to_datetime(logs_df['TimeStamp'], format='mixed', dayfirst=False, errors='coerce')
    logs_df['Date'] = logs_df['TimeStamp'].dt.date
   

    reports_df = logs_df.groupby(by=['Date','Name','Role']).agg(
        in_time = pd.NamedAgg('TimeStamp','min'),
        out_time = pd.NamedAgg('TimeStamp','max')
    ).reset_index()
    reports_df['in_time'] = pd.to_datetime(reports_df['in_time'])
    reports_df['out_time'] = pd.to_datetime(reports_df['out_time'])

    reports_df['Duration'] = reports_df['out_time'] - reports_df['in_time']


    all_dates = reports_df['Date'].unique()
    name_role = reports_df[['Name','Role']].values.tolist()
    date_name_role_zip = []
    for dt in all_dates:
        for name,role in name_role:
            date_name_role_zip.append([dt,name,role])

    date_name_role_zip_df = pd.DataFrame(date_name_role_zip,columns= ['Date','Name','Role'])
    date_name_role_zip_df = pd.merge(date_name_role_zip_df,reports_df,how='left',on=['Date','Name','Role'])
    date_name_role_zip_df['Duration_seconds'] = date_name_role_zip_df['Duration'].dt.seconds
    date_name_role_zip_df['Duration_hours'] = date_name_role_zip_df['Duration_seconds'] / (60*60)

    def status_marker(x):
        if pd.Series(x).isnull().all():
            return 'Absent'
        elif x >= 0 and x <= 1:
            return 'Absent(less than an hour)'
        elif x >= 1  and x <= 6:
            return 'Half Day Present'
        elif x >= 6:
            return 'Present'
        
    date_name_role_zip_df['Status'] = date_name_role_zip_df['Duration_hours'].apply(status_marker)
    st.write(date_name_role_zip_df)


    st.subheader('Reports')

    t1,t2 = st.tabs(['Complete Report','Filter Report'])
    with t1:
        st.subheader('Complete Report')
        st.dataframe(date_name_role_zip_df)
    with t2:
        st.subheader('Filter Report')
        
        date_in = str(st.date_input('Filter Report',datetime.datetime.now().date()))

        name_list = date_name_role_zip_df['Name'].unique().tolist()
        name_in = st.selectbox('Select Name',['ALL']+name_list)

        role_list = date_name_role_zip_df['Role'].unique().tolist()
        role_in = st.selectbox('Select Role',['ALL']+role_list)

        duration_in = st.slider('Filter the duration in hour greater than ',0,15,6)

        status_list = date_name_role_zip_df['Status'].unique().tolist()
        status_in = st.multiselect('Select the status ',['ALL']+status_list)

        if st.button('Submit'):
            date_name_role_zip_df['Date'] =  date_name_role_zip_df['Date'].astype(str)
            filter_df = date_name_role_zip_df.query(f'Date == "{date_in}"')

            if name_in != 'ALL':
                filter_df=filter_df.query(f'Name == "{name_in}"')
            if role_in != 'ALL':
                filter_df=filter_df.query(f'Role == "{role_in}"')
            if duration_in > 0:
                filter_df=filter_df.query(f'Duration_hours == {duration_in}')

            if 'ALL' in status_in:
                filter_df = filter_df
            elif len(status_in) > 0:
                filter_df['status_condition'] = filter_df['Status'].apply(lambda x: True if x in status_in else False)
                filter_df= filter_df.query(f'status_condition == True')
                filter_df.drop(columns='status_condition',inplace = True)
            else:
                filter_df = filter_df

            st.dataframe(filter_df)