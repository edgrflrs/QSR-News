import feedparser
import logging
import re
import string
import streamlit as st
from dateutil import parser as date_parser
import pandas as pd  # Import pandas

# Setup logging (Streamlit also has logging capabilities)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Expanded RSS feed list
RSS_FEEDS = [
    "https://www.adweek.com/feed/",
    "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
    "https://www.fastcasual.com/rss/",
    "https://www.qsrmagazine.com/feed/",
    "https://www.nrn.com/rss.xml",  # Nation's Restaurant News
    "https://www.restaurantbusinessonline.com/rss.xml",  # Restaurant Business Online
    "https://www.foodbusinessnews.net/rss/articles",  # Food Business News
    "https://www.technomic.com/rss.xml"  # Technomic
]

# Updated keyword list
KEYWORDS = [
    "Inspire Brands", "Dunkin", "Sonic", "Buffalo Wild Wings", "BWW", "Jimmy John's",
    "Arby's", "Baskin-Robbins", "McDonald's", "McDonalds", "McD", "Burger King", "KFC", "Wingstop",
    "Starbucks", "Chipotle", "Taco Bell", "Popeyes", "Wendy's", "Chick-fil-A", "Panera",
    "Plant-based", "Vegan fast food", "Lab-grown meat", "Functional food", "Mood-boosting food",
    "Spicy", "Sustainable packaging", "Zero-waste", "Ethical sourcing", "Ghost kitchens",
    "Virtual restaurants", "AI drive-thru", "Mobile ordering", "Contactless payment", "Personalized menu",
    "Digital loyalty", "Foodtainment", "Pop culture menu", "Secret menu hack",
    "Fine dining fast food", "Drinks-only locations", "Korean fried chicken", "Mexican street food",
    "Southeast Asian flavors", "Global fusion", "International QSR", "Spicy", "consumer confidence", "consumer spending", "GenZ", "culture trends", "consumer preferences", "Marketing strategies", "Brand loyalty", "Customer experience", "Digital transformation", "Sustainability", "Health trends", "Economic impact"
]

# Precompile regex patterns for keywords
KEYWORD_PATTERNS = [re.compile(r'\b' + re.escape(kw.lower()) + r'\b') for kw in KEYWORDS]

def normalize_text(text):
    """Lowercase and remove punctuation from text."""
    return text.lower().translate(str.maketrans('', '', string.punctuation))

def tag_keywords(article, keyword_patterns, original_keywords):
    """Tag article with matching keywords using regex."""
    content = normalize_text(article["title"] + " " + article["summary"])
    matched = []
    for pattern, original_kw in zip(keyword_patterns, original_keywords):
        if pattern.search(content):
            matched.append(original_kw)
    return matched

@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_rss_entries(feeds):
    """Fetch articles from selected RSS feeds."""
    all_entries = []
    for feed_url in feeds:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                article_info = {
                    "title": entry.title,
                    "link": entry.link,
                    "summary": entry.get("summary", ""),
                    "published": entry.get("published", ""),
                }
                all_entries.append(article_info)
        except Exception as e:
            logging.warning(f"Error fetching {feed_url}: {e}")
            st.error(f"Error fetching {feed_url}: {e}")  # Display error in Streamlit
    return all_entries

@st.cache_data(ttl=3600)
def process_rss_feeds(selected_feeds, selected_keyword_patterns, selected_keywords):
    entries = fetch_rss_entries(selected_feeds)
    logging.info(f"Fetched {len(entries)} articles.")
    results = []
    for article in entries:
        tags = tag_keywords(article, selected_keyword_patterns, selected_keywords)
        if tags:
            try:
                published_date = date_parser.parse(article['published']).strftime('%Y-%m-%d')
            except Exception:
                published_date = "Unknown Date"

            results.append({
                "Title": article['title'],
                "Date": published_date,
                "Link": article['link'],
                "Keywords": ", ".join(tags),
                "Summary": article['summary']  # Add summary to the results
            })
    return results


# Streamlit App
st.title("Inspire RSS Digest")

# Sidebar for customization
selected_keywords = st.sidebar.multiselect("Select Keywords", KEYWORDS, default=KEYWORDS)
selected_feeds = st.sidebar.multiselect("Select RSS Feeds", RSS_FEEDS, default=RSS_FEEDS)

# Process RSS Feeds Button
if st.button("What's the Scoop?"):
    # Filter keyword patterns based on selected keywords
    selected_keyword_patterns = [
        pattern for pattern, keyword in zip(KEYWORD_PATTERNS, KEYWORDS) if keyword in selected_keywords
    ]

    # Run the analysis
    with st.spinner("Processing RSS Feeds..."):
        results = process_rss_feeds(selected_feeds, selected_keyword_patterns, selected_keywords)

    # Display results in a table
    if results:
        st.write("### Matching Articles")
        df = pd.DataFrame(results)

        st.dataframe(
            df,
            column_config={
                "Link": st.column_config.LinkColumn("Article Link"),
                "Title": st.column_config.Column(width="medium"),
                "Date": st.column_config.Column(width="small"),
                "Keywords": st.column_config.Column(width="medium"),
                "Summary": st.column_config.Column(width="large"),
            },
            use_container_width=True
        )

        # Expandable article summaries (below the table)
        st.write("### Article Summaries")
        for result in results:
            with st.expander(f"{result['Title']} ({result['Date']})"):
                st.write(result['Summary'])
    else:
        st.write("No matching articles found.")
