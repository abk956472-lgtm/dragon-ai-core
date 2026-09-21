"""
DRAGON AI CORE
Web Learning Engine

مسؤول عن:
- استقبال روابط HTTP/HTTPS.
- جلب محتوى صفحات الويب.
- استخراج النص من HTML.
- إزالة العناصر غير المفيدة مثل script وstyle.
- تحديد المصدر.
- تجهيز المحتوى لمحرك التعلّم الذاتي.
- عدم اعتبار محتوى الإنترنت حقيقة مثبتة تلقائيًا.
- منع الوصول إلى عناوين الشبكات الداخلية والمحلية.

ملاحظة:
هذا الملف لا يحفظ المعرفة مباشرة.
الحفظ يتم من خلال self_learning.py.
"""

from html.parser import HTMLParser
from ipaddress import ip_address
from socket import getaddrinfo
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .self_learning import self_learning


class WebTextExtractor(HTMLParser):
    """
    استخراج النص المرئي من صفحات HTML.
    """

    IGNORED_TAGS = {
        "script",
        "style",
        "noscript",
        "svg",
        "iframe",
        "canvas",
        "template",
    }

    def __init__(self):
        super().__init__(
            convert_charrefs=True
        )

        self._ignored_depth = 0
        self._parts = []

    def handle_starttag(
        self,
        tag,
        attrs
    ):
        tag = tag.lower()

        if tag in self.IGNORED_TAGS:
            self._ignored_depth += 1

    def handle_endtag(
        self,
        tag
    ):
        tag = tag.lower()

        if tag in self.IGNORED_TAGS:
            if self._ignored_depth > 0:
                self._ignored_depth -= 1

    def handle_data(
        self,
        data
    ):
        if self._ignored_depth > 0:
            return

        text = data.strip()

        if text:
            self._parts.append(text)

    def get_text(self) -> str:
        return " ".join(self._parts)


class WebLearningEngine:
    """
    محرك التعلّم من الإنترنت.

    هذا المحرك يجمع المحتوى فقط ثم يمرره
    إلى SelfLearningEngine.

    لا يتم اعتبار المصدر حقيقة مثبتة
    لمجرد أنه موجود على الإنترنت.
    """

    ALLOWED_SCHEMES = {
        "http",
        "https",
    }

    DEFAULT_TIMEOUT = 15

    MAX_DOWNLOAD_BYTES = 2_000_000

    MAX_CONTENT_CHARS = 50_000

    USER_AGENT = (
        "DRAGON-AI-CORE/"
        "1.0 "
        "(web-learning)"
    )

    def __init__(self):
        self.last_result = None

    # ==========================================================
    # Public API
    # ==========================================================

    def learn_from_url(
        self,
        url: str,
        title: Optional[str] = None,
        knowledge_type: str = "fact",
        confidence: str = "low",
    ) -> dict:
        """
        جلب صفحة ويب ومحاولة تعلم محتواها.

        الحالة الافتراضية للأدلة:
        unverified

        وذلك لأن وجود معلومة على الإنترنت
        لا يساوي إثباتها علميًا.
        """

        validation = self._validate_url(url)

        if not validation["valid"]:
            result = {
                "status": "rejected",
                "reason": validation["reason"],
            }

            self.last_result = result
            return result

        clean_url = validation["url"]

        fetch_result = self._fetch_url(
            clean_url
        )

        if fetch_result["status"] != "success":
            self.last_result = fetch_result
            return fetch_result

        html = fetch_result["content"]

        text = self._extract_text(
            html
        )

        text = self._clean_content(
            text
        )

        if not text:
            result = {
                "status": "rejected",
                "reason": (
                    "No readable text was found "
                    "on the web page."
                ),
                "source": clean_url,
            }

            self.last_result = result
            return result

        if title:
            clean_title = title.strip()
        else:
            clean_title = (
                "Web knowledge: "
                + clean_url
            )

        result = self_learning.learn_from_source(
            title=clean_title,
            content=text,
            source=clean_url,
            knowledge_type=knowledge_type,
            evidence_status="unverified",
            confidence=confidence,
        )

        response = {
            "status": result.get(
                "status",
                "unknown"
            ),
            "source": clean_url,
            "content_length": len(text),
            "learning": result,
        }

        self.last_result = response

        return response

    # ==========================================================
    # URL validation
    # ==========================================================

    def _validate_url(
        self,
        url: str
    ) -> dict:
        """
        التحقق من الرابط ومنع الوصول
        إلى العناوين المحلية والخاصة.
        """

        if not url:
            return {
                "valid": False,
                "reason": "URL is required.",
            }

        clean_url = url.strip()

        try:
            parsed = urlparse(
                clean_url
            )
        except Exception:
            return {
                "valid": False,
                "reason": "Invalid URL.",
            }

        if parsed.scheme.lower() not in self.ALLOWED_SCHEMES:
            return {
                "valid": False,
                "reason": (
                    "Only HTTP and HTTPS URLs "
                    "are allowed."
                ),
            }

        if not parsed.hostname:
            return {
                "valid": False,
                "reason": "URL host is required.",
            }

        hostname = parsed.hostname.strip().lower()

        if self._is_blocked_hostname(hostname):
            return {
                "valid": False,
                "reason": (
                    "Local and private network addresses "
                    "are not allowed."
                ),
            }

        address_check = self._validate_host_addresses(
            hostname
        )

        if not address_check["valid"]:
            return address_check

        return {
            "valid": True,
            "url": clean_url,
        }

    # ==========================================================
    # Hostname protection
    # ==========================================================

    def _is_blocked_hostname(
        self,
        hostname: str
    ) -> bool:
        """
        منع أسماء المضيفين المحلية والخاصة المعروفة.
        """

        blocked_names = {
            "localhost",
            "localhost.localdomain",
            "ip6-localhost",
            "ip6-loopback",
        }

        if hostname in blocked_names:
            return True

        return hostname.endswith(
            ".localhost"
        )

    # ==========================================================
    # DNS / IP protection
    # ==========================================================

    def _validate_host_addresses(
        self,
        hostname: str
    ) -> dict:
        """
        حل اسم النطاق والتحقق من أن جميع العناوين
        الناتجة ليست محلية أو خاصة أو محجوزة.
        """

        try:
            direct_ip = ip_address(
                hostname
            )

            if self._is_private_address(
                direct_ip
            ):
                return {
                    "valid": False,
                    "reason": (
                        "Direct access to local, private, "
                        "or reserved IP addresses is not allowed."
                    ),
                }

            return {
                "valid": True,
                "reason": None,
            }

        except ValueError:
            pass

        try:
            addresses = getaddrinfo(
                hostname,
                None
            )
        except Exception:
            return {
                "valid": False,
                "reason": (
                    "Unable to resolve the web host."
                ),
            }

        if not addresses:
            return {
                "valid": False,
                "reason": (
                    "The web host has no resolved address."
                ),
            }

        checked_addresses = set()

        for address_info in addresses:
            address = address_info[4][0]

            if address in checked_addresses:
                continue

            checked_addresses.add(address)

            try:
                parsed_address = ip_address(
                    address
                )
            except ValueError:
                return {
                    "valid": False,
                    "reason": (
                        "The resolved host address is invalid."
                    ),
                }

            if self._is_private_address(
                parsed_address
            ):
                return {
                    "valid": False,
                    "reason": (
                        "The web host resolves to a local, "
                        "private, or reserved network address."
                    ),
                }

        return {
            "valid": True,
            "reason": None,
        }

    def _is_private_address(
        self,
        address
    ) -> bool:
        """
        تحديد العناوين التي لا ينبغي لمحرك الويب
        الوصول إليها.
        """

        return (
            address.is_private
            or address.is_loopback
            or address.is_link_local
            or address.is_multicast
            or address.is_reserved
            or address.is_unspecified
        )

    # ==========================================================
    # Web fetching
    # ==========================================================

    def _fetch_url(
        self,
        url: str
    ) -> dict:
        """
        جلب محتوى الصفحة مع حد زمني وحد للحجم.
        """

        request = Request(
            url,
            headers={
                "User-Agent": self.USER_AGENT,
                "Accept": (
                    "text/html,"
                    "application/xhtml+xml,"
                    "text/plain;q=0.9,"
                    "*/*;q=0.1"
                ),
            },
            method="GET",
        )

        try:
            with urlopen(
                request,
                timeout=self.DEFAULT_TIMEOUT
            ) as response:

                content_type = (
                    response.headers.get(
                        "Content-Type",
                        ""
                    )
                ).lower()

                content_length = (
                    response.headers.get(
                        "Content-Length"
                    )
                )

                if content_length:
                    try:
                        declared_size = int(
                            content_length
                        )

                        if (
                            declared_size
                            > self.MAX_DOWNLOAD_BYTES
                        ):
                            return {
                                "status": "rejected",
                                "reason": (
                                    "Web page is too large."
                                ),
                            }

                    except ValueError:
                        pass

                data = response.read(
                    self.MAX_DOWNLOAD_BYTES + 1
                )

                if len(data) > self.MAX_DOWNLOAD_BYTES:
                    return {
                        "status": "rejected",
                        "reason": (
                            "Downloaded content exceeds "
                            "the maximum allowed size."
                        ),
                    }

                charset = (
                    self._detect_charset(
                        content_type
                    )
                )

                try:
                    content = data.decode(
                        charset,
                        errors="replace"
                    )
                except LookupError:
                    content = data.decode(
                        "utf-8",
                        errors="replace"
                    )

                return {
                    "status": "success",
                    "content": content,
                    "content_type": content_type,
                }

        except HTTPError as error:
            return {
                "status": "error",
                "reason": (
                    f"HTTP error: "
                    f"{error.code}"
                ),
            }

        except URLError as error:
            return {
                "status": "error",
                "reason": (
                    f"URL error: "
                    f"{error.reason}"
                ),
            }

        except TimeoutError:
            return {
                "status": "error",
                "reason": (
                    "Web request timed out."
                ),
            }

        except Exception as error:
            return {
                "status": "error",
                "reason": (
                    f"Web request failed: "
                    f"{error}"
                ),
            }

    # ==========================================================
    # Charset
    # ==========================================================

    def _detect_charset(
        self,
        content_type: str
    ) -> str:
        """
        محاولة استخراج ترميز الصفحة.
        """

        content_type = content_type.lower()

        marker = "charset="

        if marker in content_type:
            charset = (
                content_type
                .split(marker, 1)[1]
                .split(";", 1)[0]
                .strip()
                .strip('"')
                .strip("'")
            )

            if charset:
                return charset

        return "utf-8"

    # ==========================================================
    # HTML extraction
    # ==========================================================

    def _extract_text(
        self,
        html: str
    ) -> str:
        """
        استخراج النص من HTML.
        """

        parser = WebTextExtractor()

        try:
            parser.feed(html)
            parser.close()

        except Exception:
            return ""

        return parser.get_text()

    # ==========================================================
    # Content cleaning
    # ==========================================================

    def _clean_content(
        self,
        content: str
    ) -> str:
        """
        تنظيف النص وتحديد الحد الأقصى.
        """

        if not content:
            return ""

        lines = []

        for line in content.splitlines():
            clean_line = " ".join(
                line.split()
            )

            if clean_line:
                lines.append(
                    clean_line
                )

        text = " ".join(lines)

        text = " ".join(
            text.split()
        )

        if len(text) > self.MAX_CONTENT_CHARS:
            text = text[
                :self.MAX_CONTENT_CHARS
            ]

        return text.strip()

    # ==========================================================
    # Source preparation
    # ==========================================================

    def prepare_source(
        self,
        url: str,
        title: Optional[str] = None,
    ) -> dict:
        """
        جلب المصدر وتجهيزه فقط، دون حفظ المعرفة.

        هذه الوظيفة مفيدة قبل مرحلة التعلم
        عندما نريد فحص المحتوى أولًا.
        """

        validation = self._validate_url(
            url
        )

        if not validation["valid"]:
            return validation

        clean_url = validation["url"]

        fetch_result = self._fetch_url(
            clean_url
        )

        if fetch_result["status"] != "success":
            return fetch_result

        text = self._extract_text(
            fetch_result["content"]
        )

        text = self._clean_content(
            text
        )

        if not text:
            return {
                "status": "rejected",
                "reason": (
                    "No readable text was found."
                ),
                "source": clean_url,
            }

        return {
            "status": "prepared",
            "title": (
                title.strip()
                if title
                else "Web knowledge"
            ),
            "source": clean_url,
            "content": text,
            "content_length": len(text),
            "evidence_status": "unverified",
            "confidence": "low",
        }


# ==============================================================
# Global web learning engine
# ==============================================================

web_learning = WebLearningEngine()
