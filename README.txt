# Web Mining Lab - Crawler, Indexation et Recherche (Wikipédia)

Ce projet implémente un crawler web (avec Scrapy), un système d'indexation (avec Elasticsearch) et un moteur de recherche simple pour explorer les pages de la version suisse de Wikipédia.

## Prérequis

*   Python 3.9+
*   Docker et Docker Compose

## Installation

1.  **Cloner le dépôt :**
    ```bash
    git clone git@github.com:SuperMegaFort/MA-WEM.git  
    cd web_mining_lab   
    ```

2.  **Créer un environnement virtuel (recommandé):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # Linux/macOS
    # venv\Scripts\activate  # Windows
    ```

3.  **Installer les dépendances Python:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Lancer Elasticsearch et Kibana:**
    ```bash
    docker-compose up -d
    ```
    Cela lancera Elasticsearch et Kibana en arrière-plan. Kibana sera accessible sur `http://localhost:5601/`.

## Utilisation

### 1. Crawling (Collecte des Données)

Pour lancer le crawler et collecter les données de Wikipédia :

```bash
scrapy crawl wikipedia_crawler -s 

### 2. Search

Pour lancer la recherche des données Elasticsearch :

```bash
python search.py  # taper ensuite le mot voulu dans la console (exemple suisse)