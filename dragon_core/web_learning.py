"""
DRAGON AI CORE
Web Learning and Automatic Web Search

Responsibilities:
- Web search
- Search query preparation
- Result relevance evaluation
- Web page extraction
- Evidence preparation
- URL validation
- Retry search
- Source metadata

This module does NOT directly store knowledge.
Knowledge storage is handled by KnowledgeBase.
"""

import base64
import html
import re
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import requests


# =========================================================
# CONFIGURATION
# =========================================================

SEARCH_ENGINE_URL = "https://www.bing.com/search"

REQUEST_TIMEOUT = 15

MAX_RESULTS = 5

MAX_CONTENT_LENGTH = 12000

MIN_RELEVANCE_SCORE = 2

MAX_QUERY_LENGTH = 500

MAX_URL_LENGTH = 2048


# =========================================================
# WEB LEARNING
# =========================================================

class WebLearning:

    def __init__(self):
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
                "Connection": "keep-alive",
            }
        )

    # =========================================================
    # QUERY PREPARATION
    # =========================================================

    def _prepare_search_query(
        self,
        query: str
    ) -> str:

        query = str(query or "").strip()

        if not query:
            return ""

        if len(query) > MAX_QUERY_LENGTH:
            query = query[:MAX_QUERY_LENGTH]

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

    def _build_retry_query(
        self,
        query: str
    ) -> str:
        """
        Build a second search query from important
        terms in the original query.

        No arbitrary dates or fabricated context
        are added.
        """

        original_query = str(
            query or ""
        ).strip()

        if not original_query:
            return ""

        query = self._prepare_search_query(
            original_query
        )

        if not query:
            return ""

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
            "اخر",
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

        if (
            core_query.lower()
            == query.lower()
        ):
            if len(important_words) >= 2:
                return f'"{core_query}"'

            return core_query

        if len(important_words) >= 2:
            return f'"{core_query}"'

        return core_query

    # =========================================================
    # TEXT NORMALIZATION
    # =========================================================

    def _normalize_text(
        self,
        text: str
    ) -> str:

        if not text:
            return ""

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

    def _tokenize(
        self,
        text: str
    ):
        normalized = self._normalize_text(
            text
        )

        if not normalized:
            return []

        return normalized.split()

    # =========================================================
    # QUERY TERMS
    # =========================================================

    def _get_query_terms(
        self,
        query: str
    ):

        normalized = self._normalize_text(
            query
        )

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
            "is",
            "are",
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

    # =========================================================
    # RELEVANCE
    # =========================================================

    def _count_term_matches(
        self,
        terms,
        text
    ):

        tokens = set(
            self._tokenize(text)
        )

        return sum(
            1
            for term in terms
            if term in tokens
        )

    def _score_result_relevance(
        self,
        query: str,
        result: dict
    ) -> int:
        """
        Calculate relevance score.

        Weight:
        - Exact phrase: strong
        - Title: strong
        - Snippet: medium
        - Content: lower
        - All terms matched: bonus
        """

        query_terms = self._get_query_terms(
            query
        )

        if not query_terms:
            return 0

        title = self._normalize_text(
            result.get("title", "")
        )

        snippet = self._normalize_text(
            result.get("snippet", "")
        )

        content = self._normalize_text(
            result.get("content", "")[:5000]
        )

        title_tokens = set(
            title.split()
        )

        snippet_tokens = set(
            snippet.split()
        )

        content_tokens = set(
            content.split()
        )

        score = 0

        normalized_query = self._normalize_text(
            query
        )

        searchable_text = " ".join(
            [
                title,
                snippet,
                content,
            ]
        ).strip()

        # -----------------------------------------------------
        # Exact phrase
        # -----------------------------------------------------

        if (
            normalized_query
            and normalized_query in searchable_text
        ):
            score += 5

        matched_terms = 0

        for term in query_terms:

            if term in title_tokens:
                score += 4
                matched_terms += 1

            elif term in snippet_tokens:
                score += 2
                matched_terms += 1

            elif term in content_tokens:
                score += 1
                matched_terms += 1

        # -----------------------------------------------------
        # All terms matched
        # -----------------------------------------------------

        if matched_terms == len(query_terms):
            score += 4

        return score

    def _result_is_related(
        self,
        query: str,
        result: dict
    ) -> bool:
        """
        Decide whether a web result is sufficiently
        related to the requested query.
        """

        query_terms = self._get_query_terms(
            query
        )

        if not query_terms:
            return False

        title = self._normalize_text(
            result.get("title", "")
        )

        snippet = self._normalize_text(
            result.get("snippet", "")
        )

        content = self._normalize_text(
            result.get("content", "")[:5000]
        )

        searchable_text = " ".join(
            [
                title,
                snippet,
                content,
            ]
        ).strip()

        if not searchable_text:
            return False

        score = self._score_result_relevance(
            query,
            result
        )

        # -----------------------------------------------------
        # One-term query
        # -----------------------------------------------------

        if len(query_terms) == 1:
            return score >= MIN_RELEVANCE_SCORE

        # -----------------------------------------------------
        # Term matches
        # -----------------------------------------------------

        title_matches = self._count_term_matches(
            query_terms,
            title
        )

        snippet_matches = self._count_term_matches(
            query_terms,
            snippet
        )

        content_matches = self._count_term_matches(
            query_terms,
            content
        )

        del title_matches
        del snippet_matches
        del content_matches

        total_matches = len(
            {
                term
                for term in query_terms
                if (
                    term in set(title.split())
                    or term in set(snippet.split())
                    or term in set(content.split())
                )
            }
        )

        # -----------------------------------------------------
        # Exact phrase
        # -----------------------------------------------------

        normalized_query = self._normalize_text(
            query
        )

        if (
            normalized_query
            and normalized_query in searchable_text
        ):
            return True

        # -----------------------------------------------------
        # Two-term query
        # -----------------------------------------------------

        if len(query_terms) == 2:
            return (
                total_matches >= 2
                and score >= MIN_RELEVANCE_SCORE
            )

        # -----------------------------------------------------
        # Longer query
        # -----------------------------------------------------

        required_matches = max(
            2,
            (len(query_terms) + 1) // 2
        )

        return (
            total_matches >= required_matches
            and score >= MIN_RELEVANCE_SCORE
        )

    def _filter_obviously_unrelated_results(
        self,
        query: str,
        results
    ):

        if not results:
            return []

        scored_results = []

        for result in results:

            if not self._result_is_related(
                query,
                result
            ):
                continue

            score = self._score_result_relevance(
                query,
                result
            )

            result = dict(result)

            result["relevance_score"] = score

            scored_results.append(
                (
                    score,
                    result
                )
            )

        scored_results.sort(
            key=lambda item: item[0],
            reverse=True
        )

        return [
            result
            for score, result
            in scored_results[:MAX_RESULTS]
        ]

    # =========================================================
    # URL HANDLING
    # =========================================================

    def _normalize_search_url(
        self,
        url: str
    ) -> str:

        if not url:
            return ""

        url = html.unescape(url)
        url = urllib.parse.unquote(url)

        parsed = urllib.parse.urlparse(
            url
        )

        if "bing.com" in parsed.netloc.lower():

            query = urllib.parse.parse_qs(
                parsed.query
            )

            for key in (
                "u",
                "url",
                "r",
            ):

                values = query.get(
                    key
                )

                if values:

                    candidate = values[0]

                    if candidate.startswith(
                        "http"
                    ):
                        return candidate

                    decoded = (
                        self._decode_bing_url(
                            candidate
                        )
                    )

                    if decoded:
                        return decoded

        return url

    def _decode_bing_url(
        self,
        value: str
    ) -> str:

        if not value:
            return ""

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

                decoded = (
                    base64.urlsafe_b64decode(
                        encoded + padding
                    )
                    .decode(
                        "utf-8",
                        errors="ignore"
                    )
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

    def _valid_url(
        self,
        url: str
    ) -> bool:

        if not url:
            return False

        if len(url) > MAX_URL_LENGTH:
            return False

        try:

            parsed = urllib.parse.urlparse(
                url
            )

            return (
                parsed.scheme.lower()
                in (
                    "http",
                    "https",
                )
                and bool(parsed.netloc)
            )

        except Exception:
            return False

    # =========================================================
    # TEXT CLEANING
    # =========================================================

    def _clean_text(
        self,
        text: str
    ) -> str:

        if not text:
            return ""

        text = html.unescape(
            str(text)
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

    # =========================================================
    # BING RSS
    # =========================================================

    def _parse_bing_rss(
        self,
        xml_text: str
    ):

        results = []

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
                    "content": "",
                    "source_type": "web_search",
                    "evidence_status": "web_unverified",
                }
            )

            if len(results) >= MAX_RESULTS:
                break

        return results

    # =========================================================
    # PAGE CONTENT
    # =========================================================

    def _extract_html_content(
        self,
        text: str
    ) -> str:

        if not text:
            return ""

        # -----------------------------------------------------
        # Remove scripts
        # -----------------------------------------------------

        text = re.sub(
            r"<script\b[^>]*>.*?</script>",
            " ",
            text,
            flags=(
                re.IGNORECASE
                | re.DOTALL
            ),
        )

        # -----------------------------------------------------
        # Remove styles
        # -----------------------------------------------------

        text = re.sub(
            r"<style\b[^>]*>.*?</style>",
            " ",
            text,
            flags=(
                re.IGNORECASE
                | re.DOTALL
            ),
        )

        # -----------------------------------------------------
        # Remove noscript
        # -----------------------------------------------------

        text = re.sub(
            r"<noscript\b[^>]*>.*?</noscript>",
            " ",
            text,
            flags=(
                re.IGNORECASE
                | re.DOTALL
            ),
        )

        # -----------------------------------------------------
        # Remove HTML tags
        # -----------------------------------------------------

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

    def _fetch_page(
        self,
        url: str
    ) -> str:

        if not self._valid_url(url):
            return ""

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

            allowed_content = (
                "text/html",
                "text/plain",
                "application/xhtml+xml",
            )

            if not any(
                content_type.startswith(
                    content
                )
                for content in allowed_content
            ):
                return ""

            return self._extract_html_content(
                response.text
            )

        except requests.RequestException:
            return ""

        except Exception:
            return ""

    # =========================================================
    # SEARCH
    # =========================================================

    def _perform_search(
        self,
        search_query: str
    ):

        """
        Execute one Bing RSS search.
        """

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

    def _complete_results(
        self,
        results
    ):

        """
        Fetch page content while preserving
        search metadata.
        """

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

            relevance_score = result.get(
                "relevance_score",
                0
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
                    "relevance_score": (
                        relevance_score
                    ),
                    "source_type": (
                        result.get(
                            "source_type",
                            "web_search"
                        )
                    ),
                    "evidence_status": (
                        result.get(
                            "evidence_status",
                            "web_unverified"
                        )
                    ),
                    "retrieved_at": (
                        datetime.now(
                            timezone.utc
                        ).isoformat()
                    ),
                }
            )

        return final_results

    # =========================================================
    # POST-FETCH VALIDATION
    # =========================================================

    def _validate_completed_results(
        self,
        query: str,
        results
    ):

        """
        Re-check results after page content has been
        downloaded.

        This prevents a weak snippet from being treated
        as strong evidence when the actual page content
        is unrelated.
        """

        if not results:
            return []

        validated = []

        for result in results:

            if not self._result_is_related(
                query,
                result
            ):
                continue

            result = dict(result)

            result["relevance_score"] = (
                self._score_result_relevance(
                    query,
                    result
                )
            )

            validated.append(
                result
            )

        validated.sort(
            key=lambda item: item.get(
                "relevance_score",
                0
            ),
            reverse=True
        )

        return validated[:MAX_RESULTS]

    def search_web(
        self,
        query: str
    ):

        """
        Search the web and return only sufficiently
        relevant results.

        Unrelated results are never returned as
        a fallback.
        """

        search_query = (
            self._prepare_search_query(
                query
            )
        )

        if not search_query:
            return {
                "status": "error",
                "message": (
                    "Empty search query."
                ),
                "results": [],
            }

        try:

            # =================================================
            # FIRST SEARCH
            # =================================================

            first_results = (
                self._perform_search(
                    search_query
                )
            )

            if first_results:

                related_results = (
                    self._filter_obviously_unrelated_results(
                        search_query,
                        first_results
                    )
                )

                if related_results:

                    final_results = (
                        self._complete_results(
                            related_results
                        )
                    )

                    final_results = (
                        self._validate_completed_results(
                            search_query,
                            final_results
                        )
                    )

                    if final_results:

                        return {
                            "status": "success",
                            "search_query": (
                                search_query
                            ),
                            "results": (
                                final_results
                            ),
                            "retry_used": False,
                        }

            # =================================================
            # RETRY SEARCH
            # =================================================

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

                        final_results = (
                            self._validate_completed_results(
                                retry_query,
                                final_results
                            )
                        )

                        if final_results:

                            return {
                                "status": "success",
                                "search_query": (
                                    retry_query
                                ),
                                "original_search_query": (
                                    search_query
                                ),
                                "retry_used": True,
                                "results": (
                                    final_results
                                ),
                            }

            # =================================================
            # NO RELEVANT RESULTS
            # =================================================

            return {
                "status": "empty",
                "search_query": search_query,
                "results": [],
                "message": (
                    "No sufficiently relevant web "
                    "results were found."
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
                    "Web search request failed: "
                    f"{str(exc)}"
                ),
                "search_query": search_query,
                "results": [],
            }

        except Exception as exc:

            return {
                "status": "error",
                "message": (
                    "Web search failed: "
                    f"{str(exc)}"
                ),
                "search_query": search_query,
                "results": [],
            }

    # =========================================================
    # LEARN FROM URL
    # =========================================================

    def learn_from_url(
        self,
        url: str,
        title=None,
        knowledge_type=None,
        confidence=None
    ):

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
                "knowledge_type": (
                    knowledge_type
                ),
                "confidence": confidence,
                "evidence_status": (
                    "web_unverified"
                ),
                "source_type": (
                    "direct_url"
                ),
                "retrieved_at": (
                    datetime.now(
                        timezone.utc
                    ).isoformat()
                ),
                "content": content,
            }

        except Exception as exc:

            return {
                "status": "error",
                "message": str(exc),
            }

    # =========================================================
    # EVIDENCE EXTRACTION
    # =========================================================

    def prepare_evidence(
        self,
        result: dict
    ) -> dict:
        """
        Convert a web result into a clean evidence
        object for DragonEngine / KnowledgeBase.

        This function does NOT store anything.
        """

        if not isinstance(
            result,
            dict
        ):
            return {
                "status": "error",
                "message": (
                    "Invalid web result."
                ),
            }

        title = str(
            result.get(
                "title",
                ""
            )
        ).strip()

        url = str(
            result.get(
                "url",
                ""
            )
        ).strip()

        snippet = str(
            result.get(
                "snippet",
                ""
            )
        ).strip()

        content = str(
            result.get(
                "content",
                ""
            )
        ).strip()

        if not url or not self._valid_url(url):

            return {
                "status": "error",
                "message": (
                    "Evidence URL is invalid."
                ),
            }

        evidence_content = (
            content
            or snippet
        )

        if not evidence_content:

            return {
                "status": "error",
                "message": (
                    "Evidence contains no content."
                ),
            }

        return {
            "status": "success",
            "title": title,
            "content": evidence_content,
            "source": url,
            "source_type": result.get(
                "source_type",
                "web_search"
            ),
            "knowledge_type": (
                "web_unverified"
            ),
            "evidence_status": (
                result.get(
                    "evidence_status",
                    "web_unverified"
                )
            ),
            "confidence": result.get(
                "confidence",
                "low"
            ),
            "relevance_score": result.get(
                "relevance_score",
                0
            ),
            "retrieved_at": result.get(
                "retrieved_at"
            ),
        }


# =========================================================
# GLOBAL INSTANCE
# =========================================================

web_learning = WebLearning()
