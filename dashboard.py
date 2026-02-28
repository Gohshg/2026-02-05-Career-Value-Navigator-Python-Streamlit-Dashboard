import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

# Set page config
st.set_page_config(page_title="Degree ROI Calculator", layout="wide", initial_sidebar_state="expanded")

# Custom CSS
st.markdown("""
<style>
    .metric-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .header {
        font-size: 28px;
        font-weight: bold;
        color: #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

# Load data function
@st.cache_data
def load_data():
    csv_path = r"c:\Users\TUF A14\Desktop\NTU SCTP Advanced Professional Certificate Courses\01 Data Science and Artificial Intelligence (DSAI)\New folder\SGJobData.csv"
    
    # Read in chunks
    chunks = []
    for chunk in pd.read_csv(csv_path, chunksize=5000):
        chunks.append(chunk)
    
    df = pd.concat(chunks, ignore_index=True)
    
    # Clean data
    df = df.dropna(subset=['salary_minimum', 'salary_maximum', 'average_salary'])
    df['salary_minimum'] = pd.to_numeric(df['salary_minimum'], errors='coerce')
    df['salary_maximum'] = pd.to_numeric(df['salary_maximum'], errors='coerce')
    df['average_salary'] = pd.to_numeric(df['average_salary'], errors='coerce')
    df = df[(df['salary_minimum'] > 0) & (df['average_salary'] > 0)]
    
    # Parse categories
    def parse_categories(cat_str):
        try:
            if pd.isna(cat_str):
                return []
            cats = eval(cat_str)
            return [c['category'] for c in cats] if isinstance(cats, list) else []
        except:
            return []
    
    df['job_categories'] = df['categories'].apply(parse_categories)
    df['primary_category'] = df['job_categories'].apply(lambda x: x[0] if len(x) > 0 else 'Unknown')
    
    # Remove duplicates
    df = df.drop_duplicates(subset=['postedCompany_name', 'title', 'average_salary'], keep='first')
    
    # Career stage classification
    entry_level_keywords = ['entry', 'junior', 'trainee', 'graduate', 'executive']
    executive_keywords = ['executive', 'manager', 'lead', 'senior', 'head']
    
    df['career_stage'] = 'Mid-Level'
    df.loc[df['title'].str.lower().str.contains('|'.join(entry_level_keywords), na=False), 'career_stage'] = 'Entry-Level'
    df.loc[df['title'].str.lower().str.contains('|'.join(executive_keywords), na=False), 'career_stage'] = 'Senior-Level'
    
    return df

# Load data
df = load_data()

# Title and description
st.markdown('<div class="header">🎓 Degree ROI Calculator Dashboard</div>', unsafe_allow_html=True)
st.markdown("### Discover Hidden Gem Career Paths with Strong ROI and High Hiring Demand")
st.markdown("---")

# Key Metrics Row
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Job Listings", f"{len(df):,}", "Singapore Market")

with col2:
    avg_salary = df['average_salary'].mean()
    st.metric("Avg Salary", f"SGD ${avg_salary:,.0f}/mo", "All Positions")

with col3:
    entry_sal = df[df['career_stage'] == 'Entry-Level']['average_salary'].mean()
    st.metric("Entry-Level Avg", f"SGD ${entry_sal:,.0f}/mo", "Starting Salary")

with col4:
    categories = df['primary_category'].nunique()
    st.metric("Job Categories", categories, "Diverse Paths")

with col5:
    companies = df['postedCompany_name'].nunique()
    st.metric("Active Companies", f"{companies:,}", "Hiring Now")

st.markdown("---")

# Sidebar Filters
st.sidebar.markdown("### 🎯 Filter Options")

selected_categories = st.sidebar.multiselect(
    "Select Job Categories:",
    sorted(df['primary_category'].unique()),
    default=['Information Technology', 'Engineering'],
    help="Choose one or more categories to explore"
)

salary_range = st.sidebar.slider(
    "Salary Range (SGD):",
    int(df['average_salary'].min()),
    int(df['average_salary'].max()),
    (2000, 8000),
    step=500
)

career_stage_filter = st.sidebar.multiselect(
    "Career Stage:",
    ['Entry-Level', 'Mid-Level', 'Senior-Level'],
    default=['Entry-Level', 'Mid-Level']
)

min_applications = st.sidebar.slider(
    "Minimum Avg Applications (Hiring Demand):",
    0, 20, 2, step=1,
    help="Filter for roles with strong hiring demand"
)

# Apply filters
df_filtered = df[
    (df['primary_category'].isin(selected_categories)) &
    (df['average_salary'] >= salary_range[0]) &
    (df['average_salary'] <= salary_range[1]) &
    (df['career_stage'].isin(career_stage_filter)) &
    (df['metadata_totalNumberJobApplication'] >= min_applications)
]

st.sidebar.markdown(f"### Filtered Results: {len(df_filtered)} jobs")

# Main Dashboard Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "💰 ROI Rankings", "📈 Salary Analysis", "🎯 Hiring Demand", "🔍 Hidden Gems"])

# TAB 1: Overview
with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Average Salary by Career Stage")
        stage_data = df_filtered.groupby('career_stage')['average_salary'].mean().sort_values(ascending=False)
        fig1 = px.bar(
            x=stage_data.index,
            y=stage_data.values,
            labels={'x': 'Career Stage', 'y': 'Average Salary (SGD)'},
            color=stage_data.values,
            color_continuous_scale='Viridis'
        )
        fig1.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        st.subheader("Job Distribution by Category")
        cat_data = df_filtered['primary_category'].value_counts().head(10)
        fig2 = px.pie(
            values=cat_data.values,
            names=cat_data.index,
            title="Top 10 Categories"
        )
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)
    
    # Employment Type Distribution
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Employment Type Distribution")
        emp_type = df_filtered['employmentTypes'].value_counts().head(5)
        fig3 = px.bar(
            x=emp_type.index,
            y=emp_type.values,
            labels={'x': 'Employment Type', 'y': 'Count'},
            color=emp_type.values,
            color_continuous_scale='Blues'
        )
        fig3.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig3, use_container_width=True)
    
    with col2:
        st.subheader("Salary Distribution (All Positions)")
        fig4 = px.histogram(
            df_filtered,
            x='average_salary',
            nbins=30,
            labels={'average_salary': 'Average Salary (SGD)'},
            color_discrete_sequence=['#636EFA']
        )
        fig4.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig4, use_container_width=True)

# TAB 2: ROI Rankings
with tab2:
    st.subheader("💰 Top Career Paths by ROI Potential")
    
    # Group by category and calculate ROI metrics
    roi_data = df_filtered.groupby('primary_category').agg({
        'average_salary': ['mean', 'median', 'count'],
        'metadata_totalNumberJobApplication': 'mean',
        'numberOfVacancies': 'mean'
    }).reset_index()
    
    roi_data.columns = ['Category', 'Avg_Salary', 'Median_Salary', 'Job_Count', 'Avg_Applications', 'Avg_Vacancies']
    
    # Calculate ROI (assuming $2000 certification cost)
    cert_cost = 2000
    roi_data['Payback_Months'] = (cert_cost / (roi_data['Avg_Salary'] * 12) * 12).round(1)
    roi_data['Annual_Net'] = (roi_data['Avg_Salary'] * 12 - cert_cost).round(0)
    roi_data['ROI_Score'] = (roi_data['Avg_Salary'] / cert_cost * 100).round(0)
    
    roi_data = roi_data.sort_values('Avg_Salary', ascending=False)
    
    # Display as table
    st.dataframe(
        roi_data[['Category', 'Avg_Salary', 'Median_Salary', 'Job_Count', 'Avg_Applications', 'Payback_Months', 'Annual_Net']].head(20),
        use_container_width=True,
        height=400,
        hide_index=True
    )
    
    # ROI Score Visualization
    fig5 = px.bar(
        roi_data.head(15),
        x='Avg_Salary',
        y='Category',
        orientation='h',
        color='ROI_Score',
        color_continuous_scale='RdYlGn',
        title='Top 15 Career Paths by Salary (ROI Score: Higher = Better)',
        labels={'Avg_Salary': 'Average Salary (SGD)', 'Category': 'Job Category'}
    )
    fig5.update_layout(height=600)
    st.plotly_chart(fig5, use_container_width=True)

# TAB 3: Salary Analysis
with tab3:
    st.subheader("📈 Detailed Salary Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Salary by Position Level")
        position_salary = df_filtered.groupby('positionLevels')['average_salary'].agg(['mean', 'count']).reset_index()
        position_salary = position_salary[position_salary['count'] >= 3].sort_values('mean', ascending=False)
        
        fig6 = px.bar(
            position_salary.head(10),
            x='positionLevels',
            y='mean',
            title='Average Salary by Position Level',
            labels={'positionLevels': 'Position Level', 'mean': 'Average Salary (SGD)'},
            color='mean',
            color_continuous_scale='Plasma'
        )
        fig6.update_layout(height=400)
        st.plotly_chart(fig6, use_container_width=True)
    
    with col2:
        st.subheader("Entry vs Senior Level Comparison")
        comparison = df_filtered.groupby('career_stage')['average_salary'].describe().round(0)
        fig7 = px.box(
            df_filtered,
            y='average_salary',
            x='career_stage',
            color='career_stage',
            title='Salary Distribution by Career Stage',
            labels={'average_salary': 'Salary (SGD)', 'career_stage': 'Career Stage'}
        )
        fig7.update_layout(height=400)
        st.plotly_chart(fig7, use_container_width=True)
    
    # Salary percentiles
    st.subheader("Salary Percentiles")
    percentiles = df_filtered['average_salary'].quantile([0.25, 0.5, 0.75, 0.9, 0.95]).round(0)
    col_p1, col_p2, col_p3, col_p4, col_p5 = st.columns(5)
    
    with col_p1:
        st.metric("25th Percentile", f"${percentiles[0.25]:,.0f}")
    with col_p2:
        st.metric("Median (50th)", f"${percentiles[0.5]:,.0f}")
    with col_p3:
        st.metric("75th Percentile", f"${percentiles[0.75]:,.0f}")
    with col_p4:
        st.metric("90th Percentile", f"${percentiles[0.9]:,.0f}")
    with col_p5:
        st.metric("95th Percentile", f"${percentiles[0.95]:,.0f}")

# TAB 4: Hiring Demand
with tab4:
    st.subheader("🎯 Hiring Velocity & Demand Signals")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Job Applications vs Salary")
        demand_data = df_filtered.groupby('primary_category').agg({
            'metadata_totalNumberJobApplication': 'mean',
            'average_salary': 'mean',
            'title': 'count'
        }).reset_index()
        demand_data = demand_data[demand_data['title'] >= 3]
        
        fig8 = px.scatter(
            demand_data,
            x='metadata_totalNumberJobApplication',
            y='average_salary',
            size='title',
            hover_name='primary_category',
            color='average_salary',
            color_continuous_scale='Viridis',
            title='Hiring Demand vs Salary (Bubble Size = Job Listings)',
            labels={'metadata_totalNumberJobApplication': 'Avg Applications', 'average_salary': 'Avg Salary (SGD)'}
        )
        fig8.update_layout(height=500)
        st.plotly_chart(fig8, use_container_width=True)
    
    with col2:
        st.subheader("Top Hiring Categories")
        hiring_data = df_filtered.groupby('primary_category')['metadata_totalNumberJobApplication'].mean().sort_values(ascending=False).head(10)
        
        fig9 = px.bar(
            x=hiring_data.values,
            y=hiring_data.index,
            orientation='h',
            color=hiring_data.values,
            color_continuous_scale='Blues',
            title='Categories with Highest Application Volume',
            labels={'x': 'Avg Applications per Job', 'y': 'Job Category'}
        )
        fig9.update_layout(height=500)
        st.plotly_chart(fig9, use_container_width=True)
    
    # Engagement metrics
    st.subheader("Hiring Engagement Metrics")
    df_filtered['engagement_ratio'] = (df_filtered['metadata_totalNumberJobApplication'] + df_filtered['metadata_totalNumberOfView']) / (df_filtered['numberOfVacancies'] + 1)
    
    engagement = df_filtered.groupby('primary_category').agg({
        'engagement_ratio': 'mean',
        'metadata_totalNumberOfView': 'mean',
        'numberOfVacancies': 'mean'
    }).reset_index().sort_values('engagement_ratio', ascending=False).head(12)
    
    fig10 = px.bar(
        engagement,
        x='engagement_ratio',
        y='primary_category',
        orientation='h',
        color='engagement_ratio',
        color_continuous_scale='RdYlGn',
        title='Engagement Ratio (Applications + Views per Vacancy)',
        labels={'engagement_ratio': 'Engagement Ratio', 'primary_category': 'Category'}
    )
    fig10.update_layout(height=500)
    st.plotly_chart(fig10, use_container_width=True)

# TAB 5: Hidden Gems
with tab5:
    st.subheader("🔍 Hidden Gem Opportunities (Low Entry Cost, High ROI)")
    
    # Find non-prestigious roles with high salaries
    prestige_keywords = ['Senior', 'Manager', 'Lead', 'Principal', 'Director', 'Chief']
    df_filtered['is_prestigious'] = df_filtered['title'].str.contains('|'.join(prestige_keywords), case=False, na=False)
    
    gems = df_filtered[~df_filtered['is_prestigious']].copy()
    gems_by_cat = gems.groupby('primary_category').agg({
        'average_salary': ['mean', 'count'],
        'metadata_totalNumberJobApplication': 'mean',
        'numberOfVacancies': 'mean'
    }).reset_index()
    
    gems_by_cat.columns = ['Category', 'Avg_Salary', 'Job_Count', 'Avg_Applications', 'Avg_Vacancies']
    gems_by_cat = gems_by_cat[(gems_by_cat['Job_Count'] >= 3) & (gems_by_cat['Avg_Salary'] >= 2500)]
    gems_by_cat = gems_by_cat.sort_values('Avg_Salary', ascending=False)
    
    # Display gems table
    st.dataframe(
        gems_by_cat.head(15),
        use_container_width=True,
        height=400,
        hide_index=True
    )
    
    # Visualization
    fig11 = px.scatter(
        gems_by_cat.head(20),
        x='Avg_Applications',
        y='Avg_Salary',
        size='Job_Count',
        hover_name='Category',
        color='Avg_Salary',
        color_continuous_scale='Greens',
        title='Hidden Gems: High Salary + Strong Hiring Demand (Non-Prestigious Roles)',
        labels={'Avg_Applications': 'Avg Job Applications', 'Avg_Salary': 'Avg Salary (SGD)', 'Job_Count': 'Job Listings'}
    )
    fig11.update_layout(height=500)
    st.plotly_chart(fig11, use_container_width=True)
    
    # Recommendations
    st.markdown("### 💡 Why These Are Hidden Gems:")
    st.markdown("""
    - **Lower Entry Requirements**: Non-prestigious titles often mean shorter certification paths
    - **Strong Salary**: SGD $3,500+ starting salaries comparable to prestigious roles
    - **High Hiring Velocity**: Strong employer demand means faster job placement
    - **Better ROI**: Lower education cost + quick payback = maximum financial gain
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p><strong>Data Source:</strong> Singapore Job Market Data | <strong>Analysis Date:</strong> February 2026</p>
    <p><em>Discover hidden gem education paths that solve the student debt crisis with data-driven ROI insights.</em></p>
</div>
""", unsafe_allow_html=True)
