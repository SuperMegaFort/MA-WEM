import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
import json
import re
from bs4 import BeautifulSoup  # N'oublie pas d'importer BeautifulSoup


class WikipediaCrawler(CrawlSpider):
    name = "wikipedia_crawler"
    allowed_domains = ["fr.wikipedia.org", "www.wikipedia.org"]
    start_urls = ["https://fr.wikipedia.org/"]

    rules = (
        Rule(LinkExtractor(allow=r'/wiki/', deny=r'/wiki/(Aide|Spécial|Fichier|Discussion|Modèle|Portail|Catégorie|Utilisateur|Wikipédia):'), callback='parse_item', follow=True),
    )

    def parse_item(self, response):
        # Gestion des redirections INTERNES (avant l'extraction des données)
        redirect_msg = response.xpath('//div[@class="redirectMsg"]/a/@href').get()
        if redirect_msg:
            redirect_url = response.urljoin(redirect_msg)
            yield scrapy.Request(redirect_url, callback=self.parse_item)
            return  # Arrête le traitement de la page de redirection

        # Extraction du titre (avec gestion du <i>)
        titre = response.css('h1#firstHeading').xpath('string(.)').get() # Solution plus robuste
        if titre:
            titre = titre.strip()

        # Extraction du résumé (améliorée)
        paragraphs = response.xpath('//div[@class="mw-parser-output"]/p[not(ancestor::div[@class="bandeau-container"] or ancestor::table))]//text()').getall()
        resume = ' '.join(paragraphs).strip()
        resume = re.sub(r'\[\d+\]', '', resume)


        # Extraction des données structurées (JSON-LD) - reste inchangé
        scripts = response.xpath('//script[@type="application/ld+json"]/text()').getall()
        structured_data = {}
        for script in scripts:
            try:
                data = json.loads(script)
                if data.get('@type') == 'Article':
                    structured_data = data
                    break
            except json.JSONDecodeError:
                pass

        # Extraction Open Graph - reste inchangé
        og_title = response.xpath('//meta[@property="og:title"]/@content').get()
        og_description = response.xpath('//meta[@property="og:description"]/@content').get()
        og_image = response.xpath('//meta[@property="og:image"]/@content').get()


        # Nettoyage du contenu avec BeautifulSoup (FORTEMENT recommandé)
        contenu_brut = response.xpath('//div[@class="mw-parser-output"]').get()
        if contenu_brut: #Evite les erreurs
            soup = BeautifulSoup(contenu_brut, 'html.parser')
            for element in soup(['table', 'div.bandeau-container', 'div.infobox_v3', 'figure', 'style', 'script', 'div.reference', 'span.mw-editsection']):
                element.decompose()
            contenu = ' '.join(soup.stripped_strings)
            contenu = re.sub(r'\[\d+\]', '', contenu)
            contenu = re.sub(r'\s+', ' ', contenu).strip()
        else:
            contenu = ""


        item = {
            'url': response.url,
            'titre': titre,
            'resume': resume,
            'structured_data': structured_data,
            'og_title': og_title,
            'og_description': og_description,
            'og_image': og_image,
            'contenu': contenu
        }
        yield item