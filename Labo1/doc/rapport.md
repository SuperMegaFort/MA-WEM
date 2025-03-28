# WEM : Web Mining - Laboratoire n°1 : Rapport

**Groupe:**  (Remplacez par les noms des membres de votre groupe)

**Date:** 13.03.2025

## 1. Introduction

Ce rapport décrit l'implémentation d'un crawler web, d'un système d'indexation avec Elasticsearch, et d'une fonction de recherche, dans le cadre du laboratoire n°1 du cours WEM.  Nous avons utilisé Python 3.13, Scrapy 2.12.0, BeautifulSoup 4, et le client Python officiel d'Elasticsearch 8.x.

## 2. Crawler (Scrapy)

### 2.1. Choix du Site Web

Nous avons choisi de crawler la version française de Wikipédia (`fr.wikipedia.org`). Ce choix a été motivé par :

*   **Richesse du contenu:** Wikipédia offre une grande variété d'articles sur des sujets divers.
*   **Données structurées:** Wikipédia utilise la norme Schema.org (via JSON-LD) pour fournir des métadonnées structurées, ce qui facilite l'extraction d'informations pertinentes.
*   **Fichier `robots.txt`:** Wikipédia dispose d'un fichier `robots.txt` clair, permettant de crawler le site de manière responsable.
*   **Structure HTML relativement stable:** Bien que la structure HTML de Wikipédia puisse varier, elle est globalement bien définie, ce qui facilite l'écriture de sélecteurs CSS et XPath.

### 2.2. Éléments Indexés et Extraction

Nous avons décidé d'indexer les éléments suivants pour chaque page Wikipédia :

*   **`url` (type: `keyword`):** L'URL complète de la page.
*   **`titre` (type: `text`, analyzer: `french`):** Le titre principal de l'article (balise `<h1>`).
*   **`resume` (type: `text`, analyzer: `french`):** Le premier paragraphe de l'article, servant de résumé.
*   **`contenu` (type: `text`, analyzer: `french`):** Le contenu principal de l'article, nettoyé des balises HTML et autres éléments non pertinents.
*   **`og_title` (type: `text`, analyzer: `french`):** Le titre Open Graph (pour les réseaux sociaux).
*   **`og_description` (type: `text`, analyzer: `french`):** La description Open Graph.
*   **`og_image` (type: `keyword`):** L'URL de l'image Open Graph.
*   **`structured_data` (type: `object`):**  Les données structurées (Schema.org) au format JSON-LD, avec les sous-champs suivants (entre autres) :
    *   `name` (type: `text`, analyzer: `french`)
    *   `description` (type: `text`, analyzer: `french`)
    *   `datePublished` (type: `date`, format: spécifié)
    *   `author` (type: `object`)

**Méthodes d'Extraction:**

*   **Sélecteurs CSS et XPath:** Nous avons utilisé les sélecteurs CSS et XPath de Scrapy pour cibler les éléments HTML contenant les informations souhaitées.  Par exemple, `response.css('h1#firstHeading').xpath('string(.)').get()` extrait le titre, et `response.xpath('//li[@id="mw-content-text"]/div[@class="redirectMsg"]/a/@href').get()` gère les redirections.
*   **BeautifulSoup:** Nous avons utilisé BeautifulSoup pour *nettoyer* le contenu HTML brut et pour extraire le *résumé* de manière plus fiable.  Par exemple, `soup.find('p')` trouve le premier paragraphe, et `element.decompose()` supprime les éléments indésirables (tableaux, bandeaux, etc.).  `stripped_strings` est utilisé pour obtenir un texte propre.
*   **JSON-LD:** Nous avons extrait les données structurées en recherchant les balises `<script type="application/ld+json">` et en utilisant la librairie `json` de Python pour parser le contenu JSON.
* **Gestion des redirections**: La méthode `parse_item` commence par vérifier et gèrer les redirections internes de Wikipédia, grace à `response.xpath('//li[@id="mw-content-text"]/div[@class="redirectMsg"]/a/@href').get()`.
* **Nettoyage**: Utilisation de `re.sub` pour le nettoyage du texte.

### 2.3. Code du Crawler (Extraits Pertinents)

Voir le code complet en annexe (`wikipedia_crawler.py`). Voici les parties clés:

```python
# ... (imports) ...

class WikipediaCrawler(CrawlSpider):
    name = "wikipedia_crawler"
    allowed_domains = ["fr.wikipedia.org", "www.wikipedia.org"]
    start_urls = ["[https://fr.wikipedia.org/](https://fr.wikipedia.org/)"]

    rules = (
        Rule(LinkExtractor(allow=r'/wiki/', deny=r'/wiki/(Aide|Spécial|Fichier|Discussion|Modèle|Portail|Catégorie|Utilisateur|Wikipédia):'), callback='parse_item', follow=True),
    )

    def parse_item(self, response):
        # Gestion des redirections INTERNES
        redirect_link = response.xpath('//li[@id="mw-content-text"]/div[@class="redirectMsg"]/a/@href').get()
        if redirect_link:
            redirect_url = response.urljoin(redirect_link)
            yield scrapy.Request(redirect_url, callback=self.parse_item)
            return

        # Extraction du titre
        titre = response.css('h1#firstHeading').xpath('string(.)').get()
        if titre:
            titre = titre.strip()

        # Extraction du résumé (avec BeautifulSoup)
        contenu_brut = response.xpath('//div[@class="mw-parser-output"]').get()
        if contenu_brut:
            soup = BeautifulSoup(contenu_brut, 'html.parser')
            resume_element = soup.find('p')
            if resume_element:
                for unwanted_tag in resume_element(['table', 'div']):
                    unwanted_tag.decompose()
                resume = ' '.join(resume_element.stripped_strings)
                resume = re.sub(r'\[\d+\]', '', resume).strip()
            else:
                resume = ""
        else:
            resume = ""

        # ... (extraction des autres champs) ...

        # Nettoyage du contenu (avec BeautifulSoup)
        contenu_brut = response.xpath('//div[@class="mw-parser-output"]').get()
        if contenu_brut:
            soup = BeautifulSoup(contenu_brut, 'html.parser')
            for element in soup(['table', 'div.bandeau-container', 'div.infobox_v3', 'figure', 'style', 'script', 'div.reference', 'span.mw-editsection', 'div.redirectMsg']):
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