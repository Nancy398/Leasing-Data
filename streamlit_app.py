import streamlit as st
import pandas as pd
import plotly.express as px
from google.oauth2.service_account import Credentials
import gspread
import datetime
from gspread_dataframe import set_with_dataframe

# ------------------- 初始化 -------------------
current_year = datetime.datetime.now().year
next_year = current_year + 1

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

data = read_file('Vacancy','Full Book')

# ------------------- 数据处理 -------------------
records = []
for idx, row in data.iterrows():
    if str(row.get('Notes','')).strip().lower() == 'airbnb':
        continue
    prop = row['Property']
    prop_name = row['Property Name'] 
    prop_type = row['Type']
    prop_status = row['Status']
    # current lease
    if pd.notnull(row['Lease From']) and pd.notnull(row['Lease To']):
        records.append({
            'Property Name': prop_name,
            'Property': prop,
            'Unit': row['Unit'],
            'Room': row['Room'],
            'Type': prop_type,
            'Status': prop_status,
            'Start': row['Lease From'],
            'End': row['Lease To'],
            'Rent': row.get('Rent',''),
            'Notes': row.get('Notes','')
        })
    # future lease
    if pd.notnull(row['Future Lease From']) and pd.notnull(row['Future Lease To']):
        records.append({
            'Property Name': prop_name,
            'Property': prop,
            'Unit': row['Unit'],
            'Room': row['Room'],
            'Type': prop_type,
            'Status': prop_status,
            'Start': row['Future Lease From'],
            'End': row['Future Lease To'],
            'Rent': row.get('Rent',''),
            'Notes': row.get('Notes','')
        })

df = pd.DataFrame(records)
df['Start'] = pd.to_datetime(df['Start'])
df['End'] = pd.to_datetime(df['End'])

# ------------------- 左右布局 -------------------
col1, col2 = st.columns([2,1])

with col1:
    st.subheader("🏠 Vacancy Timeline & Room List")
    
    # 1️⃣ 按 Property Name 展示时间线
    all_property_names = sorted(df['Property Name'].unique())
    for i, property_name in enumerate(all_property_names):
        df_property = df[df['Property Name']==property_name]
        df_property['Status'] = df_property['Status'].fillna('').astype(str)
        df_property['Status'] = df_property['Status'].apply(lambda x: x if x=='Out for Signing' else 'Other')
        
        fig = px.timeline(
            df_property,
            x_start='Start',
            x_end='End',
            y='Unit',  # 按 Unit 显示
            color='Status',
            color_discrete_map={'Out for Signing':'red','Other':'#7FB3D5'}
        )
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(
            showlegend=False,
            height=40*len(df_property["Unit"].unique()) + 100
        )
        st.plotly_chart(fig, use_container_width=True,key=f"{property_name}_timeline_{i}")
    
    # 2️⃣ 房间列表 + 点击选择
    df['display'] = df['Property Name'] + ' - ' + df['Unit'] + ' - ' + df['Room']
    for idx, row in df.iterrows():
        if st.button(row['display'], key=f"btn_{idx}"):
            st.session_state['selected_idx'] = idx

with col2:
    st.subheader("📝 Room Details")
    if 'selected_idx' in st.session_state:
        idx = st.session_state['selected_idx']
        room = df.loc[idx]
        st.text(f"Property: {room['Property']}")
        st.text(f"Unit: {room['Unit']}")
        st.text(f"Room: {room['Room']}")
        st.text(f"Type: {room['Type']}")
        
        rent = st.number_input("Rent", value=float(room.get('Rent',0)))
        notes = st.text_area("Notes", value=room.get('Notes',''))
        
        if st.button("Save", key="save_btn"):
            # 写回 Google Sheets
            scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
            credentials = Credentials.from_service_account_info(st.secrets["GOOGLE_APPLICATION_CREDENTIALS"], scopes=scope)
            gc = gspread.authorize(credentials)
            ws = gc.open('Vacancy').worksheet('Full Book')
            cell = ws.find(room['Unit'])
            ws.update(f"C{cell.row}:D{cell.row}", [[rent, notes]])
            st.success(f"{room['Property']} - {room['Unit']} updated!")
