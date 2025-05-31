import streamlit as st
import pandas as pd
import plotly.express as px


def main():
    st.set_page_config(
        page_title="JBU Institutional Dashboard",
        page_icon=":mortar_board:",
        layout="wide"
    )

    hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stAlert {display: none;}
    </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    st.title("John Brown University Institutional Dashboard")
    st.markdown("---")

    st.header("University Overview")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Enrollment", "3200", help="Total students across all programs")

    with col2:
        st.metric("Student-Faculty Ratio", "14:1", help="Ratio of students to faculty members")

    with col3:
        st.metric("Undergraduate Programs", "50+", help="Number of bachelor's degree programs")

    with col4:
        st.metric("Graduate Programs", "18", help="Number of master's degree programs")

    st.header("Academic Structure")

    colleges_data = {
        "College": [
            "Bible & Ministry", "Business", "Education", "Engineering",
            "Humanities & Social Sciences", "Natural Sciences & Math",
            "Communication & Arts", "Music & Performing Arts"
        ],
        "Programs": [8, 12, 5, 6, 9, 7, 5, 4],
        "Faculty": [15, 22, 18, 20, 25, 19, 12, 8]
    }

    df = pd.DataFrame(colleges_data)

    col1, col2 = st.columns(2)

    with col1:
        fig1 = px.bar(
            df,
            x="College",
            y="Programs",
            title="Programs by College",
            color="College",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        fig2 = px.pie(
            df,
            names="College",
            values="Faculty",
            title="Faculty Distribution",
            hole=0.3
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.header("Mission & Values")

    mission_expander = st.expander("View Full Mission Statement")
    with mission_expander:
        st.write("""
        **John Brown University Mission Statement:**

        "To provide Christ-centered education that prepares people to honor God and serve others by developing their intellectual, spiritual, and professional lives."

        **Core Values:**
        - Christ-centered
        - Transformational Education
        - Whole Person Preparation
        - Servant Leadership
        - Global Engagement
        """)

    st.markdown("---")
    st.caption("Data sourced from jbu.edu | Dashboard last updated: May 2024")


if __name__ == "__main__":
    main()
