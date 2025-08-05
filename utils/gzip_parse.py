import io
import xml.etree.ElementTree as ET
import gzip

def process_gzip(content):
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(content)) as gz:
            xml_data = gz.read()
        root = ET.fromstring(xml_data)
        if root.tag.endswith('sitemapindex'):
            sitemap_urls = [elem.text for elem in root.iter() if elem.tag.endswith('loc')]

            result = {'type': 'index', 'sitemaps': sitemap_urls}
        
        elif root.tag.endswith('urlset'):
            urls = [elem.text for elem in root.iter() if elem.tag.endswith('loc')]
            result = {'type': 'urlset', 'urls': urls}
        else:
            result = {'type': 'unknown', 'tag': root.tag}
        

        if result:
            if result.get('type') == 'index':
                unique_sitemaps = list(set(result['sitemaps']))

                return {"xmls":unique_sitemaps}
            
            elif result.get('type') == 'urlset':
                unique_urls = list(set(result['urls']))
                return {"urls":unique_urls}
            
            else:
                print(f"\nUnknown sitemap structure: {result.get('tag')}")
        else:
            print("\nFailed to get sitemap")
    except Exception as e:

        print(f"Failed to parse gzip: {e}")
        return None
