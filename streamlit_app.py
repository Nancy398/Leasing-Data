import streamlit as st
from google.oauth2.service_account import Credentials
import pandas as pd
import gspread
import os
from gspread_dataframe import set_with_dataframe


import streamlit as st
from google.oauth2.service_account import Credentials
import pandas as pd
import gspread
import os
from gspread_dataframe import set_with_dataframe
from datetime import datetime
from datetime import datetime, timedelta
import time

st.title('Leasing Data')

@st.cache_data(ttl=300)
def read_file(name,sheet):
  scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
  credentials = Credentials.from_service_account_info(
  st.secrets["GOOGLE_APPLICATION_CREDENTIALS"], 
  scopes=scope)
  gc = gspread.authorize(credentials)
  worksheet = gc.open(name).worksheet(sheet)
  rows = worksheet.get_all_values()
  df = pd.DataFrame.from_records(rows)
  df = pd.DataFrame(df.values[1:], columns=df.iloc[0])
  return df
  
@st.cache_data(ttl=300)
def open_file(url):
  scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
  credentials = Credentials.from_service_account_info(
  st.secrets["GOOGLE_APPLICATION_CREDENTIALS"], 
  scopes=scope)
  gc = AuthorizedSession(credentials)
  worksheet = gc.get(url)
  return worksheet
  

def generate_pivot_table(df,index,columns):
  Table = df.pivot_table(index=index, columns=columns, values='Number of beds',aggfunc='sum',fill_value=0,margins=True)
  Table = Table.astype(int)
  return Table

Leasing_US = read_file("MOO HOUSING PRICING SHEET","April 2025 Leasing Tracker")
# Leasing_US['Tenant Name'] = Leasing_US['Tenant Name'].replace('', pd.NA)
# Leasing_US = Leasing_US.drop(columns=[''])
Leasing_US = Leasing_US.dropna()
Leasing_US.columns=['Tenant','Property','Renewal','Agent','Lease Term','Term Catorgy','Number of beds','Deposit','Term','Signed Date','Special Note','Domestic','Column 1']
Leasing_US.loc[Leasing_US['Renewal'] == "YES", 'Renewal'] = 'Renew'
Leasing_US.loc[Leasing_US['Renewal'] == "NO", 'Renewal'] = 'New'
Leasing_US.loc[Leasing_US['Renewal'] == "No", 'Renewal'] = 'New'
Leasing_US.loc[Leasing_US['Renewal'] == "Lease Transfer", 'Renewal'] = 'Transfer'
Leasing_US.loc[Leasing_US['Term Catorgy'] == "short", 'Term Catorgy'] = 'Short'
Leasing_US['Number of beds'] = pd.to_numeric(Leasing_US['Number of beds'], errors='coerce')
# Leasing_US['Number of beds'] = Leasing_US['Number of beds'].astype(int)
# Leasing_US['Signed Date'] = pd.to_datetime(Leasing_US['Signed Date'],format='mixed')
Leasing_US['signed date'] = pd.to_datetime(Leasing_US['Signed Date'].astype(str), errors='coerce')
Leasing_US = Leasing_US[Leasing_US['signed date'].notna()]
# Leasing_US['Signed Date'] = Leasing_US['Signed Date'].dt.date
Leasing_US['Region'] = 'US'

Leasing_China = read_file("China Sales","Apr")
Leasing_China['Term length'] = Leasing_China['Term length'].astype(str)  # 确保是字符串
Leasing_China['Term length'] = Leasing_China['Term length'].replace(to_replace='1年', value='12个月', regex=True)
Leasing_China['Term length'] = Leasing_China['Term length'].str.replace(r'[^\d]', '', regex=True)  # 只保留数字
Leasing_China['Term length'] = Leasing_China['Term length'].apply(lambda x: x if x.strip() else '0')  # 处理空字符串
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
Leasing_China.loc[Leasing_China['Renewal'] == "换房续租", 'Renewal'] = 'Transfer'
Leasing_China.loc[Leasing_China['Renewal'] == "Leo", 'Renewal'] = 'Leo'
Leasing_China['Signed Date'] = pd.to_datetime(Leasing_China['Signed Date'])
Leasing_China['Signed Date'] = Leasing_China['Signed Date'].dt.date
Leasing_China = Leasing_China.drop(['Lease term and length','Term start','Term Ends'],axis=1)
Leasing = pd.concat([Leasing_US,Leasing_China], join='inner',ignore_index=True)

Leasing_all = read_file('Leasing Database','Sheet1')
Leasing_all['Number of beds'] = pd.to_numeric(Leasing_all['Number of beds'], errors='coerce')
# Leasing_all['Number of beds'].fillna(0, inplace=True)
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
      default=["Fall"]
)

Renewal =  st.multiselect(
    "选择合同种类",
    ["New", "Renew",'Transfer','Leo'],
      default=["New", "Renew"]
)

Domestic =  st.multiselect(
    "选择房屋地区",
    ["USC", "UCLA",'UCI','Leo'],
      default=["USC"]
)


# 设置起始日期和结束日期
start_date = datetime(2024, 9, 1)  # 2024年11月1日
end_date = datetime(2025, 4, 30) 

# 创建日期区间选择器
# selected_dates = st.slider(
#     "选择日期区间:",
#     min_value=start_date,
#     max_value=end_date,
#     value=(start_date, end_date),  # 默认选定区间为12月1日至12月31日
#     format="YYYY-MM-DD"  # 格式化显示日期
# )
# 
col1, col2 = st.columns(2)

# 在第一个列中添加开始日期选择器
with col1:
    start_selected = st.date_input(
        "From:",
        value=start_date,
        min_value=start_date,
        max_value=end_date
    )

# 在第二个列中添加结束日期选择器
with col2:
    end_selected = st.date_input(
        "To:",
        value=end_date,
        min_value=start_date,
        max_value=end_date
    )

# 显示用户选择的日期范围
st.write(f"您选择的日期范围是：{start_selected} 至 {end_selected}")

# # 显示选择的日期区间
# st.write(f"你选择的日期区间是: 从 {start_selected}.strftime('%Y-%m-%d')} 到 {end_selected.strftime('%Y-%m-%d')}")
start_selected = pd.Timestamp(start_selected)
end_selected = pd.Timestamp(end_selected)
# Filter the dataframe based on the widget input and reshape it.
df_filtered = Leasing_all[(Leasing_all["Region"].isin(Region)) & (Leasing_all["Signed Date"].between(start_selected,end_selected) & (Leasing_all["Term Catorgy"].isin(Term)) &(Leasing_all["Term"].isin(Category)) & (Leasing_all["Renewal"].isin(Renewal)) & (Leasing_all["Domestic"].isin(Domestic)))]

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

with st.expander("Click to see DataFrame"):
    st.dataframe(
        df_filtered,
        use_container_width=True,
        # column_config={"selected_dates": st.column_config.TextColumn("Time")},
      )
@st.cache_data(ttl=300)
def save_data():
  old = read_file('Leasing Database','Sheet1')
  old = old.astype(Leasing.dtypes.to_dict())
  combined_data = pd.concat([old, Leasing], ignore_index=True)
  Temp = pd.concat([old, combined_data])
  final_data = Temp[Temp.duplicated(subset = ['Tenant','Property','Renewal'],keep=False) == False]
  scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
  credentials = Credentials.from_service_account_info(
  st.secrets["GOOGLE_APPLICATION_CREDENTIALS"], 
  scopes=scope)
  gc = gspread.authorize(credentials)
  target_spreadsheet_id = 'Leasing Database'  # 目标表格的ID
  target_sheet_name = 'Sheet1'  # 目标表格的工作表名称
  target_sheet = gc.open(target_spreadsheet_id).worksheet(target_sheet_name)
  
  return set_with_dataframe(target_sheet, final_data, row=(len(old) + 2),include_column_header=False)
  
save_data()


def save_data1():
  doc = read_file('Leasing Database','Test')
  old = doc.iloc[:, :10]
  # old = old.astype(Leasing.dtypes.to_dict())
  combined_data = pd.concat([old, Leasing], ignore_index=True)
  Temp = pd.concat([old, combined_data])
  final_data = Temp[Temp.duplicated(subset = ['Tenant','Property','Renewal'],keep=False) == False]
  scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
  credentials = Credentials.from_service_account_info(
  st.secrets["GOOGLE_APPLICATION_CREDENTIALS"], 
  scopes=scope)
  gc = gspread.authorize(credentials)
  target_spreadsheet_id = 'Leasing Database'  # 目标表格的ID
  target_sheet_name = 'Test'  # 目标表格的工作表名称
  target_sheet = gc.open(target_spreadsheet_id).worksheet(target_sheet_name)
  
  return target_sheet.append_rows(final_data.values.tolist())
  
save_data1()
