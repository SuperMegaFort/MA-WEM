# pipelines.py (Pas de changement majeur par rapport à l'exemple précédent)
from elasticsearch import Elasticsearch
from itemadapter import ItemAdapter

class ElasticsearchPipeline:

    def __init__(self, elastic_server, elastic_index):
        self.elastic_server = elastic_server
        self.elastic_index = elastic_index
        self.es = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            elastic_server=crawler.settings.get('ELASTICSEARCH_SERVER'),
            elastic_index=crawler.settings.get('ELASTICSEARCH_INDEX', 'wikipedia_index'),  # Valeur par défaut
        )

    def open_spider(self, spider):
        self.es = Elasticsearch(self.elastic_server)
        if not self.es.indices.exists(index=self.elastic_index):
            self.es.indices.create(
                index=self.elastic_index,
                body={
                    "mappings": {
                        "properties": {
                            "url": {"type": "keyword"},
                            "titre": {"type": "text", "analyzer": "french"},
                            "resume": {"type": "text", "analyzer": "french"},
                            "contenu": {"type": "text", "analyzer": "french"},
                             "og_title": {"type": "text", "analyzer": "french"},
                            "og_description": {"type": "text", "analyzer": "french"},
                            "og_image":{"type": "keyword"},
                            "structured_data": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "text", "analyzer": "french"},
                                    "description": {"type": "text", "analyzer": "french"},
                                    "datePublished": {"type": "date"},
                                    "author": {
                                        "type": "object",  # Type object pour author
                                        "properties":{
                                            "name": {"type": "text", "analyzer": "french"},
                                            "url": {"type":"keyword"}
                                        }
                                    },
                                    "image": {"type": "keyword"},
                                    # ... autres champs Schema.org ...
                                },
                            },
                        }
                    }
                },
            )

    def close_spider(self, spider):
        if self.es:
            self.es.close()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        self.es.index(index=self.elastic_index, document=adapter.asdict())
        return item