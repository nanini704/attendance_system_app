from Home import st


st.set_page_config(page_title='Prediction')

from Home import face_rec

st.subheader('Real-Time Face prediction')

# Retrive data from redis
with st.spinner('Retriving data from redis....'):
    redis_face_db = face_rec.retrive_data(name='academy:register')
    st.dataframe(redis_face_db)
st.success('data loaded succesfully')

import time
waitTime = 30
setTime = time.time()
realtimepred = face_rec.RealTimePredic()
# real time prediction
#call back function
from streamlit_webrtc import webrtc_streamer
import av


def video_frame_callback(frame):
    global setTime
    img = frame.to_ndarray(format="bgr24")

    pred_img = realtimepred.face_prediction(img,redis_face_db,
                                        'Features',['Name','Role'],thresh=0.5)
    
    timenow = time.time()
    difftime = timenow - setTime
    if difftime >= waitTime:
        realtimepred.saveLogs_redis()
        setTime = time.time()
        print('save data to redis database')


    return av.VideoFrame.from_ndarray(pred_img, format="bgr24")


webrtc_streamer(key="realtimepred", video_frame_callback=video_frame_callback,
rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
    }
)
