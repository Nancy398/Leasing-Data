import streamlit as st
import pandas as pd
import plotly.express as px
from google.oauth2.service_account import Credentials
import gspread
import datetime

current_year = datetime.datetime.now().year
next_year = current_year + 1

# ------------------- 读取 Google Sheets -------------------
@st.cache_data(ttl=300)
def read_file(name, sheet):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_info(
        st.secrets["GOOGLE_APPLICATION_CREDENTIALS"], 
        scopes=scope
    )
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
    for lease_type in [('Lease From','Lease To'), ('Future Lease From','Future Lease To')]:
        if pd.notnull(row[lease_type[0]]) and pd.notnull(row[lease_type[1]]):
            records.append({
                'Property Name': row['Property Name'],
                'Property': row['Property'],
                'Unit': row['Unit'],
                'Room': row['Room'],
                'Type': row['Type'],
                'Status': row['Status'],
                'Start': row[lease_type[0]],
                'End': row[lease_type[1]],
                'Rent': row.get('Rent',''),
                'Notes': row.get('Notes','')
            })

df = pd.DataFrame(records)
df['Start'] = pd.to_datetime(df['Start'])
df['End'] = pd.to_datetime(df['End'])
df['display'] = df['Property Name'] + ' - ' + df['Unit'] + ' - ' + df['Room']

# ------------------- 左右布局 -------------------
col1, col2 = st.columns([2,1])

with col1:
    st.subheader("🏠 Vacancy Timeline")
    fig = px.timeline(
        df,
        x_start='Start',
        x_end='End',
        y='Unit',
        color='Status',
        color_discrete_map={'Out for Signing':'red','Other':'#7FB3D5'}
    )
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Room Selection")
    selected_room = st.selectbox("Select a room to edit:", df['display'])

with col2:
    st.subheader("📝 Room Details")
    if selected_room:
        room = df[df['display']==selected_room].iloc[0]
        st.text(f"Property: {room['Property']}")
        st.text(f"Unit: {room['Unit']}")
        st.text(f"Room: {room['Room']}")
        st.text(f"Type: {room['Type']}")
        
        rent = st.number_input("Rent", value=float(room.get('Rent', 0) or 0))
        notes = st.text_area("Notes", value=room.get('Notes',''))

        if st.button("Save Changes"):
            # 写回 Google Sheets
            scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
            credentials = Credentials.from_service_account_info(st.secrets["GOOGLE_APPLICATION_CREDENTIALS"], scopes=scope)
            gc = gspread.authorize(credentials)
            ws = gc.open('Vacancy').worksheet('Full Book')
            cell = ws.find(room['Unit'])
            ws.update(f"C{cell.row}:D{cell.row}", [[rent, notes]])
            st.success(f"{room['Property']} - {room['Unit']} updated!")
