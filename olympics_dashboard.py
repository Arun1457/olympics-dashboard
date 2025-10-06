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
st.header("🔎 Filters & Data Selection")
st.sidebar.header("Filters")

# Multi-select filters for broader default
years = sorted(olympics_df['Year'].unique())
selected_years = st.sidebar.multiselect("Select Year(s)", years, default=[max(years), max(years)-4])

countries = sorted(olympics_df['region'].dropna().unique())
selected_countries = st.sidebar.multiselect("Select Country/Countries", countries, default=countries[:5])

sports = sorted(olympics_df['Sport'].unique())
selected_sports = st.sidebar.multiselect("Select Sport(s)", sports, default=sports[:5])

medal_options = ['All', 'Gold', 'Silver', 'Bronze']
selected_medal = st.sidebar.radio("Select Medal Type", medal_options)

# --------------------------
# Filter Data Based on Selections
# --------------------------
filtered_df = olympics_df[
    (olympics_df['Year'].isin(selected_years)) &
    (olympics_df['region'].isin(selected_countries)) &
    (olympics_df['Sport'].isin(selected_sports))
]

if selected_medal != 'All':
    filtered_df = filtered_df[filtered_df['Medal'] == selected_medal]

st.subheader("Filtered Data")
st.dataframe(filtered_df)

# --------------------------
# Key Metrics
# --------------------------
st.header("📊 Key Metrics")
col1, col2, col3 = st.columns(3)
col1.metric("Total Athletes", filtered_df['ID'].nunique())
col2.metric("Total Events", filtered_df['Event'].nunique())
col3.metric("Total Medals", filtered_df['Medal'].notna().sum())

# --------------------------
# Prepare medal data
# --------------------------
medals_df = olympics_df[olympics_df['Medal'].notna()]

# --------------------------
# Top 10 Countries by Total Medals
# --------------------------
st.header("🏆 Top 10 Countries by Total Medals")
medal_tally = medals_df.groupby('region')['Medal'].value_counts().unstack(fill_value=0)
medal_tally['Total'] = medal_tally.sum(axis=1)
medal_tally = medal_tally.sort_values('Total', ascending=False)
top10_countries = medal_tally.head(10).reset_index()

fig = px.bar(
    top10_countries,
    x='region',
    y='Total',
    text='Total',
    labels={'region': 'Country', 'Total': 'Total Medals'},
    title='Top 10 Countries by Total Olympic Medals',
    color='Total',
    color_continuous_scale='Viridis'
)
fig.update_traces(textposition='outside')
fig.update_layout(xaxis_tickangle=-45)
st.plotly_chart(fig, use_container_width=True)

# --------------------------
# Top 10 Athletes
# --------------------------
st.subheader("🏅 Top 10 Athletes by Total Olympic Medals")
top_athletes = medals_df.groupby('Name')['Medal'].count().sort_values(ascending=False).head(10).reset_index()
top_athletes.rename(columns={'Medal': 'Total Medals'}, inplace=True)
st.table(top_athletes)

# --------------------------
# Top 10 Sports
# --------------------------
st.subheader("🥇 Top 10 Sports by Total Medals")
top_sports = medals_df.groupby('Sport')['Medal'].count().sort_values(ascending=False).head(10).reset_index()
top_sports.rename(columns={'Medal': 'Total Medals'}, inplace=True)
fig_sports = px.bar(
    top_sports,
    x='Total Medals',
    y='Sport',
    text='Total Medals',
    orientation='h',
    title='Top 10 Sports by Olympic Medals',
    color='Total Medals',
    color_continuous_scale='Magma'
)
fig_sports.update_traces(textposition='outside')
st.plotly_chart(fig_sports, use_container_width=True)

# --------------------------
# Gender Participation Trends
# --------------------------
st.subheader("🚻 Gender Participation Over Years")
gender_trend = olympics_df.groupby(['Year', 'Sex'])['ID'].count().unstack()
fig_gender = px.line(
    gender_trend,
    x=gender_trend.index,
    y=['F', 'M'],
    labels={'value': 'Number of Athletes', 'Year': 'Olympic Year', 'variable': 'Gender'},
    title='Olympic Athletes Participation by Gender Over the Years'
)
st.plotly_chart(fig_gender, use_container_width=True)

# --------------------------
# Age Distribution
# --------------------------
st.subheader("🎯 Age Distribution of Medalists")
fig_age = px.histogram(
    medals_df.dropna(subset=['Age']),
    x='Age',
    nbins=30,
    title='Age Distribution of Olympic Medalists',
    color_discrete_sequence=['skyblue']
)
st.plotly_chart(fig_age, use_container_width=True)

# --------------------------
# Medals Over Time by Country
# --------------------------
st.subheader("📈 Medals Over Time by Country")
selected_country_time = st.selectbox("Select Country for Trend Analysis", countries, index=0)
country_medals = medals_df[medals_df['region'] == selected_country_time]
medals_over_time = country_medals.groupby('Year')['Medal'].count().reset_index()
fig_country_time = px.line(
    medals_over_time,
    x='Year',
    y='Medal',
    title=f'{selected_country_time} Medal Count Over the Years',
    markers=True
)
st.plotly_chart(fig_country_time, use_container_width=True)

# --------------------------
# Sport Specialization Heatmap
# --------------------------
st.subheader("🔥 Sport Specialization Heatmap by Country")
selected_country_heat = st.selectbox("Select Country for Sport Specialization", countries, index=0, key="heatmap_country")
country_sports = medals_df[medals_df['region'] == selected_country_heat]
sports_heatmap = country_sports.groupby(['Sport', 'Medal'])['ID'].count().unstack(fill_value=0)

fig, ax = plt.subplots(figsize=(10, 6))
sns.heatmap(sports_heatmap, annot=True, fmt='d', cmap='YlGnBu', ax=ax)
plt.title(f'{selected_country_heat} - Medal Distribution Across Sports')
st.pyplot(fig)

# --------------------------
# Medal Ratio by Gender
# --------------------------
st.subheader("⚖️ Medal Ratio by Gender")
selected_country_gender = st.selectbox("Select Country for Gender Ratio", countries, index=0, key="gender_country")
gender_medals = medals_df[medals_df['region'] == selected_country_gender]
gender_count = gender_medals['Sex'].value_counts().reset_index()
gender_count.columns = ['Gender', 'Medals']

fig_gender_ratio = px.pie(
    gender_count,
    names='Gender',
    values='Medals',
    title=f'{selected_country_gender} Medal Ratio by Gender'
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
