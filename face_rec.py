import numpy as np
import pandas as pd
import cv2
import os
import redis
from insightface.app import FaceAnalysis
from sklearn.metrics import pairwise
import time
from datetime import datetime

## connect to redis client
hostname = 'redis-16313.c15.us-east-1-2.ec2.redns.redis-cloud.com'
portnumber = '16313'
password = 'wHVGowA6401qo6CSQc3bpXZyAhAFNlP2'

r = redis.StrictRedis(host=hostname,
                      port=portnumber,
                      password=password)

######### 1. Extract data from database
def retrive_data(name):
    name = 'academy:register'
    retrive_dict = r.hgetall(name)
    retrive_series = pd.Series(retrive_dict)
    retrive_series = retrive_series.apply(lambda x: np.frombuffer(x,dtype=np.float32))
    index = retrive_series.index
    index =  list(map(lambda x: x.decode(),index))
    retrive_series.index = index
    retrive_df = retrive_series.to_frame().reset_index()
    retrive_df.columns = ['name_role','Features']
    retrive_df[['Name','Role']]=retrive_df['name_role'].apply(lambda x: x.split('@')).apply(pd.Series)
    return retrive_df[['Name','Role','Features']]

## configure face analysis
faceapp = FaceAnalysis(name = 'buffalo_sc', root = 'insightface_model', providers = ['CPUExecutionProvider'])
faceapp.prepare(ctx_id=0,det_size=(640,640), det_thresh=0.5)

def ml_search_algo(dataframe,feature_column,test_vector,name_role=['Name','Role'],thresh=0.4):
    dataframe = dataframe.copy()
    def is_valid_embedding(x):
        return isinstance(x, (np.ndarray, list)) and len(x) == 512

    dataframe = dataframe[dataframe[feature_column].apply(is_valid_embedding)]

    if dataframe.empty:
        return 'unknown', 'unknown'

    try:
        X_list = dataframe[feature_column].tolist()
    except KeyError:
        raise ValueError(f"Column '{feature_column}' not found in DataFrame. Available columns: {dataframe.columns.tolist()}")

    x = np.asarray(X_list)
    similar = pairwise.cosine_similarity(x,test_vector.reshape(1,512))
    similar_arr = np.array(similar).flatten()
    dataframe['cosine'] = similar_arr
    data_filter = dataframe.query(f'cosine>={thresh}')
    if len(data_filter) > 0:
        data_filter.reset_index(drop = True,inplace = True)
        argmax = data_filter['cosine'].argmax()
        person_name , person_role = data_filter.loc[argmax][name_role]
    else:
        person_name = 'unknown'
        person_role = 'unknown'

    return person_name,person_role

class RealTimePredic:
    def __init__(self):
        self.logs = dict(name=[],role = [],current_time = [])
    def reset_dict(self):
        self.logs = dict(name=[],role = [],current_time = [])
    def saveLogs_redis(self):
        dataframe = pd.DataFrame(self.logs)
        dataframe.drop_duplicates('name',inplace=True)
        name_list = dataframe['name'].tolist()
        role_list = dataframe['role'].tolist()
        ctime_list = dataframe['current_time'].tolist()
        encoded_data = []
        for name,role,ctime in zip(name_list,role_list,ctime_list):
            if name != 'unknown':
                concat_string = f"{name}@{role}@{ctime}"
                encoded_data.append(concat_string)
        if len(encoded_data) > 0:
            r.lpush('attendance:logss',*encoded_data)
        self.reset_dict()
    def face_prediction(self,test_image1,dataframe,feature_column,name_role=['Name','Role'],thresh=0.4):
        
        current_time = str(datetime.now())

        results = faceapp.get(test_image1)
        test_copy = test_image1.copy()

        for res in results:
            x1,y1,x2,y2 = res['bbox'].astype(int)
            embedding = res['embedding']
            person_name, person_role = ml_search_algo(dataframe,'Features',test_vector = embedding,name_role=name_role,thresh=thresh)
            if person_name == 'unknown':
                color = (0,0,255)
            else:
                color = (0,255,0)
            
            cv2.rectangle(test_copy,(x1,y1),(x2,y2),color)
            text_gen = person_name
            
            cv2.putText(test_copy,text_gen,(x1,y1),cv2.FONT_HERSHEY_DUPLEX,0.7,color,2)
            cv2.putText(test_copy,current_time,(x1,y2+10),cv2.FONT_HERSHEY_DUPLEX,0.7,color,2)
            
            self.logs['name'].append(person_name)
            self.logs['role'].append(person_role)
            self.logs['current_time'].append(current_time)
        
        
        return test_copy
    
## Registration form
class RegistrationForm:
    def __init__(self):
        self.sample = 0
    def reset(self):
        self.sample = 0

    def get_embedding(self,frame):
        results = faceapp.get(frame,max_num=1)
        embeddings = None
        for res in results:
            self.sample+=1
            x1,y1,x2,y2 = res['bbox'].astype(int)
            cv2.rectangle(frame,(x1,y1),(x2,y2),(0,255,0),1)
            text = f"samples = {self.sample}"
            cv2.putText(frame,text,(x1,y1),cv2.FONT_HERSHEY_DUPLEX,0.6,(255,255,0),2)
                # facial features
            embeddings = res['embedding']
        return frame,embeddings
    
    def save_data_in_redis_db(self,name,role):
        if name is not None:
            if name.strip() != '':
                key = f'{name}@{role}'
            else:
                return 'name_false'
        else:
            return 'name_false'
        
        if 'face_embedding.txt' not in os.listdir():
            return 'file_false'
        
        x_array = np.loadtxt('face_embedding.txt',dtype=np.float32)
        received_samples =int(x_array.size/512)
        x_array = x_array.reshape(received_samples,512)
        x_array = np.asarray(x_array)
        x_mean = x_array.mean(axis = 0)
        x_mean = x_mean.astype(np.float32)
        x_mean_bytes = x_mean.tobytes()
        r.hset(name = 'academy:register',key = key,value = x_mean_bytes)

        os.remove('face_embedding.txt')
        self.reset()

        return True
    
