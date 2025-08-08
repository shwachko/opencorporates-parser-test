import cloudscraper
import random
import time
import os

from fake_useragent import UserAgent
from temporalio import activity
from dotenv import load_dotenv

from utils.challenges import solve_math_challenge, handle_cloudflare_challenge, handle_turnstile_challenge
from utils.gzip_parse import process_gzip

from client import get_temporal_client

ua = UserAgent()
load_dotenv()

@activity.defn(name="fetch_and_parse_gz_xml")
async def fetch_and_parse_gz_xml(input: dict):

    workflow_id = input.get("workflow_id", None)
    run_id = input.get("run_id", None)
    link = input["link"]

    proxy = os.getenv("PROXY_URL")


    session = cloudscraper.create_scraper(
            browser={'custom': ua.random}, delay=random.uniform(1, 2))
    
    with session:
        session.headers.update({
            "User-Agent": ua.random
        })

        if proxy:
            session.proxies.update({
                "http": proxy,
                "https": proxy
            })

        time.sleep(2)
        response = session.get(url=link)
        html = response.text.lower()

        if "var p=" in html:
            headers = solve_math_challenge(html)

        elif 'cloudflare' in html:
            headers = handle_cloudflare_challenge()

        elif 'turnstile' in html:
            headers = handle_turnstile_challenge()

        else:
            raise Exception(f"Strange html, we don't know such challenge: {html}")

        if headers:
            for name, value in headers.items():
                session.cookies.set(name, value, domain='opencorporates.com')

        session.headers.update(headers)

        session.headers.update({
        'Accept-Encoding': 'gzip',
        'Accept': 'application/x-gzip, application/gzip, application/octet-stream'
        })

        time.sleep(2)

        response = session.get(url=link, timeout=30)
        if response.content.startswith(b'\x1f\x8b'):
            result = process_gzip(response.content)

            if "xmls" in result:
                    return result  
            
            elif "urls" in result:
                filtered = [link for link in result["urls"] if "/companies/us_" in link]
                client = await get_temporal_client()

                handle = client.get_workflow_handle(workflow_id, run_id=run_id)

                await handle.signal("add_links", len(filtered))

            else:
                return "unknown"
        else:
            raise Exception("We didn't get gzip, probably failed challenge")
        