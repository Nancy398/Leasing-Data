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
    st.title("Property Occupancy Information")
    
    all_property_names = sorted(df['Property Name'].unique())

    select_all_props = st.checkbox("Select All Property Names", value=True)
  
    if select_all_props:
        selected_properties = all_property_names
    else:
        selected_properties = st.multiselect("Select Property Name(s)", all_property_names, default=[], label_visibility="collapsed")
    
    df_filtered = df[df["Property Name"].isin(selected_properties)]
   
    for i,property_name in enumerate(selected_properties):
        with st.expander(f"Property: {property_name}"):
            # 在每个 Property Name 的面板内设置 Extend to Show Next Year 的选项
            show_next_year = st.checkbox(f"Extend to Show Next Year for {property_name}", value=False)
    
            # 筛选 Unit 和 Room
            units_for_property = df[df['Property Name'] == property_name]['Unit'].unique()
            rooms_for_property = df[df['Property Name'] == property_name]['Room'].unique()
    
            selected_units = st.multiselect(
            "Select Units",
            options=units_for_property,
            default=units_for_property,
            key=f"{property_name}_units"
        )
    
            selected_rooms = st.multiselect(
              "Select Rooms",
            options=rooms_for_property,
            default=rooms_for_property,
            key=f"{property_name}_rooms"
        )
    
            # 根据选择的 Unit 和 Room 筛选数据
            df_property = df[(df['Property Name'] == property_name) & 
                             (df['Unit'].isin(selected_units)) & 
                             (df['Room'].isin(selected_rooms))]
            df_property['Status'] = df_property['Status'].fillna('').astype(str)
            df_property['Status'] = df_property['Status'].apply(lambda x: x if x == 'Out for Signing' else 'Other') 
            # 根据选项，动态设置 X 轴的时间范围
            if show_next_year:
                x_range = [f"{current_year}-01-01", f"{next_year}-12-31"]  # 显示今年 + 明年
            else:
                x_range = [f"{current_year}-01-01", f"{current_year}-12-31"]  # 只显示今年

            # 根据筛选后的数据来展示图表
            fig = px.timeline(
                df_property,  # 使用该 Property Name 的数据
                x_start="Start",
                x_end="End",
                y="Property",
                color = 'Status',
                color_discrete_map={
                            'Out for signing': 'red',
                            'Other':'#7FB3D5'
                        }
            )
    
            # 设置日期格式和轴
            fig.update_layout(
                showlegend=False,
                title=None,
                margin=dict(l=20, r=20, t=20, b=20),
                height=40 * len(df_property["Property"].unique()) + 100,
                xaxis=dict(
                    tickformat="%Y-%m-%d",  # 日期格式：年-月-日
                    tickangle=45,
                    ticks="outside",
                    showgrid=True,
                    side="top",  # 将日期放在上方
                    range=x_range,  # 动态设置 X 轴的日期范围
                    title="Date"  # 设置 X 轴标题
                )
            )
    
            # 显示图表
            st.plotly_chart(fig, use_container_width=True,key=f"{prop}_occupancy_chart_{i}")


with col2:
    st.subheader("Room Selection")
    selected_room = st.selectbox("Select a room to edit:", df['display'])
    
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
            cell = ws.find(room['Property'])
            ws.update(f"M{cell.row}:N{cell.row}", [[rent, notes]])
            st.success(f"{room['Property']} - {room['Unit']} updated!")
