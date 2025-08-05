import re
import cloudscraper
import base64
import hashlib
import random
import time
import gzip
import xml.etree.ElementTree as ET
from fake_useragent import UserAgent
from temporalio import activity
from temporalio import activity

import io
import re
import cloudscraper
import random
import time
import gzip
import xml.etree.ElementTree as ET
from fake_useragent import UserAgent
from temporalio import activity

from utils.challenges import solve_math_challenge, handle_cloudflare_challenge, handle_turnstile_challenge
from utils.gzip_parse import process_gzip

import io

from client import get_temporal_client

ua = UserAgent()


@activity.defn(name="fetch_and_parse_gz_xml")
async def fetch_and_parse_gz_xml(input: dict):

    workflow_id = input["workflow_id"]
    run_id = input["run_id"]
    link = input["link"]
    session = cloudscraper.create_scraper(
            browser={'custom': ua.random}, delay=random.uniform(1, 2))
    
    with session:
        session.headers.update({
            "User-Agent": ua.random
        })
        time.sleep(2)
        response = session.get(url=link)
        html = response.text

        if "var p=" in html.lower():
            headers = solve_math_challenge(html)
        elif 'cloudflare' in html.lower():
            headers = handle_cloudflare_challenge()
        elif 'turnstile' in html.lower():
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
        