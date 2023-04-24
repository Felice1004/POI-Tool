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

results = dict()
i = 0

try:
    data = data[data[colname_POI].notnull()] #清除值為NAN的資料

    for url in data[colname_URL]:
        for poi in data[data[colname_URL] == url][colname_POI]:
            # print(type(poi), poi)
            poi.replace("'",'')
            poi = poi.split(', ')
            for attraction in poi:  
                results[i] =  [url, attraction]
                i = i + 1
except:
    print('Something went wrong. ')


st.header('3 - API Request')
input_key = st.text_input('You API Key')
selected_country = st.selectbox('Which country are you searching for?',('Option','Taiwan','Korea','Vietnam'))
selected_region = st.selectbox('Which region are you searching for?',('Option','tw','kr','vn'))
selected_language = st.selectbox('Which language do you want to return?',('Option','zh-TW','en'))

done = False

if st.button('Execute '+ len(results)+ ' POIs'):
    
    my_bar = st.progress(0, text='processing...')  
    for k in results:
        key = input_key 
        lang = selected_language
        location="region:"+selected_region
        address = selected_country + " " + results[k][1]

        url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?locationbias={location}&fields=name%2Cformatted_address&language={lang}&inputtype=textquery&input={address}&key={key}"

        response = requests.get(url)
        data = response.json()
        candidates = data['candidates']

        try:
            results[k].append(candidates[0]['name'])
            results[k].append(candidates[0]['formatted_address'])
        except:
            results[k].append("NOT FOUND")
            print('fail', address)
        my_bar.progress(k/len(results), text='processing...')

    done = True
import csv

if done:
    csv_data = dict_to_csv(results)

    st.download_button(
    label="Download Result",
    data=csv_data,
    file_name='results.csv',
    mime='text/csv')