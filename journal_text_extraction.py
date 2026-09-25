from bs4 import BeautifulSoup

def extract_journal_text_bs4(html_str: str) -> str:
    soup = BeautifulSoup(html_str, "html.parser")

    # Remove head/style tags
    for tag in soup(["head", "style", "script"]):
        tag.decompose()

    # Extract non-empty text from each paragraph
    lines = [p.get_text(strip=True) for p in soup.find_all("p") if p.get_text(strip=True)]
    return "\n".join(lines)