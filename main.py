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


st.title('Klook POI Extractor')

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
except:
    print('Something went wrong. ')


st.header('3 - Confirm API Request Info')

user_key = st.secrets("API_key")
input_key = st.text_input(user_key)
selected_country = st.selectbox('Which country are you searching for?',st.secrets["country"])
selected_language = st.selectbox('Which language do you want to return?',st.secrets["language"])

####

done = False
used_query_name = set()
output=dict()
if st.button('Comfirm & Execute '+ str(len(query_list))+ ' POIs'):
    
    my_bar = st.progress(0, text='processing...')  
    for query_name in query_list:
        if query_name not in used_query_name:
            # new query name
            output[query_name] = [0,[]] #show times, query results

            #request info
            key = input_key 
            lang = selected_language
            loc="region:"+selected_country
            address = selected_country + " " + query_list[query_name][1]
            url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?locationbias={loc}&fields=name%2Cformatted_address&language={lang}&inputtype=textquery&input={address}&key={key}"

            #send request
            response = requests.get(url)
            data = response.json()
            candidates = data['candidates']

            #process response
            try:
                output[query_name][0] += 1
                for index, candidate in enumerate(candidates):
                    output[query_name][1].append(candidate['name'])
                    if index >= 3:
                        break
            except:
                output[query_name][1].append("NOT FOUND")
            finally:
                used_query_name.add(query_name)
        else:
            #發過query的就不要再發了，直接次數＋1就好
            output[query_name][0] += 1
        my_bar.progress(query_name/len(query_list), text='processing...')

    done = True #是否顯示下載按鈕
import csv

if done:
    csv_data = dict_to_csv(output)
    st.download_button(
    label="Download Result",
    data=csv_data,
    file_name='query output.csv',
    mime='text/csv')