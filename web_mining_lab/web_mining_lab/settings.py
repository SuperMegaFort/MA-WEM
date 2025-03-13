BOT_NAME = "web_mining_lab"

SPIDER_MODULES = ["web_mining_lab.spiders"]
NEWSPIDER_MODULE = "web_mining_lab.spiders"

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Active les pipelines (pour l'envoi vers Elasticsearch)
ITEM_PIPELINES = {
    'web_mining_lab.pipelines.ElasticsearchPipeline': 300,
}

# Configuration d'Elasticsearch
ELASTICSEARCH_SERVER = 'http://localhost:9200'  # L'URL de ton serveur Elasticsearch
ELASTICSEARCH_INDEX = 'wikipedia_index'  # Le nom de l'index à créer

# Pour éviter le bannissement
DOWNLOAD_DELAY = 1  # Délai d'au moins 1 seconde entre les requêtes
USER_AGENT = 'HEG-WebMining-Bot (ton_email@example.com)'  # Remplace par une adresse email VALIDE

# Limite le nombre de pages pour éviter un crawl infini (important !)
CLOSESPIDER_PAGECOUNT = 100  # Arrête après 100 pages (à ajuster)
DEPTH_LIMIT = 5  # Limite la profondeur du crawling (à ajuster)

TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"