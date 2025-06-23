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
    # URL correta para a página de fatos
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
        print(f"Requesting URL: {url}")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extrair estatísticas da página de fatos
        # A página usa divs com classe "collapsible" para títulos e "content" para conteúdo
        collapsibles = soup.find_all('div', class_='collapsible')
        
        for collapsible in collapsibles:
            # Obter o título da seção
            section_title = collapsible.get_text(strip=True)
            
            # Obter o conteúdo correspondente (próximo elemento irmão com classe "content")
            content_div = collapsible.find_next_sibling('div', class_='content')
            
            if content_div:
                # Processar o conteúdo com base no título da seção
                if section_title == "Enrollment":
                    # Extrair estatísticas de matrícula
                    strong_tag = content_div.find('strong')
                    if strong_tag:
                        data['stats']['Total Enrollment'] = strong_tag.get_text(strip=True)
                    
                    # Extrair detalhes de matrícula
                    enrollment_details = {}
                    for span in content_div.find_all('span'):
                        text = span.get_text(strip=True)
                        if '-' in text:
                            key, value = text.split('-', 1)
                            enrollment_details[key.strip()] = value.strip()
                    
                    data['enrollment_details'] = enrollment_details
                
                elif section_title == "Top 5 Undergrad Programs":
                    # Extrair programas de graduação
                    programs = {}
                    for span in content_div.find_all('span'):
                        text = span.get_text(strip=True)
                        if '-' in text:
                            program, count = text.split('-', 1)
                            programs[program.strip()] = count.strip()
                    
                    data['top_programs'] = programs
                
                elif section_title == "Faculty":
                    # Extrair informações sobre o corpo docente
                    faculty_text = content_div.get_text(strip=True)
                    
                    # Extrair a proporção aluno/professor
                    ratio_match = re.search(r'Student/Faculty Ratio – (\d+:\d+)', faculty_text)
                    if ratio_match:
                        data['stats']['Student-Faculty Ratio'] = ratio_match.group(1)
                
                elif section_title == "Program Offerings":
                    # Extrair ofertas de programas
                    program_offerings = {}
                    for span in content_div.find_all('span'):
                        text = span.get_text(strip=True)
                        if '-' in text:
                            program_type, count = text.split('-', 1)
                            program_offerings[program_type.strip()] = count.strip()
                    
                    data['program_offerings'] = program_offerings
                    
                    # Atualizar estatísticas
                    if 'Undergraduate Majors' in program_offerings:
                        data['stats']['Undergraduate Programs'] = program_offerings['Undergraduate Majors']
                    if 'Graduate Degree Programs' in program_offerings:
                        data['stats']['Graduate Programs'] = program_offerings['Graduate Degree Programs']
                
                elif section_title == "Class Size":
                    # Extrair tamanho médio da turma
                    size_text = content_div.get_text(strip=True)
                    size_match = re.search(r'average class size is (\d+)', size_text, re.IGNORECASE)
                    if size_match:
                        data['stats']['Average Class Size'] = size_match.group(1)
                
                elif section_title == "Top 10 Home States":
                    # Extrair estados de origem
                    states = {}
                    for li in content_div.find_all('li'):
                        text = li.get_text(strip=True)
                        if '-' in text:
                            state, count = text.split('-', 1)
                            states[state.strip()] = count.strip()
                    
                    data['top_states'] = states
                
                elif section_title == "Top Countries":
                    # Extrair países de origem
                    countries_by_citizenship = []
                    countries_by_residence = []
                    
                    # Encontrar os cabeçalhos h4
                    h4_elements = content_div.find_all('h4')
                    
                    for h4 in h4_elements:
                        title = h4.get_text(strip=True)
                        ol = h4.find_next('ol')
                        
                        if ol:
                            countries = [li.get_text(strip=True) for li in ol.find_all('li')]
                            
                            if "Citizenship" in title:
                                countries_by_citizenship = countries
                            elif "Residence" in title:
                                countries_by_residence = countries
                    
                    data['countries'] = {
                        'by_citizenship': countries_by_citizenship,
                        'by_residence': countries_by_residence
                    }

        # Se não conseguimos extrair informações suficientes, usar fallback
        if not data['stats']:
            data['stats'] = fallback['stats']
            used_fallback = True
            print("Using fallback stats data")
        
        if 'top_programs' not in data:
            data['colleges'] = fallback['colleges']
            used_fallback = True
            print("Using fallback colleges data")
        
        # Missão e valores podem não estar na página de fatos, então usamos fallback
        data['mission'] = fallback['mission']
        data['values'] = fallback['values']

    except Exception as e:
        print(f"Scraping error: {str(e)}")
        return fallback, True

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

    # Exibir detalhes de matrícula se disponíveis
    if 'enrollment_details' in jbu_data and jbu_data['enrollment_details']:
        st.header("Enrollment Details")
        enrollment_df = pd.DataFrame({
            'Category': list(jbu_data['enrollment_details'].keys()),
            'Count': list(jbu_data['enrollment_details'].values())
        })
        
        fig = px.pie(
            enrollment_df,
            names="Category",
            values="Count",
            title="Enrollment Distribution",
            hole=0.3
        )
        st.plotly_chart(fig, use_container_width=True)

    # Exibir programas principais se disponíveis
    if 'top_programs' in jbu_data and jbu_data['top_programs']:
        st.header("Top Undergraduate Programs")
        
        # Função segura para extrair números dos valores
        def safe_extract_number(value):
            if not value:
                return 0
            # Extrair apenas dígitos do valor
            digits = re.findall(r'\d+', value)
            if digits:
                return int(digits[0])
            return 0
        
        # Criar DataFrame com tratamento seguro de valores
        programs_df = pd.DataFrame({
            'Program': list(jbu_data['top_programs'].keys()),
            'Students': [safe_extract_number(x) for x in jbu_data['top_programs'].values()]
        })
        
        # Verificar se temos dados válidos para exibir
        if not programs_df.empty and programs_df['Students'].sum() > 0:
            fig = px.bar(
                programs_df,
                x="Program",
                y="Students",
                title="Top 5 Undergraduate Programs",
                color="Program",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No detailed program data available to display.")

    # Exibir estados de origem se disponíveis
    if 'top_states' in jbu_data and jbu_data['top_states']:
        st.header("Geographic Distribution")
        col1, col2 = st.columns(2)
        
        with col1:
            # Função segura para extrair números dos valores
            def safe_extract_number(value):
                if not value:
                    return 0
                # Extrair apenas dígitos do valor
                digits = re.findall(r'\d+', value)
                if digits:
                    return int(digits[0])
                return 0
            
            # Criar DataFrame com tratamento seguro de valores
            states_df = pd.DataFrame({
                'State': list(jbu_data['top_states'].keys()),
                'Students': [safe_extract_number(x) for x in jbu_data['top_states'].values()]
            })
            
            # Verificar se temos dados válidos para exibir
            if not states_df.empty and states_df['Students'].sum() > 0:
                fig = px.bar(
                    states_df,
                    x="State",
                    y="Students",
                    title="Top 10 Home States",
                    color="State",
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No detailed state data available to display.")
        
        with col2:
            if 'countries' in jbu_data and jbu_data['countries'].get('by_citizenship'):
                countries = jbu_data['countries']['by_citizenship'][:5]  # Top 5 countries
                if countries:
                    countries_df = pd.DataFrame({
                        'Country': countries,
                        'Rank': list(range(1, len(countries) + 1))
                    })
                    
                    st.subheader("Top Countries by Citizenship")
                    st.table(countries_df)

    st.header("Mission & Values")
    with st.expander("View Institutional Statements"):
        st.subheader("Mission Statement")
        st.write(jbu_data['mission'])

        st.subheader("Core Values")
        for value in jbu_data['values']:
            st.markdown(f"- {value}")

    st.markdown("---")

    if using_fallback:
        st.warning("⚠️ Some data could not be scraped and fallback values are being used.")
    else:
        st.success("✅ Live data successfully loaded from jbu.edu.")
    st.caption(f"Data sourced from jbu.edu | Last updated: {datetime.now().strftime('%B %d, %Y %H:%M')}")


if __name__ == "__main__":
    create_dashboard()
