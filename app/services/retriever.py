import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import concurrent.futures
import feedparser

class Retriever:
    def __init__(self):
        self.sources = {
            'gov.uk': {
                'base_url': 'https://www.gov.uk',
                'search_url': 'https://www.gov.uk/search/all?keywords={query}&order=relevance',
                'content_selector': '.gem-c-document-list__item-title, .gem-c-document-list__item-description'
            },
            'legislation.gov.uk': {
                'base_url': 'https://www.legislation.gov.uk',
                'search_url': 'https://www.legislation.gov.uk/search?text={query}',
                'content_selector': '.searchresult h3, .searchresult p'
            },
            # 'justice.gov.uk': {
            #     'base_url': 'https://www.justice.gov.uk',
            #     'search_url': 'https://www.justice.gov.uk/search?q={query}',
            #     'content_selector': 'h3.result-title, .result-summary'
            # },
            'bailii.org': {
                'base_url': 'https://www.bailii.org',
                'search_url': 'https://www.bailii.org/cgi-bin/lucy_search_1.cgi?query={query}',
                'content_selector': 'h3 a, .case-summary'
            },
            'lawsociety.org.uk': {
                'base_url': 'https://www.lawsociety.org.uk',
                'search_url': 'https://www.lawsociety.org.uk/search?q={query}',
                'content_selector': '.search-result h3, .search-result-summary'
            },
            'citizensadvice.org.uk': {
                'base_url': 'https://www.citizensadvice.org.uk',
                'search_url': 'https://www.citizensadvice.org.uk/search/?q={query}',
                'content_selector': '.search-result__title, .search-result__summary'
            }
        }
        
        # Comprehensive legislation feed URLs with descriptions
        self.legislation_feeds = {
            'all_legislation': {
                'url': 'https://www.legislation.gov.uk/new/data.feed',
                'description': 'All UK Legislation'
            },
            'uk_public_general_acts': {
                'url': 'https://www.legislation.gov.uk/new/ukpga/data.feed',
                'description': 'UK Public General Acts'
            },
            'uk_ministerial_directions': {
                'url': 'https://www.legislation.gov.uk/new/ukmd/data.feed',
                'description': 'UK Ministerial Directions'
            },
            'northern_ireland_acts': {
                'url': 'https://www.legislation.gov.uk/new/nia/data.feed',
                'description': 'Northern Ireland Acts'
            },
            'northern_ireland_orders': {
                'url': 'https://www.legislation.gov.uk/new/nisi/data.feed',
                'description': 'Northern Ireland Orders in Council'
            },
            'northern_ireland_statutory_rules': {
                'url': 'https://www.legislation.gov.uk/new/nisr/data.feed',
                'description': 'Northern Ireland Statutory Rules'
            },
            'scotland_acts': {
                'url': 'https://www.legislation.gov.uk/new/asp/data.feed',
                'description': 'Acts of the Scottish Parliament'
            },
            'scotland_statutory_instruments': {
                'url': 'https://www.legislation.gov.uk/new/ssi/data.feed',
                'description': 'Scottish Statutory Instruments'
            },
            'wales_acts': {
                'url': 'https://www.legislation.gov.uk/new/asc/data.feed',
                'description': 'Acts of Senedd Cymru'
            },
            'wales_statutory_instruments': {
                'url': 'https://www.legislation.gov.uk/new/wsi/data.feed',
                'description': 'Welsh Statutory Instruments'
            }
        }
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def _search_site(self, site_key, query):
        site_config = self.sources[site_key]
        search_url = site_config["search_url"].format(query=query)
        
        try:
            response = requests.get(search_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')
            
            results = soup.select(site_config["content_selector"])
            
            search_results = []
            for result in results[:3]:
                title = result.get_text(strip=True)
                link = result.get('href')
                if link:
                    absolute_link = urljoin(site_config["base_url"], link)
                    if title and "search" not in title.lower():
                        search_results.append({
                            "site": site_key,
                            "title": title,
                            "url": absolute_link,
                            "snippet": title
                        })

            return search_results if search_results else []

        except requests.exceptions.ConnectionError:
            print(f"Connection failed to {site_key} - network or DNS issue")
            return []
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error from {site_key}: {e}")
            return []
        except requests.exceptions.RequestException as e:
            print(f"Could not fetch information from {site_key}: {e}")
            return []

    def fetch_single_legislation_feed(self, feed_key, limit=3):
        """
        Fetch legislation from a single feed source.
        """
        feed_config = self.legislation_feeds[feed_key]
        try:
            feed = feedparser.parse(feed_config['url'])
            items = []
            for entry in feed.entries[:limit]:
                items.append({
                    "site": f"legislation.gov.uk ({feed_config['description']})",
                    "title": entry.title,
                    "url": entry.link,
                    "snippet": entry.summary if hasattr(entry, 'summary') and entry.summary else entry.title,
                    "feed_type": feed_key,
                    "description": feed_config['description']
                })
            return items
        except Exception as e:
            print(f"Failed to fetch {feed_key} feed: {e}")
            return []

    def fetch_all_legislation_feeds(self, limit_per_feed=2):
        """
        Fetch latest legislation from all feeds concurrently.
        """
        all_legislation = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.legislation_feeds)) as executor:
            future_to_feed = {
                executor.submit(self.fetch_single_legislation_feed, feed_key, limit_per_feed): feed_key
                for feed_key in self.legislation_feeds.keys()
            }
            
            for future in concurrent.futures.as_completed(future_to_feed):
                feed_key = future_to_feed[future]
                try:
                    results = future.result()
                    if results:
                        all_legislation.extend(results)
                except Exception as exc:
                    print(f'{feed_key} feed generated an exception: {exc}')
        
        return all_legislation

    def fetch_context_for_query(self, query):
        """
        Fetches context from all legal sources and legislation feeds concurrently for a given query.
        """
        print(f"Searching for '{query}' across UK legal sources and legislation feeds...")
        all_results = []

        # Search regular sources
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.sources)) as executor:
            future_to_site = {
                executor.submit(self._search_site, key, query): key
                for key in self.sources.keys()
            }

            for future in concurrent.futures.as_completed(future_to_site):
                site_key = future_to_site[future]
                try:
                    results = future.result()
                    if results:
                        all_results.extend(results)
                except Exception as exc:
                    print(f'{site_key} generated an exception: {exc}')
        
        # Always append latest legislation from all feeds
        try:
            latest_legislation = self.fetch_all_legislation_feeds(limit_per_feed=2)
            all_results.extend(latest_legislation)
            print(f"Added {len(latest_legislation)} legislation items from feeds")
        except Exception as e:
            print(f"Failed to fetch legislation feeds: {e}")

        return all_results if all_results else [{
            "site": "N/A",
            "title": "No results found",
            "url": "N/A",
            "snippet": "No results found from any specified UK source."
        }]

    def get_recent_legislation_by_type(self, legislation_type=None, limit=5):
        """
        Get recent legislation filtered by type (e.g., 'uk_public_general_acts', 'scotland_acts', etc.)
        """
        if legislation_type and legislation_type in self.legislation_feeds:
            return self.fetch_single_legislation_feed(legislation_type, limit)
        else:
            return self.fetch_all_legislation_feeds(limit_per_feed=1)

    def search_legislation_by_keyword(self, keyword, limit=10):
        """
        Search through recent legislation for specific keywords.
        """
        all_legislation = self.fetch_all_legislation_feeds(limit_per_feed=5)
        matching_legislation = []
        
        keyword_lower = keyword.lower()
        for item in all_legislation:
            if (keyword_lower in item['title'].lower() or 
                keyword_lower in item['snippet'].lower()):
                matching_legislation.append(item)
                
        return matching_legislation[:limit]