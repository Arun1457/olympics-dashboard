# olympics_dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt

# --------------------------
# Page Configuration
# --------------------------
st.set_page_config(
    page_title="Olympics Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🏅 Olympics Data Dashboard")
st.markdown("""
Explore historical Olympic data (1896–2016):  
- Medal tally by country  
- Athlete statistics  
- Trends over time  
""")

# --------------------------
# Load Data
# --------------------------
@st.cache_data
def load_data():
    athletes_df = pd.read_csv("athlete_events.csv")
    noc_df = pd.read_csv("noc_regions.csv")
    olympics_df = athletes_df.merge(noc_df, how="left", on="NOC")
    return olympics_df

olympics_df = load_data()
st.success("✅ Data loaded successfully!")

# --------------------------
# Sidebar Filters
# --------------------------
st.sidebar.header("Filters & Options")

years = sorted(olympics_df['Year'].unique())
countries = sorted(olympics_df['region'].dropna().unique())
sports = sorted(olympics_df['Sport'].unique())
medal_options = ['All', 'Gold', 'Silver', 'Bronze']

selected_years = st.sidebar.multiselect("Select Year(s)", years, default=[max(years), max(years)-4])
selected_countries = st.sidebar.multiselect("Select Country/Countries", countries, default=countries[:5])
selected_sports = st.sidebar.multiselect("Select Sport(s)", sports, default=sports[:5])
selected_medal = st.sidebar.radio("Select Medal Type", medal_options)

show_overall = st.sidebar.checkbox("🌍 Show Overall Analysis (Ignore Filters)")

# --------------------------
# Filter Data
# --------------------------
filtered_df = olympics_df.copy()
if not show_overall:
    filtered_df = filtered_df[
        (filtered_df['Year'].isin(selected_years)) &
        (filtered_df['region'].isin(selected_countries)) &
        (filtered_df['Sport'].isin(selected_sports))
    ]
    if selected_medal != 'All':
        filtered_df = filtered_df[filtered_df['Medal'] == selected_medal]

# --------------------------
# Display Filtered or Overall Data
# --------------------------
if show_overall:
    st.header("🌍 Overall Olympic Analysis")

    medals_df = olympics_df[olympics_df['Medal'].notna()]
    overall_tally = medals_df.groupby('region')['Medal'].value_counts().unstack(fill_value=0)
    overall_tally['Total'] = overall_tally.sum(axis=1)
    overall_tally = overall_tally.sort_values('Total', ascending=False).reset_index()

    st.subheader("🏆 Overall Medal Tally (Top 20 Countries)")
    st.dataframe(overall_tally.head(20))

    # Download CSV
    csv_overall = overall_tally.to_csv(index=False)
    st.download_button(
        label="📥 Download Overall Medal Tally as CSV",
        data=csv_overall,
        file_name='overall_medal_tally.csv',
        mime='text/csv'
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Athletes", olympics_df['ID'].nunique())
    col2.metric("Total Events", olympics_df['Event'].nunique())
    col3.metric("Total Medals", olympics_df['Medal'].notna().sum())

else:
    st.header("📊 Filtered Olympic Analysis")

    st.subheader("Filtered Data Preview")
    st.dataframe(filtered_df.head(50))

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Athletes", filtered_df['ID'].nunique())
    col2.metric("Total Events", filtered_df['Event'].nunique())
    col3.metric("Total Medals", filtered_df['Medal'].notna().sum())

# --------------------------
# Top Athletes by Country
# --------------------------
st.subheader("🏅 Top Athletes by Country")
athlete_country = st.selectbox("Select Country for Athletes", ["Overall"] + countries, index=0)
athletes_df = olympics_df if athlete_country == "Overall" else olympics_df[olympics_df['region'] == athlete_country]
top_athletes = athletes_df[athletes_df['Medal'].notna()] \
    .groupby('Name')['Medal'].count().sort_values(ascending=False).head(10).reset_index()
top_athletes.rename(columns={'Medal': 'Total Medals'}, inplace=True)
st.table(top_athletes)

# --------------------------
# Top Sports by Country
# --------------------------
st.subheader("🥇 Top Sports by Country")
sports_country = st.selectbox("Select Country for Sports", ["Overall"] + countries, index=0)
sports_df = olympics_df if sports_country == "Overall" else olympics_df[olympics_df['region'] == sports_country]
top_sports = sports_df[sports_df['Medal'].notna()] \
    .groupby('Sport')['Medal'].count().sort_values(ascending=False).head(10).reset_index()
top_sports.rename(columns={'Medal': 'Total Medals'}, inplace=True)
fig_sports = px.bar(
    top_sports,
    x='Total Medals',
    y='Sport',
    orientation='h',
    text='Total Medals',
    title=f"Top Sports - {sports_country}"
)
fig_sports.update_traces(textposition='outside')
st.plotly_chart(fig_sports, use_container_width=True)

# --------------------------
# Medals Over Time by Country
# --------------------------
st.subheader("📈 Medals Over Time by Country")
country_time = st.selectbox("Select Country for Medal Trend", countries, index=0)
country_medals = olympics_df[(olympics_df['region'] == country_time) & (olympics_df['Medal'].notna())]
medals_over_time = country_medals.groupby('Year')['Medal'].count().reset_index()
fig_time = px.line(
    medals_over_time,
    x='Year',
    y='Medal',
    markers=True,
    title=f"{country_time} Medal Count Over the Years"
)
st.plotly_chart(fig_time, use_container_width=True)

# --------------------------
# Gender Participation Over Years
# --------------------------
st.subheader("🚻 Gender Participation Over Years")
gender_trend = olympics_df.groupby(['Year', 'Sex'])['ID'].count().unstack()
fig_gender = px.line(
    gender_trend,
    x=gender_trend.index,
    y=['F', 'M'],
    labels={'value': 'Number of Athletes', 'variable': 'Gender'},
    title='Olympic Athletes Participation by Gender'
)
st.plotly_chart(fig_gender, use_container_width=True)

# --------------------------
# Sport Specialization Heatmap by Country
# --------------------------
st.subheader("🔥 Sport Specialization Heatmap by Country")
heat_country = st.selectbox("Select Country for Heatmap", countries, index=0, key="heatmap_country")
country_sports = olympics_df[(olympics_df['region'] == heat_country) & (olympics_df['Medal'].notna())]
sports_heatmap = country_sports.groupby(['Sport', 'Medal'])['ID'].count().unstack(fill_value=0)

fig, ax = plt.subplots(figsize=(10, 6))
sns.heatmap(sports_heatmap, annot=True, fmt='d', cmap='YlGnBu', ax=ax)
plt.title(f'{heat_country} - Medal Distribution Across Sports')
st.pyplot(fig)

# --------------------------
# Medal Ratio by Gender
# --------------------------
st.subheader("⚖️ Medal Ratio by Gender")
gender_country = st.selectbox("Select Country for Gender Ratio", countries, index=0, key="gender_country")
gender_medals = olympics_df[(olympics_df['region'] == gender_country) & (olympics_df['Medal'].notna())]
gender_count = gender_medals['Sex'].value_counts().reset_index()
gender_count.columns = ['Gender', 'Medals']

fig_gender_ratio = px.pie(
    gender_count,
    names='Gender',
    values='Medals',
    title=f'{gender_country} Medal Ratio by Gender'
)
st.plotly_chart(fig_gender_ratio, use_container_width=True)

# --------------------------
# Advanced Filtering & Download
# --------------------------
st.subheader("🔎 Advanced Data Filter & Download")
filter_years = st.multiselect("Select Year(s)", years, default=selected_years)
filter_countries = st.multiselect("Select Country/Countries", countries, default=selected_countries)
filter_sports = st.multiselect("Select Sport(s)", sports, default=selected_sports)

filtered_advanced_df = olympics_df[
    (olympics_df['Year'].isin(filter_years)) &
    (olympics_df['region'].isin(filter_countries)) &
    (olympics_df['Sport'].isin(filter_sports))
]

st.dataframe(filtered_advanced_df)

csv = filtered_advanced_df.to_csv(index=False)
st.download_button(
    label="📥 Download Filtered Data as CSV",
    data=csv,
    file_name='olympics_filtered_data.csv',
    mime='text/csv'
)

# --------------------------
# Summary Metrics
# --------------------------
st.subheader("📊 Summary Metrics of Filtered Data")
col1, col2, col3 = st.columns(3)
col1.metric("Total Athletes", filtered_advanced_df['ID'].nunique())
col2.metric("Total Events", filtered_advanced_df['Event'].nunique())
col3.metric("Total Medals", filtered_advanced_df['Medal'].notna().sum())

# --------------------------
# Medals by Country
# --------------------------
st.subheader("🏅 Medal Count by Country for Filtered Data")
medal_filtered = filtered_advanced_df[filtered_advanced_df['Medal'].notna()]
medal_by_country = medal_filtered.groupby('region')['Medal'].count().reset_index().sort_values('Medal', ascending=False)

fig_medal_country = px.bar(
    medal_by_country,
    x='region',
    y='Medal',
    text='Medal',
    labels={'region': 'Country', 'Medal': 'Total Medals'},
    title='Medals by Country'
)
fig_medal_country.update_traces(textposition='outside')
st.plotly_chart(fig_medal_country, use_container_width=True)
