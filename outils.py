import pandas as pd
import duckdb

def load_csv(uploaded_file):
    """
    Charge un fichier CSV téléversé dans un DataFrame pandas.
    Inclut la gestion d'erreurs pour un chargement plus robuste.
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
    La base de données est en mémoire pour la simplicité de l'application web.
    """
    try:
        con = duckdb.connect(database=':memory:', read_only=False)
        # Enregistre le DataFrame pandas comme une vue temporaire DuckDB
        con.register('df_current', df) # Enregistre le DataFrame sous le nom 'df_current'
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
    KPI 1: Retourne la répartition Yes/No pour la dépression.
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

def get_gender_depression_distribution(con): # <-- Cette fonction est bien ici !
    """
    KPI 2: Retourne la répartition par genre des réponses Yes/No pour la dépression.
    """
    query = """
        SELECT "Choose your gender" as gender, UPPER("Do you have Depression?") as depression_status, COUNT(*) as nb
        FROM mental_health
        GROUP BY "Choose your gender", UPPER("Do you have Depression?")
        ORDER BY "Choose your gender", UPPER("Do you have Depression?")
    """
    df_gender_dep = con.execute(query).fetchdf()
    return df_gender_dep

def get_depression_by_course_distribution(con): # <-- Cette fonction est bien ici !
    """
    KPI 3: Retourne la répartition du nombre de dépressifs par type d'étude (cours).
    """
    query = """
        SELECT "What is your course?" as course, COUNT(*) as nb_depressed
        FROM mental_health
        WHERE UPPER("Do you have Depression?") = 'YES'
        GROUP BY "What is your course?"
        ORDER BY nb_depressed DESC
    """
    df_dep_course = con.execute(query).fetchdf()
    return df_dep_course

def get_depression_by_age_distribution(con): # <-- Cette fonction est bien ici !
    """
    KPI 4: Retourne la répartition du nombre de dépressifs par âge.
    """
    query = """
        SELECT Age as age, COUNT(*) as nb_depressed
        FROM mental_health
        WHERE UPPER("Do you have Depression?") = 'YES'
        GROUP BY Age
        ORDER BY Age ASC
    """
    df_dep_age = con.execute(query).fetchdf()
    return df_dep_age
