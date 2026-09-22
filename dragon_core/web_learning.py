"""
DRAGON AI CORE
Web Learning and Automatic Web Search
"""
 
import base64
import html
import re
import urllib.parse
import xml.etree.ElementTree as ET
 
import requests
 
SEARCH_ENGINE_URL = "[https://www.bing.com/search](https://www.bing.com/search)"
 
REQUEST_TIMEOUT = 15
 
MAX_RESULTS = 5
 
MAX_CONTENT_LENGTH = 12000
 
class WebLearning:
def init(self):
self.session = requests.Session()
 
self.session.headers.update(
{
"User-Agent": (
"Mozilla/5.0 "
"(Windows NT 10.0; Win64; x64) "
"AppleWebKit/537.36 "
"(KHTML, like Gecko) "
"Chrome/131.0 Safari/537.36"
),
"Accept": (
"text/html,application/xhtml+xml,"
"application/xml;q=0.9,*/*;q=0.8"
),
"Accept-Language": (
"en-US,en;q=0.9,ar;q=0.8"
),
}
)
 
def _prepare_search_query(self, query: str) -> str:
query = str(query or "").strip()
 
```
if not query:    
    return ""    

query = re.sub(    
    r"[؟?!،؛,:]+",    
    " ",    
    query    
)    

stop_phrases = [    
    "ما هو",    
    "ما هي",    
    "من هو",    
    "من هي",    
    "اخبرني عن",    
    "أخبرني عن",    
    "هل يمكنك أن تخبرني عن",    
    "هل يمكنك ان تخبرني عن",    
    "tell me about",    
    "what is",    
    "what are",    
    "who is",    
    "who are",    
    "what's",    
    "whats",    
]    

cleaned = query    

for phrase in stop_phrases:    
    cleaned = re.sub(    
        re.escape(phrase),    
        " ",    
        cleaned,    
        flags=re.IGNORECASE,    
    )    

cleaned = re.sub(    
    r"\s+",    
    " ",    
    cleaned    
).strip()    

if not cleaned:    
    return query    

return cleaned    
```
 
def _build_retry_query(self, query: str) -> str:
"""
Build a second search query only when the first
search appears unrelated to the original question.
"""
 
```
query = self._prepare_search_query(query)    

if not query:    
    return ""    

# Remove common Arabic search filler words.    
words = query.split()    

ignored_words = {    
    "في",    
    "من",    
    "عن",    
    "على",    
    "الى",    
    "إلى",    
    "ما",    
    "هي",    
    "هو",    
    "هل",    
    "هذا",    
    "هذه",    
    "ذلك",    
    "تلك",    
    "مع",    
    "خلال",    
    "حول",    
    "عام",    
    "سنة",    
    "ماهي",    
    "ماهو",    
    "آخر",    
    "احدث",    
    "أحدث",    
}    

important_words = [    
    word    
    for word in words    
    if word.lower() not in ignored_words    
    and len(word) > 2    
]    

if not important_words:    
    return query    

core_query = " ".join(    
    important_words    
)    

# Add a neutral freshness term rather than    
# imposing a strict relevance threshold.    
retry_query = (    
    f"{core_query} latest 2026"    
)    

return retry_query.strip()    
```
 
def _normalize_text(self, text: str) -> str:
if not text:
return ""
 
```
text = html.unescape(    
    str(text)    
).lower()    

replacements = {    
    "أ": "ا",    
    "إ": "ا",    
    "آ": "ا",    
    "ة": "ه",    
    "ى": "ي",    
}    

for old, new in replacements.items():    
    text = text.replace(    
        old,    
        new    
    )    

text = re.sub(    
    r"[^a-z0-9\u0600-\u06ff]+",    
    " ",    
    text    
)    

text = re.sub(    
    r"\s+",    
    " ",    
    text    
).strip()    

return text    
```
 
def _get_query_terms(
self,
query: str
):
normalized = self._normalize_text(
query
)
 
```
ignored_words = {    
    "ما",    
    "ماذا",    
    "ماهي",    
    "ماهو",    
    "من",    
    "في",    
    "عن",    
    "على",    
    "الى",    
    "إلى",    
    "منذ",    
    "خلال",    
    "حول",    
    "مع",    
    "هل",    
    "هو",    
    "هي",    
    "هذا",    
    "هذه",    
    "ذلك",    
    "تلك",    
    "عام",    
    "سنه",    
    "سنة",    
    "احدث",    
    "أحدث",    
    "latest",    
    "what",    
    "what's",    
    "whats",    
    "who",    
    "tell",    
    "about",    
    "the",    
    "and",    
    "for",    
    "from",    
    "with",    
}    

terms = []    

for word in normalized.split():    
    if len(word) <= 2:    
        continue    

    if word in ignored_words:    
        continue    

    if word not in terms:    
        terms.append(word)    

return terms    
```
 
def _result_is_related(
self,
query: str,
result: dict
) -> bool:
"""
This is deliberately permissive.
 
```
Its purpose is only to detect obviously unrelated    
results such as a Kyoto travel page for an AI question.    

It does NOT reject individual results based on a    
strict numerical relevance score.    
"""    

query_terms = self._get_query_terms(    
    query    
)    

if not query_terms:    
    return True    

searchable_text = " ".join(    
    [    
        result.get("title", ""),    
        result.get("snippet", ""),    
        result.get("content", "")[:3000],    
    ]    
)    

normalized_result = self._normalize_text(    
    searchable_text    
)    

if not normalized_result:    
    return False    

matches = 0    

for term in query_terms:    
    if term in normalized_result:    
        matches += 1    

# For a question with only one important term,    
# one match is enough.    
if len(query_terms) == 1:    
    return matches >= 1    

# For normal questions, at least one meaningful    
# query term is enough to consider the result    
# potentially related.    
#    
# The purpose is only to detect clearly unrelated    
# pages, not to perform strict ranking.    
return matches >= 1    
```
 
def _filter_obviously_unrelated_results(
self,
query: str,
results
):
if not results:
return []
 
```
related = []    

for result in results:    
    if self._result_is_related(    
        query,    
        result    
    ):    
        related.append(result)    

return related    
```
 
def _normalize_search_url(self, url: str) -> str:
if not url:
return ""
 
```
url = html.unescape(url)    
url = urllib.parse.unquote(url)    

parsed = urllib.parse.urlparse(url)    

if "bing.com" in parsed.netloc.lower():    
    query = urllib.parse.parse_qs(    
        parsed.query    
    )    

    for key in ("u", "url", "r"):    
        values = query.get(key)    

        if values:    
            candidate = values[0]    

            if candidate.startswith("http"):    
                return candidate    

            decoded = self._decode_bing_url(    
                candidate    
            )    

            if decoded:    
                return decoded    

return url    
```
 
def _decode_bing_url(self, value: str) -> str:
if not value:
return ""
 
```
value = urllib.parse.unquote(    
    value    
)    

if value.startswith("http"):    
    return value    

if value.startswith("a1"):    
    encoded = value[2:]    

    try:    
        padding = "=" * (    
            (-len(encoded)) % 4    
        )    

        decoded = base64.urlsafe_b64decode(    
            encoded + padding    
        ).decode(    
            "utf-8",    
            errors="ignore"    
        )    

        match = re.search(    
            r"https?://[^\s\"<>]+",    
            decoded    
        )    

        if match:    
            return match.group(0)    

    except Exception:    
        pass    

return ""    
```
 
def _valid_url(self, url: str) -> bool:
if not url:
return False
 
```
try:    
    parsed = urllib.parse.urlparse(    
        url    
    )    

    return (    
        parsed.scheme in (    
            "http",    
            "https",    
        )    
        and bool(parsed.netloc)    
    )    

except Exception:    
    return False    
```
 
def _clean_text(self, text: str) -> str:
if not text:
return ""
 
```
text = html.unescape(    
    text    
)    

text = re.sub(    
    r"<[^>]+>",    
    " ",    
    text    
)    

text = re.sub(    
    r"\s+",    
    " ",    
    text    
).strip()    

return text    
```
 
def _parse_bing_rss(
self,
xml_text: str
):
results = []
 
```
if not xml_text:    
    return results    

try:    
    root = ET.fromstring(    
        xml_text    
    )    

except ET.ParseError:    
    return results    

for item in root.findall(    
    ".//item"    
):    
    title_element = item.find(    
        "title"    
    )    

    link_element = item.find(    
        "link"    
    )    

    description_element = item.find(    
        "description"    
    )    

    title = (    
        title_element.text    
        if title_element is not None    
        else ""    
    )    

    url = (    
        link_element.text    
        if link_element is not None    
        else ""    
    )    

    snippet = (    
        description_element.text    
        if description_element is not None    
        else ""    
    )    

    title = self._clean_text(    
        title    
    )    

    url = self._normalize_search_url(    
        url    
    )    

    snippet = self._clean_text(    
        snippet    
    )    

    if not title or not url:    
        continue    

    if not self._valid_url(url):    
        continue    

    results.append(    
        {    
            "title": title,    
            "url": url,    
            "snippet": snippet,    
        }    
    )    

    if len(results) >= MAX_RESULTS:    
        break    

return results    
```
 
def _extract_html_content(
self,
text: str
) -> str:
 
```
if not text:    
    return ""    

text = re.sub(    
    r"<script\b[^>]*>.*?</script>",    
    " ",    
    text,    
    flags=re.IGNORECASE | re.DOTALL,    
)    

text = re.sub(    
    r"<style\b[^>]*>.*?</style>",    
    " ",    
    text,    
    flags=re.IGNORECASE | re.DOTALL,    
)    

text = re.sub(    
    r"<noscript\b[^>]*>.*?</noscript>",    
    " ",    
    text,    
    flags=re.IGNORECASE | re.DOTALL,    
)    

text = re.sub(    
    r"<[^>]+>",    
    " ",    
    text    
)    

text = html.unescape(    
    text    
)    

text = re.sub(    
    r"\s+",    
    " ",    
    text    
).strip()    

if len(text) > MAX_CONTENT_LENGTH:    
    text = text[    
        :MAX_CONTENT_LENGTH    
    ]    

return text    
```
 
def _fetch_page(
self,
url: str
) -> str:
 
```
try:    
    response = self.session.get(    
        url,    
        timeout=REQUEST_TIMEOUT,    
        allow_redirects=True,    
    )    

    response.raise_for_status()    

    content_type = (    
        response.headers.get(    
            "Content-Type",    
            ""    
        ).lower()    
    )    

    if (    
        "text/html" not in content_type    
        and "text/plain" not in content_type    
        and "application/xhtml+xml"    
        not in content_type    
    ):    
        return ""    

    return self._extract_html_content(    
        response.text    
    )    

except requests.RequestException:    
    return ""    

except Exception:    
    return ""    
```
 
def _perform_search(
self,
search_query: str
):
"""
Execute one Bing RSS search.
"""
 
```
if not search_query:    
    return []    

response = self.session.get(    
    SEARCH_ENGINE_URL,    
    params={    
        "q": search_query,    
        "format": "rss",    
    },    
    headers={    
        "Accept": (    
            "application/rss+xml,"    
            "application/xml,"    
            "text/xml,"    
            "*/*;q=0.8"    
        ),    
        "Accept-Language": (    
            "en-US,en;q=0.9,ar;q=0.8"    
        ),    
    },    
    timeout=REQUEST_TIMEOUT,    
    allow_redirects=True,    
)    

response.raise_for_status()    

return self._parse_bing_rss(    
    response.text    
)    
```
 
def _complete_results(
self,
results
):
"""
Fetch page content while preserving the
original search result structure.
"""
 
```
final_results = []    

for result in results:    

    title = result.get(    
        "title",    
        ""    
    )    

    url = result.get(    
        "url",    
        ""    
    )    

    snippet = result.get(    
        "snippet",    
        ""    
    )    

    content = ""    

    if self._valid_url(url):    
        content = self._fetch_page(    
            url    
        )    

    final_results.append(    
        {    
            "title": title,    
            "url": url,    
            "snippet": snippet,    
            "content": content,    
        }    
    )    

return final_results    
```
 
def search_web(
self,
query: str
):
 
```
search_query = (    
    self._prepare_search_query(    
        query    
    )    
)    

if not search_query:    
    return {    
        "status": "error",    
        "message": "Empty search query.",    
        "results": [],    
    }    

try:    
    # -------------------------------------------------    
    # FIRST SEARCH    
    # -------------------------------------------------    

    first_results = self._perform_search(    
        search_query    
    )    

    if first_results:    

        related_results = (    
            self._filter_obviously_unrelated_results(    
                search_query,    
                first_results    
            )    
        )    

        # If at least one result looks related,    
        # keep the successful first search.    
        if related_results:    

            final_results = (    
                self._complete_results(    
                    related_results    
                )    
            )    

            return {    
                "status": "success",    
                "search_query": search_query,    
                "results": final_results,    
            }    

    # -------------------------------------------------    
    # SECOND SEARCH    
    # Only reached when the first search produced    
    # no useful/related results.    
    # -------------------------------------------------    

    retry_query = (    
        self._build_retry_query(    
            search_query    
        )    
    )    

    if (    
        retry_query    
        and retry_query.lower()    
        != search_query.lower()    
    ):    
        retry_results = (    
            self._perform_search(    
                retry_query    
            )    
        )    

        if retry_results:    

            retry_related_results = (    
                self._filter_obviously_unrelated_results(    
                    retry_query,    
                    retry_results    
                )    
            )    

            if retry_related_results:    

                final_results = (    
                    self._complete_results(    
                        retry_related_results    
                    )    
                )    

                return {    
                    "status": "success",    
                    "search_query": retry_query,    
                    "original_search_query": (    
                        search_query    
                    ),    
                    "retry_used": True,    
                    "results": final_results,    
                }    

    # -------------------------------------------------    
    # If both searches fail to produce a related    
    # result, preserve the old behavior and return    
    # the original results if they existed.    
    # -------------------------------------------------    

    if first_results:    

        final_results = (    
            self._complete_results(    
                first_results    
            )    
        )    

        return {    
            "status": "success",    
            "search_query": search_query,    
            "results": final_results,    
            "retry_used": False,    
            "relevance_fallback": True,    
        }    

    return {    
        "status": "empty",    
        "search_query": search_query,    
        "results": [],    
        "message": (    
            "No valid Bing RSS results."    
        ),    
    }    

except requests.Timeout:    
    return {    
        "status": "error",    
        "message": (    
            "Web search timed out."    
        ),    
        "search_query": search_query,    
        "results": [],    
    }    

except requests.RequestException as exc:    
    return {    
        "status": "error",    
        "message": (    
            f"Web search request failed: "    
            f"{str(exc)}"    
        ),    
        "search_query": search_query,    
        "results": [],    
    }    

except Exception as exc:    
    return {    
        "status": "error",    
        "message": (    
            f"Web search failed: "    
            f"{str(exc)}"    
        ),    
        "search_query": search_query,    
        "results": [],    
    }    
```
 
def learn_from_url(
self,
url: str,
title=None,
knowledge_type=None,
confidence=None
):
 
```
if not self._valid_url(url):    
    return {    
        "status": "error",    
        "message": "Invalid URL.",    
    }    

try:    
    content = self._fetch_page(    
        url    
    )    

    if not content:    
        return {    
            "status": "error",    
            "message": (    
                "Could not extract "    
                "content from URL."    
            ),    
        }    

    return {    
        "status": "success",    
        "url": url,    
        "title": title,    
        "knowledge_type": knowledge_type,    
        "confidence": confidence,    
        "content": content,    
    }    

except Exception as exc:    
    return {    
        "status": "error",    
        "message": str(exc),    
    }  
```
 
web_learning = WebLearning()
