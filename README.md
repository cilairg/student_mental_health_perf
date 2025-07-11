Tableau de bord sur la santé mentale des étudiants


Objectif: 

Ce projet de groupe vise à développer une application web interactive avec Streamlit pour analyser des données de santé mentale d'étudiants. L'application permet de téléverser un fichier CSV, de stocker et d'interroger ces données avec DuckDB, et de visualiser des indicateurs clés de performance (KPI) pertinents, avec des options de filtrage dynamique. L'accent est mis sur la clarté et la simplicité.


Fonctionnalités:

L'application offre les fonctionnalités suivantes :

Téléversement de fichier CSV.

Gestion des données avec DuckDB.

Visualisations interactives. Affichage de quatre indicateurs clés de performance (KPI) à travers des graphiques Plotly Express.

Filtres dynamiques, avec la possibilité de filtrer les données en temps réel (tranche d'âge, genre, cours suivi, statut de dépression)


Indicateurs Clés de Performance (KPIs)

Nous avons implémenté les indicateurs suivants :

Nombre total de réponses : Compte le nombre d'enregistrements dans le dataset (après application des filtres).

Répartition de la dépression : Montre la proportion d'étudiants déclarant souffrir ou non de dépression (Oui/Non) - Graphique en Camembert.

Répartition par genre du statut de dépression : Analyse la distribution du statut de dépression (Oui/Non) par genre - Graphique à Barres Groupées.

Nombre d'étudiants dépressifs par cours : Présente le nombre d'étudiants ayant déclaré une dépression, regroupés par cours suivi - Graphique à Barres.

Nombre d'étudiants dépressifs par âge : Affiche la répartition du nombre d'étudiants ayant déclaré une dépression, par tranche d'âge - Graphique en Ligne.


Installation et Exécution

Pour faire fonctionner l'application localement, suivez ces étapes :

Cloner le dépôt :

Ouvrez votre terminal (par exemple, le terminal intégré de VS Code) et naviguez vers le dossier où vous souhaitez stocker le projet (par exemple, C:\Users\VotreNom\MesProjets). Ensuite, clonez le dépôt :

A titre d'exemple, de mon coté j'ai donc:

cd "C:\Users\gayou\OneDrive\Desktop\MBA ESG\Github" # Adaptez à votre chemin parent

git clone "https://github.com/cilairg/student_mental_health_perf"

cd student_mental_health_perf

Ouvrir le projet dans VS Code :

Dans VS Code, allez dans File > Open Folder... et sélectionnez le dossier student_mental_health_perf que vous venez de cloner.

Créer et activer l'environnement virtuel :

Ouvrez le terminal intégré de VS Code (Terminal > New Terminal) et exécutez :

Pour Windows:

python -m venv .venv #création de l'environnement virtuel

.venv\Scripts\activate #pour y acceder une fois créé

Pour macOS/Linux:

python3 -m venv .venv #là on crée l'environnement

.venv/bin/activate #et ici cest pour pouvoir l'acceder et l'utiliser une fois créé

Installer les dépendances :

Avec l'environnement virtuel activé, installez les bibliothèques Python requises :

pip install streamlit pandas duckdb plotly

Lancer l'application :
Exécutez l'application Streamlit :

streamlit run app.py

L'application s'ouvrira automatiquement dans votre navigateur web.

Télécharger les données :
Le jeu de données utilisé pour ce projet peut être téléchargé depuis Kaggle :
https://www.kaggle.com/datasets/shariful07/student-mental-health?select=Student+Mental+health.csv
Téléchargez le fichier Student Mental health.csv et téléversez-le via l'interface de l'application Streamlit.

Répartition des Tâches

[SALET Marc] : Développement de l'interface utilisateur Streamlit (app.py), intégration des filtres.

[CONE-BOVIS Sarah] : Implémentation des requêtes DuckDB (outils.py), calcul des KPIs.

[KRUGER Adrien] : Création des visualisations Plotly Express, amélioration de l'esthétique.

[CILAIR P.Y. Gaétan] : Gestion du dépôt Git (branches, pull requests), rédaction de la documentation (README.md).