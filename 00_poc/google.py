from GoogleNews import GoogleNews

def fetch_news(query, pages=10):
    googlenews = GoogleNews(lang='cn', region='CN')
    googlenews.set_period('1d')
    googlenews.set_encode('utf-8')

    all_results = []
    seen = set()

    for page in range(1, pages + 1):  # each page usually gives ~10 results
        googlenews.search(query)
        googlenews.getpage(page)
        results = googlenews.results()
        for news in results:
            title = news['title']
            link = news['link']

            # remove redundant by title + link
            key = (title.strip(), link)
            if key not in seen:
                seen.add(key)
                all_results.append(news)

    return all_results

# Example: fetch ~100 news results about China stock market
news_list = fetch_news("中国股票市场", pages=10)

print(f"Fetched {len(news_list)} unique results")
for i, news in enumerate(news_list, 1):
    print(f"{i}. {news['title']}")
    print(f"   {news['media']} | {news['date']}")
    print(f"   {news['link']}\n")
