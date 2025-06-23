import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from bs4 import BeautifulSoup
from collections import defaultdict
import re
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@st.cache_data(ttl=3600)
def scrape_jbu_data():
    url = "https://www.jbu.edu/about/facts/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

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

    used_fallback = False
    data = defaultdict(dict)

    try:
        logger.info(f"Requesting URL: {url}")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()  
        
        logger.info(f"Response status code: {response.status_code}")
        soup = BeautifulSoup(response.content, 'html.parser')
        
        mission_url = "https://www.jbu.edu/about/"
        try:
            mission_response = requests.get(mission_url, headers=headers, timeout=10)
            mission_soup = BeautifulSoup(mission_response.content, 'html.parser')
            mission_section = mission_soup.find('h2', string=lambda text: text and ('Mission' in text or 'Purpose' in text))
            if mission_section:
                mission_text = mission_section.find_next('p')
                if mission_text:
                    data['mission'] = mission_text.get_text(strip=True)
                    logger.info("Mission statement found")
            
            values_section = mission_soup.find('h2', string=lambda text: text and ('Values' in text or 'Core Values' in text))
            if values_section:
                values_list = values_section.find_next('ul')
                if values_list:
                    data['values'] = [li.get_text(strip=True) for li in values_list.find_all('li')]
                    logger.info(f"Found {len(data['values'])} values")
        except Exception as e:
            logger.warning(f"Error scraping mission/values: {str(e)}")
        
        if 'mission' not in data:
            data['mission'] = fallback['mission']
            used_fallback = True
            logger.warning("Using fallback mission statement")
        
        if 'values' not in data:
            data['values'] = fallback['values']
            used_fallback = True
            logger.warning("Using fallback values")

        stats_elements = soup.select('.stat-box, .fact-item, .number-highlight, .statistic')
        if not stats_elements:
            stats_elements = soup.select('[class*="stat"], [class*="fact"], [class*="number"]')
        
        logger.info(f"Found {len(stats_elements)} potential stat elements")
        
        if stats_elements:
            for item in stats_elements:
                label_elem = item.find(['h2', 'h3', 'h4', '.stat-title', '.fact-title'])
                value_elem = item.find(['p', '.stat-value', '.fact-value', 'span'])
                
                if label_elem and value_elem:
                    label = label_elem.get_text(strip=True)
                    value = value_elem.get_text(strip=True)
                    data['stats'][label] = value
                    logger.info(f"Found stat: {label} = {value}")
        
        if len(data['stats']) < 2:
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)
                        if label and value:
                            data['stats'][label] = value
                            logger.info(f"Found stat from table: {label} = {value}")
        
        for stat_key, stat_value in fallback['stats'].items():
            if stat_key not in data['stats']:
                data['stats'][stat_key] = stat_value
                used_fallback = True
                logger.warning(f"Using fallback for stat: {stat_key}")

        academics_url = "https://www.jbu.edu/academics/"
        try:
            academics_response = requests.get(academics_url, headers=headers, timeout=10)
            academics_soup = BeautifulSoup(academics_response.content, 'html.parser')
            
            college_sections = academics_soup.select('.college, .department, .academic-unit, [class*="college"], [class*="program"]')
            
            if college_sections:
                for section in college_sections:
                    name_elem = section.find(['h2', 'h3', 'h4', '.title'])
                    if name_elem:
                        name = name_elem.get_text(strip=True)
                        programs = section.find_all(['a', 'li'])
                        program_count = len(programs)
                        if program_count > 0:
                            data['colleges'][name] = program_count
                            logger.info(f"Found college: {name} with {program_count} programs")
            
            if not data['colleges']:
                nav_menus = academics_soup.select('nav, .menu, .navigation')
                for nav in nav_menus:
                    college_items = nav.select('li.has-children, li.has-submenu, li.dropdown')
                    for college in college_items:
                        name_elem = college.find('a')
                        if name_elem:
                            name = name_elem.get_text(strip=True)
                            # Contar submenus como programas
                            programs = college.find_all('li')
                            program_count = len(programs)
                            if program_count > 0:
                                data['colleges'][name] = program_count
                                logger.info(f"Found college from nav: {name} with {program_count} programs")
        except Exception as e:
            logger.warning(f"Error scraping academics: {str(e)}")

        if not data['colleges']:
            data['colleges'] = fallback['colleges']
            used_fallback = True
            logger.warning("Using fallback colleges data")

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        return fallback, True
    except Exception as e:
        logger.error(f"Scraping error: {str(e)}")
        return fallback, True

    logger.info(f"Scraping complete. Used fallback: {used_fallback}")
    logger.info(f"Stats found: {len(data['stats'])}")
    logger.info(f"Colleges found: {len(data['colleges'])}")

    return dict(data), used_fallback

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

    jbu_data, using_fallback = scrape_jbu_data()

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

    if using_fallback:
        st.warning("⚠️ Showing fallback data (scraping failed or partially incomplete).")
    else:
        st.success("✅ Live data successfully loaded from jbu.edu.")
    st.caption(f"Data sourced from jbu.edu | Last updated: {datetime.now().strftime('%B %d, %Y %H:%M')}")


if __name__ == "__main__":
    create_dashboard()
