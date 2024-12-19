import streamlit as st
from google.oauth2.service_account import Credentials
import pandas as pd
import gspread
import os

st.markdown(
    """
    <style>
        /* 更改 multiselect 组件的字体 */
        div.stMultiSelect > div > div {
            font-family: 'Times New Roman', sans-serif;  /* 字体类型 */
            font-size: 16px;  /* 字体大小 */
        }
        
        /* 更改 multiselect 中选中项的字体 */
        div.stMultiSelect > div > div > div > div {
            font-family: 'Times New Roman', monospace;
            font-size: 18px;
            font-weight: bold;
        }

        /* 更改 multiselect 按钮的字体 */
        div.stMultiSelect > div > div > div > button {
            font-family: 'Times New Roman', sans-serif;
            font-size: 14px;
            font-weight: normal;
        }
    </style>
    """,
    unsafe_allow_html=True
)

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = Credentials.from_service_account_info(
    st.secrets["GOOGLE_APPLICATION_CREDENTIALS"], 
    scopes=scope
)
gc = gspread.authorize(credentials)

def read_file(name,sheet):
  worksheet = gc.open(name).worksheet(sheet)
  rows = worksheet.get_all_values()
  df = pd.DataFrame.from_records(rows)
  df = pd.DataFrame(df.values[1:], columns=df.iloc[0])
  return df

st.title('Leasing Data')

Leasing_US = read_file("MOO HOUSING PRICING SHEET","December Leasing Tracker")
Leasing_US['Tenant Name'] = Leasing_US['Tenant Name'].replace('', pd.NA)
# Leasing_US = Leasing_US.drop(columns=[''])
Leasing_US = Leasing_US.dropna()
Leasing_US.columns=['Tenant','Property','Renewal','Agent','Lease Term','Term Catorgy','Number of beds','Deposit','Term','Signed Date','Special Note','Domestic']
Leasing_US.loc[Leasing_US['Renewal'] == "YES", 'Renewal'] = 'Renew'
Leasing_US.loc[Leasing_US['Renewal'] == "NO", 'Renewal'] = 'New'
Leasing_US.loc[Leasing_US['Renewal'] == "No", 'Renewal'] = 'New'
Leasing_US.loc[Leasing_US['Term Catorgy'] == "short", 'Term Catorgy'] = 'Short'
Leasing_US['Number of beds'] = pd.to_numeric(Leasing_US['Number of beds'], errors='coerce')
# Leasing_US['Number of beds'] = Leasing_US['Number of beds'].astype(int)
Leasing_US['Signed Date'] = pd.to_datetime(Leasing_US['Signed Date'],format = '%m/%d/%Y')
Leasing_US['Region'] = 'US'

Leasing_China = read_file("China Sales","Dec")
Leasing_China['Term length'] = Leasing_China['Term length'].replace(to_replace='1年', value='12个月', regex=True)
Leasing_China['Term length'] = Leasing_China['Term length'].str.replace('[^\d]', '', regex=True)
Leasing_China['Term length'] = Leasing_China['Term length'].astype(int)
Leasing_China.loc[Leasing_China['Term length'] >=6 , 'Term Catorgy'] = 'Long'
Leasing_China.loc[Leasing_China['Term length'] < 6 , 'Term Catorgy'] = 'Short'
Leasing_China['Region'] = 'China'
Leasing_China['Number of beds'] = 1
Leasing_China[['Term start', 'Term Ends']] = Leasing_China['Lease term and length'].str.split('-', expand=True)
Leasing_China['Term Ends'] ='20'+ Leasing_China['Term Ends']
Leasing_China['Term Ends'] = pd.to_datetime(Leasing_China['Term Ends'],format = '%Y.%m.%d')
Leasing_China.loc[Leasing_China['Term Ends'] <= '2025-09-01', 'Term'] = 'Spring'
Leasing_China.loc[Leasing_China['Term Ends'] > '2025-09-01', 'Term'] = 'Fall'
Leasing_China.loc[Leasing_China['Renewal'] == "新合同", 'Renewal'] = 'New'
Leasing_China.loc[Leasing_China['Renewal'] == "续租", 'Renewal'] = 'Renew'
Leasing_China.loc[Leasing_China['Renewal'] == "短租", 'Renewal'] = 'New'
Leasing_China.loc[Leasing_China['Renewal'] == "接转租", 'Renewal'] = 'Transfer'
Leasing_China.loc[Leasing_China['Renewal'] == "Leo", 'Renewal'] = 'Leo'
Leasing_China['Signed Date'] = pd.to_datetime(Leasing_China['Signed Date'],format = '%m/%d/%Y')
Leasing_China = Leasing_China.drop(['Lease term and length','Term start','Term Ends'],axis=1)
Leasing = pd.concat([Leasing_US,Leasing_China], join='inner',ignore_index=True)

def generate_pivot_table(df):
  Table = df.pivot_table(index=['Region','Agent'], columns=['Domestic','Term','Renewal','Term Catorgy'], values='Number of beds',aggfunc='sum',fill_value=0,margins=True)
  Table = Table.astype(int)
  return Table

from datetime import datetime
from datetime import datetime, timedelta
import time
today = datetime.now()
last_week = today - timedelta(weeks=1)
today_date = today.strftime('%Y-%m-%d')
last_week_date = last_week.strftime('%Y-%m-%d')
Leasing_Weekly = Leasing.loc[Leasing['Signed Date'].between(last_week_date,today_date) ]

Table = generate_pivot_table(Leasing_Weekly)
Table_All = generate_pivot_table(Leasing)
Table = Table.replace(0,"")
Table_All = Table_All.replace(0,"")

# st.title("动态更新时间戳")
# while True:
#     st.write(f"当前时间: {time.strftime('%Y-%m-%d')}")
#     time.sleep(1000)  # 每秒更新一次
#     st.rerun()
    
# st.title("Google Sheets 数据展示")
# st.write(Table)
# st.write(Table_All)

# # Show the page title and description.
# st.set_page_config(page_title="Movies dataset", page_icon="🎬")
# st.title("🎬 Movies dataset")
# st.write(
#     """
#     This app visualizes data from [The Movie Database (TMDB)](https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata).
#     It shows which movie genre performed best at the box office over the years. Just 
#     click on the widgets below to explore!
#     """
# )


# # Load the data from a CSV. We're caching this so it doesn't reload every time the app
# # reruns (e.g. if the user interacts with the widgets).
# @st.cache_data
# def load_data():
#     df = pd.read_csv("data/movies_genres_summary.csv")
#     return df


# df = load_data()

# # Show a multiselect widget with the genres using `st.multiselect`.
Region = st.multiselect(
    "选择地区",
    ["US", "China"],
      default=["US", "China"]
)

Term = st.multiselect(
    "选择长/短",
    ["Long", "Short"],
      default=["Long", "Short"]
)

Category =  st.multiselect(
    "选择春/秋季",
    ["Spring", "Fall"],
      default=["Spring", "Fall"]
)

Renewal =  st.multiselect(
    "选择合同种类",
    ["New", "Renew",'Transfer','Leo'],
      default=["New", "Renew",'Transfer']
)

Domestic =  st.multiselect(
    "选择房屋地区",
    ["USC", "UCLA",'UCI','Leo'],
      default=["USC", "UCLA",'UCI','Leo']
)

# # Show a slider widget with the years using `st.slider`.
from datetime import datetime

# 设置起始日期和结束日期
start_date = datetime(2024, 12, 1)  # 2024年12月1日
end_date = datetime(2024, 12, 31)  # 2024年12月31日

# 创建日期区间选择器
selected_dates = st.slider(
    "选择日期区间:",
    min_value=start_date,
    max_value=end_date,
    value=(start_date, end_date),  # 默认选定区间为12月1日至12月31日
    format="YYYY-MM-DD"  # 格式化显示日期
)

# 显示选择的日期区间
st.write(f"你选择的日期区间是: 从 {selected_dates[0].strftime('%Y-%m-%d')} 到 {selected_dates[1].strftime('%Y-%m-%d')}")

# Filter the dataframe based on the widget input and reshape it.
df_filtered = Leasing[(Leasing["Region"].isin(Region)) & (Leasing["Signed Date"].between(selected_dates[0],selected_dates[1]) & (Leasing["Term Catorgy"].isin(Term)) &(Leasing["Term"].isin(Category)) & (Leasing["Renewal"].isin(Renewal)))]
df_reshaped = generate_pivot_table(df_filtered)

# # Display the data as a table using `st.dataframe`.
st.write('Leasing Data')
st.dataframe(
    df_reshaped,
    use_container_width=True,
    # column_config={"selected_dates": st.column_config.TextColumn("Time")},
)
styled_pivot_table = df_reshaped.style.set_table_styles(
    [{'selector': 'thead th', 'props': [('text-align', 'center')]}]
)


while True:
    st.write(f"Last Update: {time.strftime('%Y-%m-%d')}")
    time.sleep(86400)  # 每秒更新一次
    st.rerun()
