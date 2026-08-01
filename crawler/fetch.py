import asyncio
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


async def fetch(url: str, timeout: int, retries: int) -> tuple[str, str]:
    def get():
        request = Request(url, headers={"User-Agent": "CompanyHunterMVP/1.0 (+contact)"})
        with urlopen(request, timeout=timeout) as response:
            return response.read(1_500_000).decode("utf-8", "ignore"), ""
    for attempt in range(retries + 1):
        try:
            return await asyncio.to_thread(get)
        except HTTPError as exc:
            return "", "blocked_403" if exc.code == 403 else f"http_{exc.code}"
        except URLError as exc:
            reason = str(exc.reason).lower()
            if attempt == retries:
                return "", "dns_error" if "name" in reason else "timeout"
        except TimeoutError:
            if attempt == retries:
                return "", "timeout"
        except Exception:
            if attempt == retries:
                return "", "parse_error"
    return "", "parse_error"
