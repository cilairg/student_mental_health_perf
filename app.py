import streamlit as st
import pandas as pd
import plotly.express as px
from outils import ( # <-- MODIFIÉ ICI : from outils au lieu de from utils
    load_csv, load_to_duckdb, get_total_responses,
    get_depression_distribution, get_gender_distribution,
    get_year_distribution, get_cgpa_by_depression,
    get_anxiety_by_course_distribution
)

st.set_page_config(page_title="Dashboard Santé Mentale", layout="wide")

st.title("📊 Dashboard santé mentale des étudiants")

uploaded_file = st.file_uploader("📂 Upload your CSV file", type=["csv"])

if uploaded_file:
    st.write("✅ Fichier uploadé, lecture en cours...")
    df = load_csv(uploaded_file)

    if df is None:
        st.error("Impossible de lire le fichier CSV. Veuillez vérifier son format.")
        st.stop()

    st.subheader("Aperçu du CSV")
    st.write(df.head())

    # --- Section de filtrage dynamique ---
    st.sidebar.header("🔍 Filtres")

    # Récupérer les valeurs uniques pour les filtres depuis le DataFrame original
    # pour s'assurer que toutes les options sont disponibles même si le df est filtré
    gender_options = df['Choose your gender'].unique().tolist()
    year_options = df['Your current year of Study'].unique().tolist()
    depression_options = df['Do you have Depression?'].unique().tolist()
    anxiety_options = df['Do you have Anxiety?'].unique().tolist()
    course_options = df['What is your course?'].unique().tolist()
    age_options = sorted(df['Age'].unique().tolist())

    selected_ages = st.sidebar.slider(
        "Sélectionnez une tranche d'âge",
        min_value=min(age_options) if age_options else 0,
        max_value=max(age_options) if age_options else 100,
        value=(min(age_options), max(age_options)) if age_options else (0, 100)
    )
    selected_gender = st.sidebar.multiselect("Genre :", options=gender_options, default=gender_options)
    selected_year = st.sidebar.multiselect("Année d'étude :", options=year_options, default=year_options)
    selected_depression = st.sidebar.multiselect("Dépression :", options=depression_options, default=depression_options)
    selected_anxiety = st.sidebar.multiselect("Anxiété :", options=anxiety_options, default=anxiety_options)
    selected_course = st.sidebar.multiselect("Cours :", options=course_options, default=course_options)


    # Application des filtres au DataFrame pandas AVANT de le charger dans DuckDB
    df_filtered = df.copy()
    df_filtered = df_filtered[
        (df_filtered['Age'] >= selected_ages[0]) & (df_filtered['Age'] <= selected_ages[1])
    ]
    if selected_gender:
        df_filtered = df_filtered[df_filtered['Choose your gender'].isin(selected_gender)]
    if selected_year:
        df_filtered = df_filtered[df_filtered['Your current year of Study'].isin(selected_year)]
    if selected_depression:
        df_filtered = df_filtered[df_filtered['Do you have Depression?'].isin(selected_depression)]
    if selected_anxiety:
        df_filtered = df_filtered[df_filtered['Do you have Anxiety?'].isin(selected_anxiety)]
    if selected_course:
        df_filtered = df_filtered[df_filtered['What is your course?'].isin(selected_course)]

    if df_filtered.empty:
        st.warning("Aucune donnée ne correspond aux filtres sélectionnés. Veuillez ajuster vos sélections.")
        st.stop()

    # DuckDB : Charger le DataFrame FILTRÉ
    con = load_to_duckdb(df_filtered)
    if con is None:
        st.error("Impossible d'initialiser DuckDB. Veuillez réessayer.")
        st.stop()

    try:
        # La table mental_health est maintenant créée à partir de df_filtered (via 'df_current' dans outils)
        con.execute("CREATE OR REPLACE TABLE mental_health AS SELECT * FROM df_current")

        # --- KPI 1 : Nombre total de réponses ---
        total_responses = get_total_responses(con)
        st.metric("👥 Nombre de réponses (filtré)", total_responses)

        # --- KPI 2 : Répartition dépression ---
        st.subheader("📈 Répartition des réponses à 'Souffrez-vous de dépression ?'")
        df_depression = get_depression_distribution(con)
        if not df_depression.empty:
            fig1 = px.bar(
                df_depression, x='depression', y='percentage',
                text=df_depression['percentage'].astype(str) + '%',
                color='depression',
                labels={'depression': 'Réponse', 'percentage': 'Pourcentage'},
                title='Répartition des étudiants déclarant une dépression'
            )
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("Aucune donnée pour la répartition de la dépression avec les filtres actuels.")


        # --- KPI 3 : Répartition par genre (parmi ceux en dépression) ---
        st.subheader("🥧 Répartition par genre parmi les étudiants en dépression")
        df_gender = get_gender_distribution(con)
        if not df_gender.empty:
            fig2 = px.pie(df_gender, names='gender', values='percentage', hover_data=['nb'], title="Répartition par genre (en %)")
            fig2.update_traces(textinfo='percent+label')
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Aucune donnée pour la répartition par genre (dépression) avec les filtres actuels.")

        # --- KPI 4 : Répartition par année d'étude ---
        st.subheader("🎓 Répartition par année d'étude")
        df_year = get_year_distribution(con)
        if not df_year.empty:
            fig3 = px.bar(df_year, x='year', y='nb', color='year',
                          labels={'year': 'Année d\'étude', 'nb': 'Nombre d\'étudiants'},
                          title='Nombre d\'étudiants par année d\'étude')
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("Aucune donnée pour la répartition par année d'étude avec les filtres actuels.")

        # --- KPI 5 : Moyenne du CGPA selon la dépression ---
        st.subheader("📚 Moyenne du CGPA selon la dépression")
        df_cgpa = get_cgpa_by_depression(con)
        if not df_cgpa.empty:
            fig4 = px.bar(df_cgpa, x='depression', y='avg_cgpa', color='depression', text=df_cgpa['avg_cgpa'].round(2),
                          labels={'depression': 'Dépression', 'avg_cgpa': 'Moyenne CGPA'},
                          title='Moyenne du CGPA selon le statut de dépression')
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("Aucune donnée pour la moyenne du CGPA avec les filtres actuels.")

        # --- KPI 6 : Répartition de l'anxiété par cours ---
        st.subheader("📊 Répartition de l'anxiété par cours")
        df_anxiety_course = get_anxiety_by_course_distribution(con)
        if not df_anxiety_course.empty:
            fig_anxiety_course = px.bar(
                df_anxiety_course,
                x='course',
                y='nb',
                color='anxiety_status',
                barmode='group',
                labels={'course': 'Cours', 'nb': 'Nombre d\'étudiants', 'anxiety_status': 'Anxiété'},
                title='Nombre d\'étudiants déclarant de l\'anxiété (Oui/Non) par cours'
            )
            st.plotly_chart(fig_anxiety_course, use_container_width=True)
        else:
            st.info("Aucune donnée disponible pour ce KPI avec les filtres actuels.")


    except Exception as e:
        st.error(f"Une erreur est survenue lors de l'exécution des requêtes DuckDB ou de la visualisation: {e}")
        st.exception(e)
    finally:
        con.close()
else:
    st.info("⏳ Veuillez téléverser un fichier CSV pour commencer.")
