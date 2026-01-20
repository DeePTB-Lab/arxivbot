import requests
import json
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from ..config import LarkConfig, EmailConfig
from .models import Paper
from loguru import logger

class BaseNotifier:
    def post(self, papers: List[Paper], tag: str):
        raise NotImplementedError

class LarkNotifier(BaseNotifier):
    def __init__(self, config: LarkConfig):
        self.config = config

    def post(self, papers: List[Paper], tag: str):
        if not papers:
            logger.info("No papers to post to Lark.")
            return

        logger.info(f"Posting {len(papers)} papers to Lark...")
        
        today_date = datetime.date.today().strftime('%Y-%m-%d')
        
        table_rows = []
        paper_list = []
        
        for i, paper in enumerate(papers):
            table_rows.append({
                "index": i + 1,
                "title": paper.title,
                "url": f"[{paper.url}]({paper.url})"
            })
            
            # Format Deep Scan Content
            deep_summary_text = ""
            if paper.deep_summary:
                deep_summary_text = f"{paper.deep_summary}"
            
            paper_list.append({
                "counter": i + 1,
                "title": paper.title,
                "id": paper.id,
                "abstract": paper.abstract,
                "zh_abstract": paper.zh_abstract or "Running translation...",
                "deep_summary": deep_summary_text,
                "url": paper.url,
                "published": paper.published
            })

        card_data = {
            "type": "template",
            "data": {
                "template_id": self.config.template_id,
                "template_version_name": self.config.template_version,
                "template_variable": {
                    "today_date": today_date,
                    "tag": tag,
                    "total_paper": len(papers),
                    "table_rows": table_rows,
                    "paper_list": paper_list
                }
            }
        }

        data = {
            "msg_type": "interactive",
            "card": card_data
        }

        try:
            response = requests.post(
                self.config.webhook_url, 
                headers={'Content-Type': 'application/json'}, 
                data=json.dumps(data)
            )
            if response.status_code == 200:
                logger.info(f"Lark response: {response.json()}")
            else:
                logger.error(f"Lark request failed: {response.status_code}, {response.text}")
        except Exception as e:
            logger.error(f"Error posting to Lark: {e}")

class EmailNotifier(BaseNotifier):
    def __init__(self, config: EmailConfig):
        self.config = config

    def post(self, papers: List[Paper], tag: str):
        if not papers:
            logger.info("No papers to email.")
            return

        logger.info(f"Sending email with {len(papers)} papers...")
        
        msg = MIMEMultipart()
        msg['From'] = self.config.sender_email
        msg['To'] = self.config.receiver_email
        msg['Subject'] = f"[{tag}] ArXiv Papers Daily - {datetime.date.today()}"

        # Build HTML Body
        html_body = "<html><body>"
        html_body += f"<h2>Today's ArXiv Papers ({len(papers)})</h2>"
        
        for i, paper in enumerate(papers):
            html_body += f"<hr>"
            html_body += f"<h3>{i+1}. <a href='{paper.url}'>{paper.title}</a></h3>"
            html_body += f"<p><b>ID:</b> {paper.id} | <b>Published:</b> {paper.published}</p>"
            
            if paper.zh_abstract:
                html_body += f"<p><b>Abstract (CN):</b> {paper.zh_abstract}</p>"
            else:
                html_body += f"<p><b>Abstract:</b> {paper.abstract}</p>"
            
            if paper.introduction:
                 html_body += f"<details><summary><b>Introduction (Deep Scan)</b></summary><p>{paper.introduction[:500]}...</p></details>"
            
        html_body += "</body></html>"

        msg.attach(MIMEText(html_body, 'html'))

        try:
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.sender_email, self.config.sender_password)
                server.send_message(msg)
            logger.info("Email sent successfully.")
        except Exception as e:
            logger.error(f"Error sending email: {e}")
