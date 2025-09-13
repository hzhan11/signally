import time
import uuid

from GoogleNews import GoogleNews

from chromadb import HttpClient
client = HttpClient(host="localhost", port=8001)
sc = client.get_or_create_collection("info")

googlenews = GoogleNews(lang='cn', region='CHINA')
googlenews.search('比亚迪')
googlenews.set_period('12h')

# Get the results from the first page
results = googlenews.result()

# Loop through additional pages (e.g., pages 2, 3, and 4)
for page_number in range(1, 3):
    googlenews.get_page(page_number)
    results.extend(googlenews.result())

count = 0
target = 0
# Process the combined results from all pages
for item in results:
    print(f"Title: {item['title']}")
    print(f"Date: {item['date']}")
    print(f"Link: {item['link']}")
    print(f"Desc: {item['desc']}")
    print(f"Media: {item['media']}")

    metadata = {
        "id": str(uuid.uuid4()),
        "attached_stock_id": "002594",
        "datetime": item['date'],
        "type": "news",
        "title": item['title']
    }

    sc.upsert(
        ids=[metadata["id"]],
        documents=[item['title']+""+item['desc']],
        metadatas=[metadata]
    )