"""
DRAGON AI CORE
Web Learning Engine

يدعم:
1. التعلم من رابط يحدده المستخدم.
2. البحث التلقائي في الويب من السؤال.
3. استخراج النص من صفحات الويب.
4. التحقق الأساسي من عناوين URL لمنع الوصول إلى
   العناوين المحلية والخاصة.
"""

from html.parser import HTMLParser
from ipaddress import ip_address
from socket import gethostbyname
from urllib.error import HTTPError, URLError
from urllib.parse import (
    parse_qs,
    unquote,
    urlencode,
    urlparse,
)
from urllib.request import (
    Request,
    urlopen,
)


ALLOWED_SCHEMES = {"http", "https"}

REQUEST_TIMEOUT = 15
MAX_DOWNLOAD_BYTES = 2_000_000
MAX_CONTENT_CHARS = 50_000

MAX_SEARCH_RESULTS = 5
MAX_SEARCH_SOURCES_TO_FETCH = 2
MAX_SEARCH_CONTENT_CHARS = 12_000

SEARCH_ENGINE_URL = "https://html.duckduckgo.com/html/"

USER_AGENT = (
    "Mozilla/5.0 "
    "(compatible; DRAGON-AI-CORE/1.0; +https://github.com/)"
)


class WebTextExtractor(HTMLParser):
    """
    استخراج النص الظاهر من HTML.
    """

    SKIP_TAGS = {
        "script",
        "style",
        "noscript",
        "svg",
        "canvas",
        "iframe",
    }

    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()

        if tag in self.SKIP_TAGS:
            self.skip_depth += 1

    def handle_endtag(self, tag):
        tag = tag.lower()

        if (
            tag in self.SKIP_TAGS
            and self.skip_depth > 0
        ):
            self.skip_depth -= 1

    def handle_data(self, data):
        if self.skip_depth > 0:
            return

        text = data.strip()

        if text:
            self.parts.append(text)

    def get_text(self):
        return " ".join(self.parts)


class WebSearchExtractor(HTMLParser):
    """
    استخراج نتائج البحث من صفحة DuckDuckGo HTML.
    """

    def __init__(self):
        super().__init__()

        self.results = []

        self.current_title = ""
        self.current_url = ""
        self.current_snippet = ""

        self.in_result = False
        self.in_title = False
        self.in_snippet = False

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()

        attrs_dict = dict(attrs)

        classes = attrs_dict.get(
            "class",
            ""
        )

        class_names = set(
            classes.split()
        )

        # --------------------------------------------------
        # بداية نتيجة بحث جديدة
        # --------------------------------------------------

        if (
            tag == "a"
            and "result__a" in class_names
        ):

            # حفظ النتيجة السابقة أولًا
            if self.in_result:
                self.close_result()

            self.in_result = True
            self.in_title = True
            self.in_snippet = False

            self.current_title = ""
            self.current_url = ""
            self.current_snippet = ""

            self.current_url = attrs_dict.get(
                "href",
                ""
            ).strip()

            return

        # --------------------------------------------------
        # بداية النص المختصر
        # --------------------------------------------------

        if (
            tag in {"a", "div"}
            and "result__snippet" in class_names
            and self.in_result
        ):
            self.in_snippet = True

    def handle_endtag(self, tag):
        tag = tag.lower()

        if (
            tag == "a"
            and self.in_title
        ):
            self.in_title = False

        if (
            tag in {"a", "div"}
            and self.in_snippet
        ):
            self.in_snippet = False

    def handle_data(self, data):
        text = data.strip()

        if not text:
            return

        if self.in_title:
            self.current_title += (
                " " + text
            )

        elif self.in_snippet:
            self.current_snippet += (
                " " + text
            )

    def handle_startendtag(
        self,
        tag,
        attrs
    ):
        pass

    def close_result(self):
        title = " ".join(
            self.current_title.split()
        )

        snippet = " ".join(
            self.current_snippet.split()
        )

        url = self.current_url.strip()

        if title and url:
            self.results.append(
                {
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                }
            )

        self.in_result = False
        self.in_title = False
        self.in_snippet = False

        self.current_title = ""
        self.current_url = ""
        self.current_snippet = ""

    def get_results(self):
        # حفظ آخر نتيجة
        if self.in_result:
            self.close_result()

        return self.results


class WebLearningEngine:
    def __init__(self):
        self.name = "Web Learning Engine"

    # ---------------------------------------------------------
    # URL VALIDATION
    # ---------------------------------------------------------

    def _validate_url(self, url: str):
        if not url:
            return False, "الرابط فارغ."

        try:
            parsed = urlparse(url)

        except Exception:
            return False, "تعذر تحليل الرابط."

        if parsed.scheme.lower() not in ALLOWED_SCHEMES:
            return False, "نوع الرابط غير مسموح."

        if not parsed.hostname:
            return False, (
                "الرابط لا يحتوي على اسم نطاق صالح."
            )

        hostname = parsed.hostname.lower().strip()

        blocked_hosts = {
            "localhost",
            "localhost.localdomain",
        }

        if hostname in blocked_hosts:
            return False, (
                "الوصول إلى العنوان المحلي غير مسموح."
            )

        try:
            resolved_ip = gethostbyname(
                hostname
            )

            ip = ip_address(
                resolved_ip
            )

            if (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_reserved
                or ip.is_multicast
                or ip.is_unspecified
            ):
                return False, (
                    "الوصول إلى عنوان شبكة "
                    "خاص أو محلي غير مسموح."
                )

        except Exception:
            return False, (
                "تعذر التحقق من عنوان النطاق."
            )

        return True, None

    # ---------------------------------------------------------
    # FETCH URL
    # ---------------------------------------------------------

    def _fetch_url(self, url: str):
        valid, error = self._validate_url(
            url
        )

        if not valid:
            return {
                "status": "error",
                "message": error,
            }

        request = Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": (
                    "text/html,application/xhtml+xml,"
                    "application/xml;q=0.9,*/*;q=0.8"
                ),
            },
        )

        try:
            with urlopen(
                request,
                timeout=REQUEST_TIMEOUT
            ) as response:

                content_type = response.headers.get(
                    "Content-Type",
                    ""
                ).lower()

                if (
                    "text/html" not in content_type
                    and "application/xhtml+xml"
                    not in content_type
                    and "text/plain"
                    not in content_type
                ):
                    return {
                        "status": "error",
                        "message": (
                            "نوع المحتوى غير مدعوم."
                        ),
                    }

                data = response.read(
                    MAX_DOWNLOAD_BYTES + 1
                )

                if len(data) > MAX_DOWNLOAD_BYTES:
                    return {
                        "status": "error",
                        "message": (
                            "حجم الصفحة أكبر "
                            "من الحد المسموح."
                        ),
                    }

                charset = self._detect_charset(
                    content_type,
                    data
                )

                try:
                    text = data.decode(
                        charset,
                        errors="replace"
                    )

                except Exception:
                    text = data.decode(
                        "utf-8",
                        errors="replace"
                    )

                return {
                    "status": "success",
                    "url": response.geturl(),
                    "content_type": content_type,
                    "text": text,
                }

        except HTTPError as exc:
            return {
                "status": "error",
                "message": (
                    f"HTTP error: {exc.code}"
                ),
            }

        except URLError as exc:
            return {
                "status": "error",
                "message": (
                    f"تعذر الوصول إلى الرابط: "
                    f"{exc.reason}"
                ),
            }

        except Exception as exc:
            return {
                "status": "error",
                "message": (
                    f"حدث خطأ أثناء تحميل الصفحة: "
                    f"{exc}"
                ),
            }

    # ---------------------------------------------------------
    # CHARACTER ENCODING
    # ---------------------------------------------------------

    def _detect_charset(
        self,
        content_type: str,
        data: bytes
    ):
        content_type_lower = (
            content_type.lower()
        )

        marker = "charset="

        if marker in content_type_lower:

            charset = (
                content_type_lower
                .split(marker, 1)[1]
                .split(";", 1)[0]
                .strip()
                .strip('"')
                .strip("'")
            )

            if charset:
                return charset

        sample = data[:10_000].decode(
            "ascii",
            errors="ignore"
        )

        lower_sample = sample.lower()

        marker = 'charset="'

        if marker in lower_sample:

            value = (
                lower_sample
                .split(marker, 1)[1]
                .split('"', 1)[0]
            )

            if value:
                return value

        marker = "charset="

        if marker in lower_sample:

            value = (
                lower_sample
                .split(marker, 1)[1]
                .split(">", 1)[0]
                .split(";", 1)[0]
                .split('"', 1)[0]
                .strip()
            )

            if value:
                return value

        return "utf-8"

    # ---------------------------------------------------------
    # HTML EXTRACTION
    # ---------------------------------------------------------

    def _extract_text(
        self,
        html: str
    ):
        extractor = WebTextExtractor()

        try:
            extractor.feed(html)
            extractor.close()

            text = extractor.get_text()

        except Exception:
            text = html

        return text

    # ---------------------------------------------------------
    # CLEAN CONTENT
    # ---------------------------------------------------------

    def _clean_content(
        self,
        content: str,
        max_chars: int = MAX_CONTENT_CHARS
    ):
        lines = []

        for line in content.splitlines():

            cleaned = " ".join(
                line.split()
            )

            if cleaned:
                lines.append(
                    cleaned
                )

        result = " ".join(
            lines
        )

        if len(result) > max_chars:
            result = result[:max_chars]

        return result.strip()

    # ---------------------------------------------------------
    # PREPARE SOURCE
    # ---------------------------------------------------------

    def prepare_source(
        self,
        url: str,
        max_chars: int = MAX_CONTENT_CHARS
    ):
        fetched = self._fetch_url(
            url
        )

        if fetched.get("status") != "success":
            return fetched

        raw_text = fetched.get(
            "text",
            ""
        )

        content_type = fetched.get(
            "content_type",
            ""
        ).lower()

        if (
            "text/html" in content_type
            or "application/xhtml+xml"
            in content_type
        ):
            extracted = self._extract_text(
                raw_text
            )

        else:
            extracted = raw_text

        content = self._clean_content(
            extracted,
            max_chars=max_chars
        )

        if not content:
            return {
                "status": "error",
                "message": (
                    "لم يتم العثور على نص "
                    "قابل للاستخراج."
                ),
                "url": fetched.get(
                    "url",
                    url
                ),
            }

        return {
            "status": "success",
            "url": fetched.get(
                "url",
                url
            ),
            "content": content,
        }

    # ---------------------------------------------------------
    # LEARN FROM URL
    # ---------------------------------------------------------

    def learn_from_url(
        self,
        url: str,
        title: str,
        knowledge_type: str = "fact",
        confidence: str = "low"
    ):
        source = self.prepare_source(
            url
        )

        if source.get(
            "status"
        ) != "success":

            return {
                "status": "error",
                "message": source.get(
                    "message",
                    "فشل استخراج محتوى الرابط."
                ),
            }

        content = source.get(
            "content",
            ""
        )

        return {
            "status": "prepared",
            "title": title,
            "content": content,
            "source": source.get(
                "url",
                url
            ),
            "knowledge_type": knowledge_type,
            "confidence": confidence,
        }

    # ---------------------------------------------------------
    # NORMALIZE SEARCH URL
    # ---------------------------------------------------------

    def _normalize_search_url(
        self,
        url: str
    ):
        url = url.strip()

        if not url:
            return ""

        if url.startswith("//"):
            url = "https:" + url

        parsed = urlparse(
            url
        )

        query = parse_qs(
            parsed.query
        )

        if (
            parsed.hostname
            and parsed.hostname.endswith(
                "duckduckgo.com"
            )
            and "uddg" in query
        ):
            target = query.get(
                "uddg",
                [""]
            )[0]

            if target:
                return unquote(
                    target
                )

        return url

    # ---------------------------------------------------------
    # SEARCH WEB
    # ---------------------------------------------------------

    def search_web(
        self,
        question: str
    ):
        clean_question = " ".join(
            str(question)
            .strip()
            .split()
        )

        if not clean_question:
            return {
                "status": "error",
                "message": "السؤال فارغ.",
            }

        search_url = (
            SEARCH_ENGINE_URL
            + "?"
            + urlencode(
                {
                    "q": clean_question,
                }
            )
        )

        request = Request(
            search_url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html",
            },
        )

        try:
            with urlopen(
                request,
                timeout=REQUEST_TIMEOUT
            ) as response:

                data = response.read(
                    MAX_DOWNLOAD_BYTES
                )

                charset = self._detect_charset(
                    response.headers.get(
                        "Content-Type",
                        ""
                    ),
                    data
                )

                html = data.decode(
                    charset,
                    errors="replace"
                )

        except HTTPError as exc:
            return {
                "status": "error",
                "message": (
                    f"فشل البحث في الويب: "
                    f"HTTP {exc.code}"
                ),
            }

        except URLError as exc:
            return {
                "status": "error",
                "message": (
                    f"تعذر الاتصال بمحرك البحث: "
                    f"{exc.reason}"
                ),
            }

        except Exception as exc:
            return {
                "status": "error",
                "message": (
                    f"حدث خطأ أثناء البحث: "
                    f"{exc}"
                ),
            }

        parser = WebSearchExtractor()

        try:
            parser.feed(
                html
            )

            parser.close()

            search_results = (
                parser.get_results()
            )

        except Exception:
            search_results = []

        normalized_results = []

        for item in search_results:

            title = str(
                item.get(
                    "title",
                    ""
                )
            ).strip()

            snippet = str(
                item.get(
                    "snippet",
                    ""
                )
            ).strip()

            raw_url = str(
                item.get(
                    "url",
                    ""
                )
            ).strip()

            url = self._normalize_search_url(
                raw_url
            )

            if not title or not url:
                continue

            valid, _ = self._validate_url(
                url
            )

            if not valid:
                continue

            normalized_results.append(
                {
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                }
            )

            if (
                len(normalized_results)
                >= MAX_SEARCH_RESULTS
            ):
                break

        if not normalized_results:
            return {
                "status": "success",
                "question": clean_question,
                "results": [],
                "source_count": 0,
                "knowledge_saved": False,
                "evidence_status": "unverified",
            }

        final_results = []

        for item in normalized_results[
            :MAX_SEARCH_SOURCES_TO_FETCH
        ]:

            source = self.prepare_source(
                item["url"],
                max_chars=MAX_SEARCH_CONTENT_CHARS
            )

            content = ""

            if source.get(
                "status"
            ) == "success":

                content = source.get(
                    "content",
                    ""
                )

            final_results.append(
                {
                    "title": item["title"],
                    "url": item["url"],
                    "snippet": item["snippet"],
                    "content": content,
                }
            )

        return {
            "status": "success",
            "question": clean_question,
            "results": final_results,
            "source_count": len(
                final_results
            ),
            "knowledge_saved": False,
            "evidence_status": "unverified",
        }


web_learning = WebLearningEngine()
