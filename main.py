import pandas as pd
import requests
import streamlit as st
import io

def dict_to_csv(data):
    csv_string = io.StringIO()
    csv_writer = csv.writer(csv_string)
    csv_writer.writerow(['Key', 'Value'])
    for key, value in data.items():
        csv_writer.writerow([key, value])
    return csv_string.getvalue()

def get_colname_options(data):
    colnames = []
    for col in data.columns:
        colnames.append(col)
    return colnames


st.set_page_config(
   page_title="Klook POI 資料清洗小工具",
   page_icon="🧽",
   layout="wide",
   initial_sidebar_state="expanded",
)


st.title('Klook POI Data CLeaning Tool')


#----------------------------------------#
st.header('1. Upload a CSV File')
uploaded_file = st.file_uploader("Choose a csv file containing targeted parsed POI")

colnames = []
data = pd.DataFrame()
if uploaded_file is not None:
    data = pd.read_csv(uploaded_file)
    data.rename(columns={'Top ranked URL (article)\nSource:Ahrefs': 'URL'}, inplace=True)
    st.write('Preview data')
    st.write(data)
    colnames = get_colname_options(data)
    
#----------------------------------------#
st.header('2 - Select POI Column')
colname_URL = st.selectbox(
    '2.1 Choose the column that contains URL', colnames)
colname_POI = st.selectbox(
    '2.2 Choose the column that contains POI', colnames)

query_list = dict()
i = 0
try:
    data = data[data[colname_POI].notnull()] #清除值為NAN的資料

    for url in data[colname_URL]:
        for poi in data[data[colname_URL] == url][colname_POI]:
            # print(type(poi), poi)
            poi.replace("'",'')
            poi = poi.split(', ')
            for poi_name in poi:  
                query_list[i] =  [url, poi_name]
                i +=  1
except:
    print('Something went wrong. ')


st.header('3 - Confirm API Request Info')

selected_country = st.selectbox('Which country are you searching for?',st.secrets["country"])
selected_language = st.selectbox('Which language do you want to return?',st.secrets["language"])
selected_query_mode = st.selectbox('How many queries you would like to execute?(Please check your free quota)',st.secrets["test_mode"])
key = st.secrets["API_key"]
lang = selected_language
loc="region:"+selected_country
####

done = False
used_query_name = set()
used_url = set()
output=dict()
query_times = 0

if selected_query_mode == "all":
    message = 'Comfirm & Execute All '+ str(len(query_list))+ ' POIs'
else :
    message = 'Comfirm & Execute Only TOP'+ str(selected_query_mode)+ ' POIs'

if st.button(message):
    my_bar = st.progress(0, text='processing...')  
    for dict_key in query_list:
        query_url = query_list[dict_key][0]
        query_name = str.lower(query_list[dict_key][1])

        #只搜尋新地名
        if query_name not in used_query_name:
            # new query name
            output[dict_key] = [0, query_url, query_name, []] #show times, url, query name, query results
            # output[dict_key][3].append('TEST')
            print('hi')
            #request
            address = selected_country + " " + query_name
            url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?locationbias={loc}&fields=name%2Cformatted_address&language={lang}&inputtype=textquery&input={address}&key={key}"

            #send request
            response = requests.get(url)
            data = response.json()
            candidates = data['candidates']

            #process response
            try:
                print('tried')
                #只取搜尋結果前三個
                for index, candidate in enumerate(candidates):
                    # output[dict_key][3].append('TEST')
                    output[dict_key][3].append(candidate['name'])
                    if index >= 3:
                        break
            except:
                output[dict_key][3].append("NOT FOUND")
            finally:
                query_times +=1
                output[dict_key][0] += 1
                used_query_name.add(query_name)
        else:
            #發過query的就不要再發了，直接次數＋1就好
            output[query_name][0] += 1

        # 更新進度條
        if selected_query_mode == 'all':
            my_bar.progress(query_times/len(query_list), text='processing...')
        else:
            my_bar.progress(query_times/int(selected_query_mode), text='processing...')

        #依據選擇的測試模式，判斷是否終止查詢
        if (str(selected_query_mode) != "all") & (str(query_times) == str(selected_query_mode)):
            break
    done = True #是否顯示下載按鈕

import csv

if done:
    csv_data = dict_to_csv(output)
    st.download_button(
    label="Download Result",
    data=csv_data,
    file_name='query output.csv',
    mime='text/csv')