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
        
        collapsibles = soup.find_all('div', class_='collapsible')
        
        for collapsible in collapsibles:
            section_title = collapsible.get_text(strip=True)
            
            content_div = collapsible.find_next_sibling('div', class_='content')
            
            if content_div:
                if section_title == "Enrollment":
                    strong_tag = content_div.find('strong')
                    if strong_tag:
                        data['stats']['Total Enrollment'] = strong_tag.get_text(strip=True)
                    
                    enrollment_details = {}
                    for span in content_div.find_all('span'):
                        text = span.get_text(strip=True)
                        if '-' in text:
                            key, value = text.split('-', 1)
                            enrollment_details[key.strip()] = value.strip()
                    
                    data['enrollment_details'] = enrollment_details
                
                elif section_title == "Top 5 Undergrad Programs":
                    programs = {}
                    for span in content_div.find_all('span'):
                        text = span.get_text(strip=True)
                        if '-' in text:
                            program, count = text.split('-', 1)
                            programs[program.strip()] = count.strip()
                    
                    data['top_programs'] = programs
                
                elif section_title == "Faculty":
                    faculty_text = content_div.get_text(strip=True)
                    
                    ratio_match = re.search(r'Student/Faculty Ratio – (\d+:\d+)', faculty_text)
                    if ratio_match:
                        data['stats']['Student-Faculty Ratio'] = ratio_match.group(1)
                
                elif section_title == "Program Offerings":
                    program_offerings = {}
                    for span in content_div.find_all('span'):
                        text = span.get_text(strip=True)
                        if '-' in text:
                            program_type, count = text.split('-', 1)
                            program_offerings[program_type.strip()] = count.strip()
                    
                    data['program_offerings'] = program_offerings
                    
                    if 'Undergraduate Majors' in program_offerings:
                        data['stats']['Undergraduate Programs'] = program_offerings['Undergraduate Majors']
                    if 'Graduate Degree Programs' in program_offerings:
                        data['stats']['Graduate Programs'] = program_offerings['Graduate Degree Programs']
                
                elif section_title == "Class Size":
                    size_text = content_div.get_text(strip=True)
                    size_match = re.search(r'average class size is (\d+)', size_text, re.IGNORECASE)
                    if size_match:
                        data['stats']['Average Class Size'] = size_match.group(1)
                
                elif section_title == "Top 10 Home States":
                    states = {}
                    for li in content_div.find_all('li'):
                        text = li.get_text(strip=True)
                        if '-' in text:
                            state, count = text.split('-', 1)
                            states[state.strip()] = count.strip()
                    
                    data['top_states'] = states
                
                elif section_title == "Top Countries":
                    countries_by_citizenship = []
                    countries_by_residence = []
                    
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

        if not data['stats']:
            data['stats'] = fallback['stats']
            used_fallback = True
            print("Using fallback stats data")
        
        if 'top_programs' not in data:
            data['colleges'] = fallback['colleges']
            used_fallback = True
            print("Using fallback colleges data")
        
        data['mission'] = fallback['mission']
        data['values'] = fallback['values']

    except Exception as e:
        print(f"Scraping error: {str(e)}")
        return fallback, True

    return dict(data), used_fallback

@st.cache_data(ttl=3600)
def scrape_jbu_faculty_data():
    url = "https://www.jbu.edu/faculty/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    faculty_data = {
        'faculty_count': 0,
        'departments': {},
        'faculty_list': []
    }
    
    try:
        print(f"Requesting faculty URL: {url}")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        faculty_links = soup.find_all('a', class_='jbu-faculty-profile-link')
        
        faculty_data['faculty_count'] = len(faculty_links)
        departments = {}
        faculty_list = []
        
        for faculty_link in faculty_links:
            faculty_info = {}
            
            name_elem = faculty_link.find('h3', class_='jbu-font-size-24')
            if name_elem:
                faculty_info['name'] = name_elem.get_text(strip=True)
            
            title_elem = faculty_link.find('div', class_='jbu-faculty-profile-title')
            if title_elem:
                title = title_elem.get_text(strip=True)
                faculty_info['title'] = title
                
                department = None
                if "Professor of" in title:
                    dept_match = re.search(r'Professor of\s+([^;]+)', title)
                    if dept_match:
                        department = dept_match.group(1).strip()
                elif "Department Chair" in title:
                    dept_match = re.search(r'Department Chair,\s+([^;]+)', title)
                    if dept_match:
                        department = dept_match.group(1).strip()
                
                if department:
                    faculty_info['department'] = department
                    
                    if department in departments:
                        departments[department] += 1
                    else:
                        departments[department] = 1
            
            profile_url = faculty_link.get('href')
            if profile_url:
                faculty_info['profile_url'] = profile_url
            
            img_elem = faculty_link.find('img')
            if img_elem:
                img_src = img_elem.get('data-src')
                if img_src:
                    faculty_info['image_url'] = img_src
            
            if faculty_info:
                faculty_list.append(faculty_info)
        
        faculty_data['departments'] = departments
        faculty_data['faculty_list'] = faculty_list
        
    except Exception as e:
        print(f"Faculty scraping error: {str(e)}")
        return None
    
    return faculty_data


def create_dashboard():
    st.set_page_config(
        page_title="JBU Institutional Dashboard",
        page_icon=":mortar_board:",
        layout="wide"
    )

    # Aplicando estilo global para texto azul
    st.markdown("""
    <style>
    /* Aplicando cor azul a todos os elementos de texto */
    body {
        color: #003366 !important;
    }
    
    /* Estilo específico para cabeçalhos */
    .css-10trblm {
        color: #003366 !important;
    }
    
    /* Estilo para métricas */
    .css-1wivap2 {
        color: #003366 !important;
    }
    
    /* Estilo para texto normal */
    p, div, span, label, .css-1d8n9bt {
        color: #003366 !important;
    }
    
    /* Estilo para tabelas */
    .dataframe th, .dataframe td {
        color: #003366 !important;
    }
    
    /* Estilo para expandir/colapsar */
    .css-1fcdlhc {
        color: #003366 !important;
    }
    
    /* Estilo para links */
    a:not(.css-1cpxqw2) {
        color: #0066cc !important;
    }
    
    /* Estilo para botões */
    .css-1cpxqw2 {
        background-color: #003366 !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Título com cor azul explícita
    st.markdown('<h1 style="color: #003366;">John Brown University Institutional Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("---")

    # Cabeçalho com cor azul explícita
    st.markdown('<h2 style="color: #003366;">University Overview</h2>', unsafe_allow_html=True)
    
    cols = st.columns(4)
    stats = jbu_data.get('stats', {})

    # Métricas com rótulos coloridos manualmente
    with cols[0]:
        st.markdown('<div style="color: #003366; font-weight: bold;">Total Enrollment</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="color: #003366; font-size: 2.5rem; font-weight: bold;">{stats.get("Total Enrollment", "2,343")}</div>', unsafe_allow_html=True)

    with cols[1]:
        st.markdown('<div style="color: #003366; font-weight: bold;">Student-Faculty Ratio</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="color: #003366; font-size: 2.5rem; font-weight: bold;">{stats.get("Student-Faculty Ratio", "14:1")}</div>', unsafe_allow_html=True)

    with cols[2]:
        st.markdown('<div style="color: #003366; font-weight: bold;">Undergraduate Programs</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="color: #003366; font-size: 2.5rem; font-weight: bold;">{stats.get("Undergraduate Programs", "50+")}</div>', unsafe_allow_html=True)

    with cols[3]:
        st.markdown('<div style="color: #003366; font-weight: bold;">Graduate Programs</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="color: #003366; font-size: 2.5rem; font-weight: bold;">{stats.get("Graduate Programs", "18")}</div>', unsafe_allow_html=True)

    if 'enrollment_details' in jbu_data and jbu_data['enrollment_details']:
        st.markdown('<h2 style="color: #003366;">Enrollment Details</h2>', unsafe_allow_html=True)
        enrollment_df = pd.DataFrame({
            'Category': list(jbu_data['enrollment_details'].keys()),
            'Count': list(jbu_data['enrollment_details'].values())
        })
        
        # Cores mais escuras e vibrantes para o gráfico de pizza
        dark_blues = ['#001f3f', '#003366', '#004080', '#0059b3', '#0066cc', '#0074D9']
        
        fig = px.pie(
            enrollment_df,
            names="Category",
            values="Count",
            title="Enrollment Distribution",
            hole=0.3,
            color_discrete_sequence=dark_blues  # Usando tons de azul mais escuros
        )
        # Definindo cor do título do gráfico e adicionando bordas
        fig.update_layout(
            title_font=dict(color="#003366"),
            font=dict(color="#003366")
        )
        # Adicionando bordas e contorno para melhor visualização
        fig.update_traces(
            marker=dict(line=dict(color='#FFFFFF', width=2)),
            textfont_color='white'
        )
        st.plotly_chart(fig, use_container_width=True)

    # Seção Faculty & Staff
    st.markdown('<h2 style="color: #003366;">Faculty & Staff</h2>', unsafe_allow_html=True)
    
    # Obter dados de professores
    faculty_data = scrape_jbu_faculty_data()
    
    if faculty_data:
        # Mostrar métricas principais em cards consistentes
        faculty_metrics = st.columns(3)
        
        with faculty_metrics[0]:
            st.markdown('<div style="color: #003366; font-weight: bold;">Total Faculty</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="color: #003366; font-size: 2.5rem; font-weight: bold;">{faculty_data["faculty_count"]}</div>', unsafe_allow_html=True)
        
        with faculty_metrics[1]:
            st.markdown('<div style="color: #003366; font-weight: bold;">Academic Departments</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="color: #003366; font-size: 2.5rem; font-weight: bold;">{len(faculty_data["departments"])}</div>', unsafe_allow_html=True)
        
        with faculty_metrics[2]:
            # Calcular o departamento com mais professores
            if faculty_data['departments']:
                largest_dept = max(faculty_data['departments'].items(), key=lambda x: x[1])
                st.markdown('<div style="color: #003366; font-weight: bold;">Largest Department</div>', unsafe_allow_html=True)
                st.markdown(f'<div style="color: #003366; font-size: 2.5rem; font-weight: bold;">{largest_dept[0]} ({largest_dept[1]})</div>', unsafe_allow_html=True)
        
        # Visualização da distribuição por departamento
        if faculty_data['departments']:
            st.markdown('<h3 style="color: #003366;">Faculty Distribution by Department</h3>', unsafe_allow_html=True)
            
            # Filtrar departamentos com pelo menos 2 professores para melhor visualização
            filtered_departments = {k: v for k, v in faculty_data['departments'].items() if v >= 2}
            
            if filtered_departments:
                dept_df = pd.DataFrame({
                    'Department': list(filtered_departments.keys()),
                    'Faculty Count': list(filtered_departments.values())
                })
                
                # Ordenar por contagem (do maior para o menor)
                dept_df = dept_df.sort_values('Faculty Count', ascending=False)
                
                # Limitar a 10 departamentos para melhor visualização
                if len(dept_df) > 10:
                    dept_df = dept_df.head(10)
                    chart_title = "Top 10 Departments by Faculty Count"
                else:
                    chart_title = "Faculty Distribution by Department"
                
                # Cores mais escuras para o gráfico de barras
                dept_colors = ['#001f3f', '#003366', '#004080', '#0059b3', '#0066cc', '#0074D9', 
                              '#0080ff', '#3399ff', '#4da6ff', '#66b3ff']
                
                fig = px.bar(
                    dept_df,
                    x='Department',
                    y='Faculty Count',
                    title=chart_title,
                    color='Department',
                    color_discrete_sequence=dept_colors  # Usando tons de azul mais escuros
                )
                
                # Ajustar layout para melhor legibilidade e cor azul
                fig.update_layout(
                    xaxis_title="",
                    yaxis_title="Number of Faculty",
                    xaxis={'categoryorder':'total descending'},
                    margin=dict(l=20, r=20, t=40, b=20),
                    title_font=dict(color="#003366"),
                    font=dict(color="#003366"),
                    plot_bgcolor='rgba(240,240,240,0.5)'  # Fundo cinza claro para melhor contraste
                )
                
                # Adicionar bordas às barras para melhor visualização
                fig.update_traces(
                    marker_line_color='white',
                    marker_line_width=1.5,
                    opacity=1.0  # Opacidade total para cores mais vivas
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        # Adicionar link para a página completa de Faculty & Staff
        st.markdown("""
        <div style="margin-top: 20px; padding: 15px; background-color: #f8f9fa; border-radius: 10px; text-align: center;">
            <p style="margin-bottom: 10px; color: #003366; font-weight: bold;">If you want to see all the faculty staff, click on the link below:</p>
            <a href="https://www.jbu.edu/faculty/" style="display: inline-block; padding: 8px 16px; background-color: #003366; color: white !important; text-decoration: none; border-radius: 5px; font-weight: bold;">Visit JBU Faculty Page</a>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ Faculty data could not be loaded. Please try again later.")
        
        # Mesmo assim, fornecer o link para a página oficial
        st.markdown("""
        <div style="margin-top: 20px; padding: 15px; background-color: #f8f9fa; border-radius: 10px; text-align: center;">
            <p style="margin-bottom: 10px; color: #003366; font-weight: bold;">Visit the official JBU faculty page for complete information:</p>
            <a href="https://www.jbu.edu/faculty/" style="display: inline-block; padding: 8px 16px; background-color: #003366; color: white !important; text-decoration: none; border-radius: 5px; font-weight: bold;">Visit JBU Faculty Page</a>
        </div>
        """, unsafe_allow_html=True)

    if 'top_programs' in jbu_data and jbu_data['top_programs']:
        st.markdown('<h2 style="color: #003366;">Top Undergraduate Programs</h2>', unsafe_allow_html=True)
        
        def safe_extract_number(value):
            if not value:
                return 0
            digits = re.findall(r'\d+', value)
            if digits:
                return int(digits[0])
            return 0
        
        programs_df = pd.DataFrame({
            'Program': list(jbu_data['top_programs'].keys()),
            'Students': [safe_extract_number(x) for x in jbu_data['top_programs'].values()]
        })
        
        if not programs_df.empty and programs_df['Students'].sum() > 0:
            # Cores mais escuras e vibrantes para o gráfico de barras
            program_colors = ['#001f3f', '#003366', '#004080', '#0059b3', '#0066cc']
            
            fig = px.bar(
                programs_df,
                x="Program",
                y="Students",
                title="Top 5 Undergraduate Programs",
                color="Program",
                color_discrete_sequence=program_colors  # Usando tons de azul mais escuros
            )
            # Definindo cor do título e texto do gráfico
            fig.update_layout(
                title_font=dict(color="#003366"),
                font=dict(color="#003366"),
                plot_bgcolor='rgba(240,240,240,0.5)'  # Fundo cinza claro para melhor contraste
            )
            
            # Adicionar bordas às barras para melhor visualização
            fig.update_traces(
                marker_line_color='white',
                marker_line_width=1.5,
                opacity=1.0  # Opacidade total para cores mais vivas
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.markdown('<div style="color: #003366;">No detailed program data available to display.</div>', unsafe_allow_html=True)

    if 'top_states' in jbu_data and jbu_data['top_states']:
        st.markdown('<h2 style="color: #003366;">Geographic Distribution</h2>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            def safe_extract_number(value):
                if not value:
                    return 0
                digits = re.findall(r'\d+', value)
                if digits:
                    return int(digits[0])
                return 0
            
            states_df = pd.DataFrame({
                'State': list(jbu_data['top_states'].keys()),
                'Students': [safe_extract_number(x) for x in jbu_data['top_states'].values()]
            })
            
            if not states_df.empty and states_df['Students'].sum() > 0:
                # Cores mais escuras para o gráfico de barras
                state_colors = ['#001f3f', '#00264d', '#003366', '#004080', '#004d99', 
                               '#0059b3', '#0066cc', '#0074D9', '#0080ff', '#1a8cff']
                
                fig = px.bar(
                    states_df,
                    x="State",
                    y="Students",
                    title="Top 10 Home States",
                    color="State",
                    color_discrete_sequence=state_colors  # Usando tons de azul mais escuros
                )
                # Definindo cor do título e texto do gráfico
                fig.update_layout(
                    title_font=dict(color="#003366"),
                    font=dict(color="#003366"),
                    plot_bgcolor='rgba(240,240,240,0.5)'  # Fundo cinza claro para melhor contraste
                )
                
                # Adicionar bordas às barras para melhor visualização
                fig.update_traces(
                    marker_line_color='white',
                    marker_line_width=1.5,
                    opacity=1.0  # Opacidade total para cores mais vivas
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.markdown('<div style="color: #003366;">No detailed state data available to display.</div>', unsafe_allow_html=True)
        
        with col2:
            if 'countries' in jbu_data and jbu_data['countries'].get('by_citizenship'):
                countries = jbu_data['countries']['by_citizenship'][:5]  
                if countries:
                    countries_df = pd.DataFrame({
                        'Country': countries,
                        'Rank': list(range(1, len(countries) + 1))
                    })
                    
                    st.markdown('<h3 style="color: #003366;">Top Countries by Citizenship</h3>', unsafe_allow_html=True)
                    # Aplicando estilo à tabela para texto azul
                    st.markdown(
                        countries_df.style.set_properties(**{'color': '#003366'})
                        .to_html(), unsafe_allow_html=True
                    )

    st.markdown('<h2 style="color: #003366;">Mission & Values</h2>', unsafe_allow_html=True)
    with st.expander("View Institutional Statements"):
        st.markdown('<h3 style="color: #003366;">Mission Statement</h3>', unsafe_allow_html=True)
        st.markdown(f'<p style="color: #003366;">{jbu_data["mission"]}</p>', unsafe_allow_html=True)

        st.markdown('<h3 style="color: #003366;">Core Values</h3>', unsafe_allow_html=True)
        for value in jbu_data['values']:
            st.markdown(f'<li style="color: #003366;">{value}</li>', unsafe_allow_html=True)

    st.markdown("---")

    if using_fallback:
        st.warning("⚠️ Some data could not be scraped and fallback values are being used.")
    else:
        st.success("✅ Live data successfully loaded from jbu.edu.")
    st.markdown(f'<p style="color: #003366; font-size: 0.8rem;">Data sourced from jbu.edu | Last updated: {datetime.now().strftime("%B %d, %Y %H:%M")}</p>', unsafe_allow_html=True)


if __name__ == "__main__":
    jbu_data, using_fallback = scrape_jbu_data()
    create_dashboard()
