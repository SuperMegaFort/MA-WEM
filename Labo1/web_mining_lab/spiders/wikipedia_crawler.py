import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
import json
import re
from bs4 import BeautifulSoup

class WikipediaCrawler(CrawlSpider):
    name = "wikipedia_crawler"
    allowed_domains = ["fr.wikipedia.org", "www.wikipedia.org"]
    start_urls = ["https://fr.wikipedia.org/"]

    rules = (
        Rule(LinkExtractor(allow=r'/wiki/', deny=r'/wiki/(Aide|Spécial|Fichier|Discussion|Modèle|Portail|Catégorie|Utilisateur|Wikipédia):'), callback='parse_item', follow=True),
    )

    def parse_item(self, response):
        # Gestion des redirections INTERNES (Wikipédia)
        # Mon code original (INCORRECT - mauvais sélecteur XPath):
        # redirect_msg = response.xpath('//div[@class="redirectMsg"]/a/@href').get()
        # Raison de l'erreur:  La structure HTML des pages de redirection de Wikipédia
        # n'utilise pas toujours une balise <div> avec la classe "redirectMsg".
        # Le sélecteur correct est plus spécifique (et robuste).

        # Code corrigé (Sélecteur XPath correct pour les redirections Wikipédia):
        redirect_link = response.xpath('//li[@id="mw-content-text"]/div[@class="redirectMsg"]/a/@href').get()
        if redirect_link:
            redirect_url = response.urljoin(redirect_link)
            yield scrapy.Request(redirect_url, callback=self.parse_item)
            return  

        # Extraction du titre, ne fonctionne pas, je ne comprends pas pourquoi 
        # on a bien sur la page wikipedia: <h1 id="firstHeading" class="firstHeading mw-first-heading"><i>Brovada</i></h1> 
        # mais le titre est vide 

        # Ton code original 
        titre = response.css('h1#firstHeading').xpath('string(.)').get()  
        # Explication: response.css('h1#firstHeading') sélectionne la balise <h1> avec l'id "firstHeading".
        # .xpath('string(.)') extrait tout le texte à l'intérieur de cette balise,
        # y compris le texte à l'intérieur des balises enfants 


        if titre:
            titre = titre.strip()  # Supprime les espaces blancs au début et à la fin / pas obligatoire

        # Extraction du résumé (ne fonctionne pas) On aimerais prendre le premier paragraphe du la page wikipedia 

        # Mes tentatives originales (INCORRECTES - problèmes de sélecteur et de gestion de None)
        '''
        #paragraphs = response.xpath('//div[@class="mw-parser-output"]/p[not(ancestor::div[@class="bandeau-container"] or ancestor::table))]//text()').getall()
        # Raison de l'erreur (1ère version):  Syntaxe XPath incorrecte pour exclure les tableaux.
        # Raison de l'erreur (2ème version): Ne gérait pas le cas où il n'y a pas de <div class="mw-parser-output">.

        paragraphs = response.xpath('//div[@class="mw-parser-output"]/p[not(ancestor::div[@class="bandeau-container"])]//text()').getall()
        resume = ' '.join(paragraphs).strip()
        resume = re.sub(r'\[\d+\]', '', resume)
        '''
        # Extraction du résumé (AVEC BEAUTIFULSOUP) - CORRIGÉ
        contenu_brut = response.xpath('//div[@class="mw-parser-output"]').get()
        # Mon erreur était ici: tu appelais BeautifulSoup *avant* de vérifier si contenu_brut était None
        # soup = BeautifulSoup(contenu_brut, 'html.parser')  # <-- ERREUR : Déplacé à l'intérieur du if

        if contenu_brut:  
            soup = BeautifulSoup(contenu_brut, 'html.parser')  
            resume_element = soup.find('p') 
            if resume_element:
                # Exclure les balises indésirables à l'intérieur du premier paragraphe
                for unwanted_tag in resume_element(['table', 'div']):
                    unwanted_tag.decompose()
                resume = ' '.join(resume_element.stripped_strings)
                resume = re.sub(r'\[\d+\]', '', resume).strip()  # Nettoyage des références [1], [2], etc.
            else:
                resume = ""  # Si pas de premier paragraphe, resume est vide
        else:  # CORRECTION : Gérer le cas où contenu_brut est None
            resume = ""  # Si pas de contenu principal, resume est vide


        # Extraction des données structurées (JSON-LD)
        scripts = response.xpath('//script[@type="application/ld+json"]/text()').getall()
        structured_data = {}
        for script in scripts:
            try:
                data = json.loads(script)
                if data.get('@type') == 'Article':  # On cible le type Article (pour Wikipédia) / sinon erreur (jsp pourquoi)
                    structured_data = data
                    break  # On prend le premier Article trouvé
            except json.JSONDecodeError:
                pass  # Gérer les erreurs de parsing JSON (ignorer ici)

        # Extraction Open Graph (OG) 
        og_title = response.xpath('//meta[@property="og:title"]/@content').get()
        og_description = response.xpath('//meta[@property="og:description"]/@content').get()
        og_image = response.xpath('//meta[@property="og:image"]/@content').get()


        # Pour nettoyager le contenu du crawler (beaucoup de balises inutiles) 
        
        contenu_brut = response.xpath('//div[@class="mw-parser-output"]').get()
        if contenu_brut:  
            soup = BeautifulSoup(contenu_brut, 'html.parser')
            for element in soup(['table', 'div.bandeau-container', 'div.infobox_v3', 'figure', 'style', 'script', 'div.reference', 'span.mw-editsection', 'div.redirectMsg']):
                element.decompose()  # Supprime l'élément et tout son contenu
            contenu = ' '.join(soup.stripped_strings) #Pour avoir un texte propre
            contenu = re.sub(r'\[\d+\]', '', contenu)  # Enlève les références [1], [2]... (Nettoyage)
            contenu = re.sub(r'\s+', ' ', contenu).strip() # Enlève les espaces multiples (Nettoyage)
        else:  
            contenu = ""  # Si pas de contenu principal, contenu est vide


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