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
ELASTICSEARCH_SERVER = 'http://localhost:9200'  # L'URL pour accéder à Elasticsearch
ELASTICSEARCH_INDEX = 'wikipedia_index'  # Nom de l'index Elasticsearch

# Pour éviter le bannissement
DOWNLOAD_DELAY = 1  # Délai d'au moins 1 seconde entre les requêtes
#USER_AGENT = 'HEG-WebMining-Bot (ton_email@example.com)'  Ps obligatoire

# Limite le nombre de pages pour éviter un crawl infini 
CLOSESPIDER_PAGECOUNT = 100  
DEPTH_LIMIT = 5  

TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"