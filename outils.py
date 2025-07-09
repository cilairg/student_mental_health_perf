import pandas as pd
import duckdb

def load_csv(uploaded_file):
    """
    Charge un fichier CSV téléversé dans un DataFrame pandas.
    """
    try:
        df = pd.read_csv(uploaded_file)
        return df
    except Exception as e:
        print(f"Erreur lors du chargement du CSV: {e}")
        return None

def load_to_duckdb(df):
    """
    Établit une connexion DuckDB en mémoire et enregistre le DataFrame.
    """
    try:
        con = duckdb.connect(database=':memory:', read_only=False)
        # Enregistre le DataFrame pandas comme une vue DuckDB
        con.register('df_current', df) # Renommé pour éviter la confusion avec le df original
        return con
    except Exception as e:
        print(f"Erreur lors de la connexion à DuckDB ou de l'enregistrement du DataFrame: {e}")
        return None

def get_total_responses(con):
    """
    Retourne le nombre total de réponses dans le dataset.
    """
    result = con.execute("SELECT COUNT(*) as nb_lignes FROM mental_health").fetchdf()
    return result.loc[0, 'nb_lignes']

def get_depression_distribution(con):
    """
    Retourne la répartition Yes/No pour la dépression.
    """
    query = """
        SELECT UPPER("Do you have Depression?") as depression, COUNT(*) as nb
        FROM mental_health
        GROUP BY UPPER("Do you have Depression?")
    """
    df_depression = con.execute(query).fetchdf()
    if not df_depression.empty and df_depression['nb'].sum() > 0:
        total = df_depression['nb'].sum()
        df_depression['percentage'] = (df_depression['nb'] / total * 100).round(1)
    return df_depression

def get_gender_distribution(con):
    """
    Retourne la répartition par genre parmi ceux en dépression.
    """
    query = """
        SELECT "Choose your gender" as gender, COUNT(*) as nb
        FROM mental_health
        WHERE UPPER("Do you have Depression?") = 'YES'
        GROUP BY "Choose your gender"
    """
    df_gender = con.execute(query).fetchdf()
    if not df_gender.empty and df_gender['nb'].sum() > 0:
        total = df_gender['nb'].sum()
        df_gender['percentage'] = (df_gender['nb'] / total * 100).round(1)
    return df_gender

def get_year_distribution(con):
    """
    Retourne la répartition par année d'étude.
    """
    query = """
        SELECT "Your current year of Study" as year, COUNT(*) as nb
        FROM mental_health
        GROUP BY "Your current year of Study"
        ORDER BY "Your current year of Study"
    """
    df_year = con.execute(query).fetchdf()
    return df_year

def get_cgpa_by_depression(con):
    """
    Retourne la moyenne du CGPA selon la dépression.
    """
    query = """
        SELECT UPPER("Do you have Depression?") as depression, AVG("CGPA") as avg_cgpa
        FROM mental_health
        GROUP BY UPPER("Do you have Depression?")
    """
    df_cgpa = con.execute(query).fetchdf()
    return df_cgpa

def get_anxiety_by_course_distribution(con):
    """
    Retourne la répartition de l'anxiété par cours.
    """
    query = """
        SELECT "What is your course?" as course, UPPER("Do you have Anxiety?") as anxiety_status, COUNT(*) as nb
        FROM mental_health
        GROUP BY "What is your course?", UPPER("Do you have Anxiety?")
        ORDER BY "What is your course?", UPPER("Do you have Anxiety?")
    """
    df_anxiety_course = con.execute(query).fetchdf()
    return df_anxiety_course
