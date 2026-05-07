from pathlib import Path
from playwright.sync_api import sync_playwright


def html_to_pdf(html_path, pdf_path):
    html_path = Path(html_path).resolve()
    pdf_path = Path(pdf_path).resolve()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        page.goto(f"file:///{html_path}", wait_until="networkidle")

        page.pdf(
            path=str(pdf_path),
            format="A4",
            print_background=True,
        )

        browser.close()

if __name__ == "__main__":
    html_to_pdf(
        "../output/reports/new_high_report_{}.html",
        "../output/reports/new_high_report.pdf"
    )