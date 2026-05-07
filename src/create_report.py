from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from playwright.sync_api import sync_playwright
import boto3

def create_report_html(newest_market_date, new_highs_df, Path_report_template, file_name_report_template, Path_output_report):
    ### HTML形式で保存
    env = Environment(loader=FileSystemLoader(Path_report_template))
    template = env.get_template(file_name_report_template)

    html = template.render(
        report_date=newest_market_date,
        stocks=new_highs_df.to_dict(orient="records")
    )

    with open(Path_output_report, "w", encoding="utf-8") as f:
        f.write(html)

def html_to_pdf(html_path, pdf_path):
    ### HTML形式のレポートをPDF形式に変換
    
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
            display_header_footer=False,
            scale=0.6,
            margin={
                "top": "12mm",
                "right": "5mm",
                "bottom": "12mm",
                "left": "5mm",
            },
        )

        browser.close()
    
def upload_report(
        Path_output_report_pdf, 
        CLOUDFLARE_ACCOUNT_ID, 
        R2_ACCESS_KEY_ID,
        R2_SECRET_ACCESS_KEY,
        r2_public_dev_url,
        r2_backet_name,
        r2_report_folder_name
    ):
    ### Cloudflare R2にレポートをPDF形式でアップロードして公開URLを取得

    Path_output_report_pdf = Path(Path_output_report_pdf)

    if not Path_output_report_pdf.exists():
        raise FileNotFoundError(f"PDFが見つかりません: {Path_output_report_pdf}")

    object_key = f"{r2_report_folder_name}/{Path_output_report_pdf.name}"

    s3 = boto3.client(
        "s3",
        endpoint_url=f"https://{CLOUDFLARE_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name="auto",
    )

    s3.upload_file(
        Filename=str(Path_output_report_pdf),
        Bucket=r2_backet_name,
        Key=object_key,
        ExtraArgs={
            "ContentType": "application/pdf",
        },
    )

    report_url = f"{r2_public_dev_url}/{object_key}"
    return report_url

def create_and_upload_report(
    newest_market_date, 
    new_highs_df, 
    Path_report_template, 
    file_name_report_template, 
    Path_output_report_html, 
    Path_output_report_pdf,
    CLOUDFLARE_ACCOUNT_ID,
    R2_ACCESS_KEY_ID,
    R2_SECRET_ACCESS_KEY,
    r2_public_dev_url,
    r2_backet_name,
    r2_report_folder_name
):
    # HTML形式のレポートを作成
    create_report_html(
        newest_market_date, 
        new_highs_df, 
        Path_report_template, 
        file_name_report_template, 
        Path_output_report_html
    )
    
    # PDF形式のレポートに変換
    html_to_pdf(Path_output_report_html, Path_output_report_pdf)
    
    # Cloudflare R2にPDF形式のレポートをアップロードして公開URLを取得
    report_url = upload_report(
        Path_output_report_pdf, 
        CLOUDFLARE_ACCOUNT_ID, 
        R2_ACCESS_KEY_ID,
        R2_SECRET_ACCESS_KEY,
        r2_public_dev_url,
        r2_backet_name,
        r2_report_folder_name
    )
    
    return report_url