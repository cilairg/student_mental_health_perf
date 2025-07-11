import streamlit as st
import pandas as pd
import plotly.express as px
from outils import (
    load_csv, load_to_duckdb, get_total_responses,
    get_depression_distribution, get_gender_depression_distribution,
    get_depression_by_course_distribution,
    get_depression_by_age_distribution
)

st.set_page_config(page_title="Dashboard Santé Mentale", layout="wide")

st.title("📊 Dashboard santé mentale des étudiants")

uploaded_file = st.file_uploader("📂 Téléchargez votre fichier CSV", type=["csv"])

if uploaded_file:
    st.write("✅ Fichier téléversé, lecture en cours...")
    df = load_csv(uploaded_file)

    if df is None:
        st.error("Impossible de lire le fichier CSV. Veuillez vérifier son format.")
        st.stop()

    
    st.subheader("Aperçu des données")
    st.write(df.head())

    # --- Section de filtrage dynamique ---
    st.sidebar.header("🔍 Filtres")

    # Récupérer les options de filtre depuis le DataFrame original
    gender_options = df['Choose your gender'].unique().tolist()
    course_options = df['What is your course?'].unique().tolist()
    depression_options = df['Do you have Depression?'].unique().tolist()
    age_options = sorted(df['Age'].unique().tolist())
    
    # Sliders et multiselects pour les filtres
    selected_ages = st.sidebar.slider(
        "Sélectionnez une tranche d'âge",
        min_value=int(min(age_options)) if age_options else 0,
        max_value=int(max(age_options)) if age_options else 100,
        value=(int(min(age_options)), int(max(age_options))) if age_options else (0, 100)
    )
    selected_gender = st.sidebar.multiselect("Genre :", options=gender_options, default=gender_options)
    selected_course = st.sidebar.multiselect("Cours :", options=course_options, default=course_options)
    selected_depression_status = st.sidebar.multiselect("Statut de dépression :", options=depression_options, default=depression_options)


    # Application des filtres au DataFrame pandas AVANT de le charger dans DuckDB
    df_filtered = df.copy()
    df_filtered = df_filtered[
        (df_filtered['Age'] >= selected_ages[0]) & (df_filtered['Age'] <= selected_ages[1])
    ]
    if selected_gender:
        df_filtered = df_filtered[df_filtered['Choose your gender'].isin(selected_gender)]
    if selected_course:
        df_filtered = df_filtered[df_filtered['What is your course?'].isin(selected_course)]
    if selected_depression_status:
        df_filtered = df_filtered[df_filtered['Do you have Depression?'].isin(selected_depression_status)]

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

        # --- KPI 1 : Nombre total de réponses (filtré) ---
        total_responses = get_total_responses(con)
        st.metric("👥 Nombre de réponses (filtré)", total_responses)

        # --- KPI 2 : Répartition Yes/No pour la dépression (Camembert) ---
        st.subheader("📈 Répartition des réponses à 'Souffrez-vous de dépression ?'")
        df_depression = get_depression_distribution(con)
        if not df_depression.empty:
            fig1 = px.pie( # Reste un camembert
                df_depression,
                names='depression',
                values='nb',
                color='depression',
                title='Répartition des étudiants déclarant une dépression (Oui/Non)'
            )
            fig1.update_traces(textinfo='percent+label')
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("Aucune donnée pour la répartition de la dépression avec les filtres actuels.")

        # --- KPI 3 : Répartition par genre du Yes/No de dépression (Graphique à barres groupées) ---
        st.subheader("🚻 Répartition Dépression par Genre")
        df_gender_dep = get_gender_depression_distribution(con)
        if not df_gender_dep.empty:
            fig_gender_dep = px.bar( # CHANGÉ ICI : de px.pie à px.bar
                df_gender_dep,
                x='gender',
                y='nb',
                color='depression_status',
                barmode='group', # Pour afficher les barres côte à côte (Yes/No par genre)
                labels={'gender': 'Genre', 'nb': 'Nombre d\'étudiants', 'depression_status': 'Statut de Dépression'},
                title='Nombre d\'étudiants par genre et statut de dépression'
            )
            st.plotly_chart(fig_gender_dep, use_container_width=True)
        else:
            st.info("Aucune donnée disponible pour la répartition par genre des étudiants en dépression avec les filtres actuels.")


        # --- KPI 4 : Répartition du nombre de dépressifs par type d'étude (cours) ---
        st.subheader("🎓 Nombre d'étudiants dépressifs par cours")
        df_dep_course = get_depression_by_course_distribution(con)
        if not df_dep_course.empty:
            fig_dep_course = px.bar(
                df_dep_course,
                x='course',
                y='nb_depressed',
                color='course',
                labels={'course': 'Cours', 'nb_depressed': 'Nombre de dépressifs'},
                title='Nombre d\'étudiants dépressifs par cours'
            )
            st.plotly_chart(fig_dep_course, use_container_width=True)
        else:
            st.info("Aucune donnée disponible pour ce KPI avec les filtres actuels.")

        # --- KPI 5 : Répartition du nombre de dépressifs par âge ---
        st.subheader("🎂 Nombre d'étudiants dépressifs par âge")
        df_dep_age = get_depression_by_age_distribution(con)
        if not df_dep_age.empty:
            fig_dep_age = px.line( # Reste un graphique en ligne
                df_dep_age,
                x='age',
                y='nb_depressed',
                markers=True,
                labels={'age': 'Âge', 'nb_depressed': 'Nombre de dépressifs'},
                title='Nombre d\'étudiants dépressifs par âge'
            )
            st.plotly_chart(fig_dep_age, use_container_width=True)
        else:
            st.info("Aucune donnée disponible pour ce KPI avec les filtres actuels.")

    except Exception as e:
        st.error(f"Une erreur est survenue lors de l'exécution des requêtes DuckDB ou de la visualisation: {e}")
        st.exception(e)
    finally:
        con.close()
else:
    st.info("⏳ Veuillez téléverser un fichier CSV pour commencer.")
