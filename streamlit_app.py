import streamlit as st
from google.oauth2.service_account import Credentials
import pandas as pd
import gspread
import os
from gspread_dataframe import set_with_dataframe

os.environ['TZ'] = 'America/Los Angeles'

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

def generate_pivot_table(df,index,columns):
  Table = df.pivot_table(index=index, columns=columns, values='Number of beds',aggfunc='sum',fill_value=0,margins=True)
  Table = Table.astype(int)
  return Table

from datetime import datetime
from datetime import datetime, timedelta
import time
# today = datetime.now()
# last_week = today - timedelta(weeks=1)
# today_date = today.strftime('%Y-%m-%d')
# last_week_date = last_week.strftime('%Y-%m-%d')
# Leasing_Weekly = Leasing.loc[Leasing['Signed Date'].between(last_week_date,today_date) ]

# Table = generate_pivot_table(Leasing_Weekly)
# Table_All = generate_pivot_table(Leasing)
# Table = Table.replace(0,"")
# Table_All = Table_All.replace(0,"")


Leasing_all = read_file('Leasing Database','Sheet1')
Leasing_all['Number of beds'] = pd.to_numeric(Leasing_all['Number of beds'], errors='coerce')
Leasing_all['Signed Date'] = pd.to_datetime(Leasing_all['Signed Date'],format = 'mixed')

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
start_date = datetime(2024, 11, 1)  # 2024年11月1日
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
df_filtered = Leasing_all[(Leasing_all["Region"].isin(Region)) & (Leasing_all["Signed Date"].between(selected_dates[0],selected_dates[1]) & (Leasing_all["Term Catorgy"].isin(Term)) &(Leasing_all["Term"].isin(Category)) & (Leasing_all["Renewal"].isin(Renewal)))]
st.sidebar.header("选择透视表展示")
row_options = st.sidebar.multiselect('请选择展示行', options=['Region','Agent'], default=['Region'])
column_options = st.sidebar.multiselect('请选择展示列', options=['Domestic','Term','Renewal','Term Catorgy'], default=['Domestic','Term','Renewal'])
df_reshaped = generate_pivot_table(df_filtered,row_options,column_options)

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

old = read_file('Leasing Database','Sheet1')
old = old.astype(Leasing.dtypes.to_dict())
combined_data = pd.concat([old, Leasing], ignore_index=True)
Temp = pd.concat([old, combined_data])
final_data = Temp[Temp.duplicated(subset = ['Tenant','Property','Renewal'],keep=False) == False]

target_spreadsheet_id = 'Leasing Database'  # 目标表格的ID
target_sheet_name = 'Sheet1'  # 目标表格的工作表名称
target_sheet = gc.open(target_spreadsheet_id).worksheet(target_sheet_name)

# set_with_dataframe(target_sheet, final_data, row=(len(old) + 2),include_column_header=False)

while True:
    st.write(f"Last Update: {time.strftime('%Y-%m-%d')}")
    time.sleep(86400)  # 每秒更新一次
    st.rerun()
