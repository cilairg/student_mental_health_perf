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

    # --- Vérification et conversion de la colonne CGPA (si elle existe et est nécessaire) ---
    # Cette section est commentée car le CGPA n'est plus un KPI direct.
    # Si vous ajoutez un KPI qui utilise CGPA, vous devrez la réactiver et l'adapter.
    # if "What is your CGPA?" in df.columns:
    #     def convert_cgpa_range_to_midpoint(cgpa_range_str):
    #         if pd.isna(cgpa_range_str):
    #             return None
    #         try:
    #             s_cgpa_range_str = str(cgpa_range_str)
    #             if ' - ' in s_cgpa_range_str:
    #                 parts = s_cgpa_range_str.split(' - ')
    #             elif '-' in s_cgpa_range_str:
    #                 parts = s_cgpa_range_str.split('-')
    #             else:
    #                 return float(s_cgpa_range_str)
    #             if len(parts) == 2:
    #                 lower = float(parts[0].strip())
    #                 upper = float(parts[1].strip())
    #                 return (lower + upper) / 2
    #             else:
    #                 return float(s_cgpa_range_str)
    #         except ValueError:
    #             return None
    #         except Exception as e:
    #             print(f"Erreur inattendue lors de la conversion de CGPA '{cgpa_range_str}': {e}")
    #             return None
    #     
    #     df["What is your CGPA?"] = df["What is your CGPA?"].apply(convert_cgpa_range_to_midpoint)
    #     df.dropna(subset=["What is your CGPA?"], inplace=True)
    #     if df.empty:
    #         st.warning("Aucune donnée valide après la conversion du CGPA. Veuillez vérifier le format de la colonne ou les filtres.")
    #         st.stop()
    # else:
    #     st.warning("La colonne 'What is your CGPA?' est introuvable. Certains KPIs pourraient être affectés.")
    # --- Fin de la section CGPA ---


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

        # --- KPI 2 : Répartition Yes/No pour la dépression ---
        st.subheader("📈 Répartition des réponses à 'Souffrez-vous de dépression ?'")
        df_depression = get_depression_distribution(con)
        if not df_depression.empty:
            fig1 = px.pie( # C'était déjà un camembert ici, comme demandé précédemment
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

        # --- KPI 3 : Répartition par genre du Yes/No de dépression ---
        st.subheader("🚻 Répartition Dépression par Genre")
        df_gender_dep = get_gender_depression_distribution(con)
        if not df_gender_dep.empty:
            # Pour un camembert, nous devons calculer les pourcentages par genre et statut de dépression
            # et choisir une seule colonne pour les 'names' et une pour les 'values'.
            # Pour un camembert par genre, il faut d'abord agréger les données
            # pour obtenir le total de chaque genre.
            # Cependant, le KPI 3 est "Répartition par genre du Yes/No de dépression",
            # ce qui suggère de voir la proportion de Yes/No au sein de chaque genre, ou la proportion de chaque genre
            # parmi les dépressifs/non-dépressifs. Un graphique à barres groupées est souvent plus clair ici.
            # Si vous voulez un camembert pour chaque genre (un camembert pour les hommes, un pour les femmes),
            # ce serait plus complexe et nécessiterait des sous-graphiques ou des filtres supplémentaires.
            #
            # Pour un camembert simple sur la répartition des genres parmi les dépressifs (ce qui était un KPI précédent),
            # il faudrait filtrer df_gender_dep pour 'YES' et ensuite faire le camembert.
            #
            # Pour ce KPI spécifique ("Répartition par genre du Yes/No de dépression"),
            # un camembert n'est pas idéal car il y a deux dimensions (genre ET statut de dépression).
            # Un bar chart groupé est plus approprié pour montrer les deux dimensions.
            #
            # Si l'intention est de montrer la *proportion de chaque genre* parmi les dépressifs,
            # alors il faut une agrégation spécifique :
            df_depressed_gender = df_gender_dep[df_gender_dep['depression_status'].str.upper() == 'YES'].copy()
            if not df_depressed_gender.empty and df_depressed_gender['nb'].sum() > 0:
                total_depressed_gender = df_depressed_gender['nb'].sum()
                df_depressed_gender['percentage'] = (df_depressed_gender['nb'] / total_depressed_gender * 100).round(1)

                fig_gender_pie = px.pie( # CHANGÉ ICI : de px.bar à px.pie
                    df_depressed_gender,
                    names='gender',
                    values='percentage',
                    color='gender',
                    title='Répartition par genre des étudiants déclarant une dépression'
                )
                fig_gender_pie.update_traces(textinfo='percent+label')
                st.plotly_chart(fig_gender_pie, use_container_width=True)
            else:
                st.info("Aucune donnée disponible pour la répartition par genre des étudiants en dépression avec les filtres actuels.")
        else:
            st.info("Aucune donnée disponible pour ce KPI avec les filtres actuels.")


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
            fig_dep_age = px.line( # Utilisation d'un graphique en ligne pour la répartition par âge
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
