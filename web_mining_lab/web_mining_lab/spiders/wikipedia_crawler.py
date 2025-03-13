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
        # Ton code original (INCORRECT - mauvais sélecteur XPath):
        # redirect_msg = response.xpath('//div[@class="redirectMsg"]/a/@href').get()
        # Raison de l'erreur:  La structure HTML des pages de redirection de Wikipédia
        # n'utilise pas toujours une balise <div> avec la classe "redirectMsg".
        # Le sélecteur correct est plus spécifique (et robuste).

        # Code corrigé (Sélecteur XPath correct pour les redirections Wikipédia):
        redirect_link = response.xpath('//li[@id="mw-content-text"]/div[@class="redirectMsg"]/a/@href').get()
        if redirect_link:
            redirect_url = response.urljoin(redirect_link)
            yield scrapy.Request(redirect_url, callback=self.parse_item)
            return  # Très important (ton code original avait ce return, c'est bien!)
            # Sans ce return, le code continuait à traiter la page de redirection,
            # ce qui créait des doublons.

        # Extraction du titre, ne fonctionne pas, je ne comprends pas pourquoi (Ton commentaire original)
        # on a bien sur la page wikipedia: <h1 id="firstHeading" class="firstHeading mw-first-heading"><i>Brovada</i></h1> (Ton commentaire original)
        # mais le titre est vide (Ton commentaire original)

        # Ton code original (CORRECT pour l'extraction du titre, le problème était les redirections):
        titre = response.css('h1#firstHeading').xpath('string(.)').get()  # Solution plus robuste
        # Explication: response.css('h1#firstHeading') sélectionne la balise <h1> avec l'id "firstHeading".
        # .xpath('string(.)') extrait *tout* le texte à l'intérieur de cette balise,
        # y compris le texte à l'intérieur des balises enfants (comme <i>).
        # C'est plus sûr que ::text, qui n'aurait extrait que le texte *directement* à l'intérieur du <h1>.
        if titre:
            titre = titre.strip()  # Supprime les espaces blancs au début et à la fin

        # Extraction du résumé (ne fonctionne pas) On aimerais prendre le premier paragraphe du la page wikipedia (Ton commentaire original)

        # Tes tentatives originales (INCORRECTES - problèmes de sélecteur et de gestion de None)
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
        # Ton erreur était ici: tu appelais BeautifulSoup *avant* de vérifier si contenu_brut était None
        # soup = BeautifulSoup(contenu_brut, 'html.parser')  # <-- ERREUR : Déplacé à l'intérieur du if

        if contenu_brut:  # CORRECTION : Vérifier si contenu_brut existe
            soup = BeautifulSoup(contenu_brut, 'html.parser')  # Crée l'objet soup *seulement* si contenu_brut existe
            # Récupération du premier paragraphe pour le résumé
            resume_element = soup.find('p') #On prend que le premier paragraphe
            if resume_element:
                # Exclure les balises indésirables à l'intérieur du premier paragraphe
                for unwanted_tag in resume_element(['table', 'div']):
                    unwanted_tag.decompose()
                resume = ' '.join(resume_element.stripped_strings)
                resume = re.sub(r'\[\d+\]', '', resume).strip()  # Nettoyage
            else:
                resume = ""  # Si pas de premier paragraphe, resume est vide
        else:  # CORRECTION : Gérer le cas où contenu_brut est None
            resume = ""  # Si pas de contenu principal, resume est vide


        # Extraction des données structurées (JSON-LD)  (Ton code original, correct)
        scripts = response.xpath('//script[@type="application/ld+json"]/text()').getall()
        structured_data = {}
        for script in scripts:
            try:
                data = json.loads(script)
                if data.get('@type') == 'Article':  # On cible le type Article (plus robuste)
                    structured_data = data
                    break  # On prend le premier Article (souvent le plus pertinent)
            except json.JSONDecodeError:
                pass  # Gérer les erreurs de parsing JSON (si le JSON est invalide)

        # Extraction Open Graph (OG) - reste inchangé (Ton commentaire original, et ton code était correct)
        og_title = response.xpath('//meta[@property="og:title"]/@content').get()
        og_description = response.xpath('//meta[@property="og:description"]/@content').get()
        og_image = response.xpath('//meta[@property="og:image"]/@content').get()


        # Pour nettoyager le contenu du crawler (beaucoup de balises inutiles) (Ton commentaire original)
        # Ton code original (CORRECT, mais avec la même erreur potentielle que pour le résumé, maintenant corrigée)
        contenu_brut = response.xpath('//div[@class="mw-parser-output"]').get()
        if contenu_brut:  # Tu avais déjà cette vérification, c'est bien !
            soup = BeautifulSoup(contenu_brut, 'html.parser')
            for element in soup(['table', 'div.bandeau-container', 'div.infobox_v3', 'figure', 'style', 'script', 'div.reference', 'span.mw-editsection', 'div.redirectMsg']):
                element.decompose()  # Supprime l'élément et tout son contenu
            contenu = ' '.join(soup.stripped_strings) #Pour avoir un texte propre
            contenu = re.sub(r'\[\d+\]', '', contenu)  # Enlève les références [1], [2]... (Nettoyage)
            contenu = re.sub(r'\s+', ' ', contenu).strip() # Enlève les espaces multiples (Nettoyage)
        else:  # Tu avais aussi ce else, c'est bien !
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