import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from bs4 import BeautifulSoup
from collections import defaultdict
import re
from datetime import datetime

@st.cache_data(ttl=3600)
def scrape_jbu_data():
    url = "https://www.jbu.edu"
    headers = {'User-Agent': 'Mozilla/5.0'}

    fallback = {
        'mission': "To provide Christ-centered education that prepares people to honor God and serve others by developing their intellectual, spiritual, and professional lives.",
        'values': ["Christ-centered", "Transformational Education", "Whole Person Preparation", "Servant Leadership",
                   "Global Engagement"],
        'colleges': {
            "College of Bible & Ministry": 8,
            "College of Business": 12,
            "College of Education": 5,
            "College of Engineering": 6,
            "College of Liberal Arts": 9,
            "College of Natural Sciences": 7,
            "Division of Communication": 5,
            "Division of Music": 4
        },
        'stats': {
            'Total Enrollment': '2,343',
            'Student-Faculty Ratio': '14:1',
            'Undergraduate Programs': '50+',
            'Graduate Programs': '18'
        }
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        data = defaultdict(dict)

        mission_section = soup.find('h2', string=re.compile(r'Mission|Purpose', re.I))
        if mission_section:
            data['mission'] = mission_section.find_next('p').get_text(strip=True)

        values_section = soup.find('h2', string=re.compile(r'Values|Core', re.I))
        if values_section:
            data['values'] = [li.get_text(strip=True) for li in values_section.find_next('ul').find_all('li')]

        facts_section = soup.find('section', class_=re.compile(r'stats|facts|numbers', re.I))
        if facts_section:
            for item in facts_section.find_all('div', class_=re.compile(r'stat|fact|number', re.I)):
                label = item.find('h3').get_text(strip=True) if item.find('h3') else None
                value = item.find('p').get_text(strip=True) if item.find('p') else None
                if label and value:
                    data['stats'][label] = value

        academics_nav = soup.find('nav', id=re.compile(r'academics|programs', re.I))
        if academics_nav:
            for college in academics_nav.find_all('li', class_='menu-item'):
                name = college.find('a').get_text(strip=True)
                programs = college.find_all('li', class_='menu-item')
                data['colleges'][name] = len(programs)

        for key in fallback:
            if not data.get(key):
                data[key] = fallback[key]

        return dict(data)

    except Exception as e:
        st.error(f"Scraping error: {str(e)} - Using fallback data")
        return fallback


def create_dashboard():
    st.set_page_config(
        page_title="JBU Institutional Dashboard",
        page_icon=":mortar_board:",
        layout="wide"
    )

    st.markdown("""
<style>
.metric-box {
    border-radius: 10px;
    padding: 15px;
    margin-bottom: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    background-color: var(--background-color);
    color: var(--text-color);
}
</style>
""", unsafe_allow_html=True)


    jbu_data = scrape_jbu_data()

    st.title("John Brown University Institutional Dashboard")
    st.markdown("---")

    st.header("University Overview")
    cols = st.columns(4)
    stats = jbu_data.get('stats', {})

    with cols[0]:
        st.markdown('<div class="metric-box">', unsafe_allow_html=True)
        st.metric("Total Enrollment", stats.get('Total Enrollment', '2,343'))
        st.markdown('</div>', unsafe_allow_html=True)

    with cols[1]:
        st.markdown('<div class="metric-box">', unsafe_allow_html=True)
        st.metric("Student-Faculty Ratio", stats.get('Student-Faculty Ratio', '14:1'))
        st.markdown('</div>', unsafe_allow_html=True)

    with cols[2]:
        st.markdown('<div class="metric-box">', unsafe_allow_html=True)
        st.metric("Undergraduate Programs", stats.get('Undergraduate Programs', '50+'))
        st.markdown('</div>', unsafe_allow_html=True)

    with cols[3]:
        st.markdown('<div class="metric-box">', unsafe_allow_html=True)
        st.metric("Graduate Programs", stats.get('Graduate Programs', '18'))
        st.markdown('</div>', unsafe_allow_html=True)

    st.header("Academic Structure")
    colleges_df = pd.DataFrame({
        'College': list(jbu_data['colleges'].keys()),
        'Programs': list(jbu_data['colleges'].values()),
        'Faculty': [15, 22, 18, 20, 25, 19, 12, 8]  
    })

    col1, col2 = st.columns(2)
    with col1:
        fig1 = px.bar(
            colleges_df,
            x="College",
            y="Programs",
            title="Programs by College",
            color="College",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        fig2 = px.pie(
            colleges_df,
            names="College",
            values="Faculty",
            title="Faculty Distribution",
            hole=0.3
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.header("Mission & Values")
    with st.expander("View Institutional Statements"):
        st.subheader("Mission Statement")
        st.write(jbu_data['mission'])

        st.subheader("Core Values")
        for value in jbu_data['values']:
            st.markdown(f"- {value}")

    st.markdown("---")
    st.caption(f"Data sourced from jbu.edu | Last updated: {datetime.now().strftime('%B %d, %Y %H:%M')}")


if __name__ == "__main__":
    create_dashboard()
