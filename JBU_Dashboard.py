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
    .faculty-card {
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .faculty-image {
        width: 100%;
        border-radius: 5px;
        margin-bottom: 10px;
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

    if 'top_programs' in jbu_data and jbu_data['top_programs']:
        st.header("Top Undergraduate Programs")
        
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

    if 'top_states' in jbu_data and jbu_data['top_states']:
        st.header("Geographic Distribution")
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
                countries = jbu_data['countries']['by_citizenship'][:5]  
                if countries:
                    countries_df = pd.DataFrame({
                        'Country': countries,
                        'Rank': list(range(1, len(countries) + 1))
                    })
                    
                    st.subheader("Top Countries by Citizenship")
                    st.table(countries_df)

    # Nova seção para dados de professores
   # Seção Faculty & Staff
st.header("Faculty & Staff")
    
# Obter dados de professores
faculty_data = scrape_jbu_faculty_data()
    
if faculty_data:
    # Mostrar métricas principais em cards consistentes
    faculty_metrics = st.columns(3)
    
    with faculty_metrics[0]:
        st.markdown('<div class="metric-box">', unsafe_allow_html=True)
        st.metric("Total Faculty", faculty_data['faculty_count'])
        st.markdown('</div>', unsafe_allow_html=True)
    
    with faculty_metrics[1]:
        st.markdown('<div class="metric-box">', unsafe_allow_html=True)
        st.metric("Academic Departments", len(faculty_data['departments']))
        st.markdown('</div>', unsafe_allow_html=True)
    
    with faculty_metrics[2]:
        # Calcular o departamento com mais professores
        if faculty_data['departments']:
            largest_dept = max(faculty_data['departments'].items(), key=lambda x: x[1])
            st.markdown('<div class="metric-box">', unsafe_allow_html=True)
            st.metric("Largest Department", f"{largest_dept[0]} ({largest_dept[1]})")
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Visualização da distribuição por departamento
    if faculty_data['departments']:
        st.subheader("Faculty Distribution by Department")
        
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
            
            fig = px.bar(
                dept_df,
                x='Department',
                y='Faculty Count',
                title=chart_title,
                color='Department',
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            
            # Ajustar layout para melhor legibilidade
            fig.update_layout(
                xaxis_title="",
                yaxis_title="Number of Faculty",
                xaxis={'categoryorder':'total descending'},
                margin=dict(l=20, r=20, t=40, b=20),
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # Diretório de professores pesquisável e filtrável
    st.subheader("Faculty Directory")
    
    # Criar lista de departamentos para filtro
    departments = ['All Departments'] + sorted(list(faculty_data['departments'].keys()))
    
    # Layout de 2 colunas para os filtros
    filter_cols = st.columns([2, 3])
    
    with filter_cols[0]:
        selected_dept = st.selectbox("Filter by Department:", departments)
    
    with filter_cols[1]:
        search_term = st.text_input("Search by name, title or keyword:")
    
    # Filtrar a lista de professores com base nos critérios
    filtered_faculty = faculty_data['faculty_list']
    
    # Aplicar filtro de departamento
    if selected_dept != 'All Departments':
        filtered_faculty = [
            f for f in filtered_faculty 
            if f.get('department') and selected_dept in f.get('department', '')
        ]
    
    # Aplicar filtro de pesquisa
    if search_term:
        search_term = search_term.lower()
        filtered_faculty = [
            f for f in filtered_faculty 
            if search_term in f.get('name', '').lower() or 
               (f.get('department') and search_term in f.get('department', '').lower()) or
               search_term in f.get('title', '').lower()
        ]
    
    # Mostrar os resultados em formato de tabela
    if filtered_faculty:
        # Criar tabela para visualização
        faculty_table = []
        for f in filtered_faculty:
            faculty_table.append({
                'Name': f.get('name', ''),
                'Title': f.get('title', ''),
                'Department': f.get('department', 'N/A'),
                'Profile': f.get('profile_url', '#')
            })
        
        # Converter para DataFrame e exibir
        faculty_df = pd.DataFrame(faculty_table)
        
        # Adicionar link para perfil
        def make_clickable(val):
            if val and val != '#':
                return f'<a href="{val}" >View Profile</a>'
            return ''
        
        # Aplicar formatação e exibir
        st.dataframe(
            faculty_df.style.format({
                'Profile': make_clickable
            }),
            column_config={
                "Profile": st.column_config.LinkColumn("Profile")
            },
            hide_index=True
        )
        
        # Mostrar visualização em cards para os professores em destaque
        st.subheader("Featured Faculty")
        
        # Adicionar CSS personalizado para os cards
        st.markdown("""
        <style>
        .faculty-card {
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            background-color: white;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            height: 100%;
            transition: transform 0.2s;
        }
        .faculty-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .faculty-image {
            width: 100%;
            border-radius: 5px;
            margin-bottom: 10px;
            aspect-ratio: 1;
            object-fit: cover;
        }
        .faculty-name {
            font-weight: bold;
            font-size: 1.1em;
            margin-bottom: 5px;
            color: #003366;
        }
        .faculty-title {
            font-style: italic;
            font-size: 0.9em;
            color: #555;
            margin-bottom: 8px;
        }
        .faculty-dept {
            font-size: 0.85em;
            color: #777;
        }
        .faculty-link {
            margin-top: 10px;
            display: inline-block;
            color: #0066cc;
            text-decoration: none;
            font-size: 0.9em;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Dividir em 3 colunas
        cols = st.columns(3)
        
        # Limitar a 9 professores para não sobrecarregar a página
        display_faculty = filtered_faculty[:9]
        
        for i, faculty in enumerate(display_faculty):
            with cols[i % 3]:
                profile_link = faculty.get('profile_url', '#')
                profile_link_html = f'<a href="{profile_link}"  class="faculty-link">View Full Profile</a>' if profile_link != '#' else ''
                
                department = faculty.get('department', '')
                dept_html = f'<div class="faculty-dept">{department}</div>' if department else ''
                
                st.markdown(f"""
                <div class="faculty-card">
                    <img src="{faculty.get('image_url', 'https://f.hubspotusercontent30.net/hubfs/19902035/faculty/Avatar.png')}" 
                         class="faculty-image" alt="{faculty.get('name', '')}">
                    <div class="faculty-name">{faculty.get('name', '')}</div>
                    <div class="faculty-title">{faculty.get('title', '')}</div>
                    {dept_html}
                    {profile_link_html}
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No faculty members found matching your search criteria.")
else:
    st.warning("⚠️ Faculty data could not be loaded. Please try again later.")
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
