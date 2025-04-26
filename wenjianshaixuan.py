import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from fake_useragent import UserAgent

def get_random_user_agent():
    ua = UserAgent()
    return ua.random

def get_pubmed_abstract(pubmed_id):
    """
    Fetch the abstract of a PubMed article using its ID.
    Args:
        pubmed_id (str): The PubMed ID of the article
    Returns:
        str: The abstract of the article, or None if not found
    """
    try:
        # PubMed article URL
        article_url = f"https://pubmed.ncbi.nlm.nih.gov/{pubmed_id}/"
        headers = {
            'User-Agent': get_random_user_agent()
        }
        # Get the article page
        response = requests.get(article_url, headers=headers)
        response.raise_for_status()
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        # Try to find the abstract
        abstract = None
        # Method 1: Look for the abstract section
        abstract_section = soup.find('div', {'class': 'abstract'})
        if abstract_section:
            abstract = abstract_section.get_text().strip()
        # Method 2: Look for meta description
        if not abstract:
            meta_desc = soup.find('meta', {'name': 'description'})
            if meta_desc:
                abstract = meta_desc.get('content', '').strip()
        # Method 3: Look for citation_abstract
        if not abstract:
            citation_abstract = soup.find('meta', {'name': 'citation_abstract'})
            if citation_abstract:
                abstract = citation_abstract.get('content', '').strip()
        # If we still don't have an abstract, try to find any text that looks like an abstract
        if not abstract:
            for p in soup.find_all('p'):
                text = p.get_text().strip()
                if len(text) > 100 and ('abstract' in p.get('class', []) or 'abstract' in p.get('id', '')):
                    abstract = text
                    break
        return abstract
    except Exception as e:
        return f"Error fetching PubMed article: {e}"

def analyze_words_in_abstract(abstract, words_to_find):
    """
    Analyze the abstract for specific words and their context.
    Args:
        abstract (str): The abstract text
        words_to_find (list): List of words to search for
    Returns:
        dict: Dictionary containing word counts and sentences
    """
    if not abstract:
        return None
    
    # Convert abstract to lowercase for case-insensitive search
    abstract_lower = abstract.lower()
    
    # Split abstract into sentences
    sentences = re.split(r'(?<=[.!?])\s+', abstract)
    
    # Initialize results dictionary
    results = {}
    
    for word in words_to_find:
        word = word.lower()
        # Count occurrences
        count = abstract_lower.count(word)
        
        # Find sentences containing the word
        containing_sentences = []
        for sentence in sentences:
            if word in sentence.lower():
                containing_sentences.append(sentence.strip())
        
        results[word] = {
            'count': count,
            'sentences': containing_sentences
        }
    
    return results

st.title("PubMed Abstract Analyzer")

pubmed_ids_input = st.text_area("Enter PubMed IDs (one per line):")
words_input = st.text_input("Enter words to search for (comma-separated):")

if st.button("Analyze"):
    pubmed_ids = [pid.strip() for pid in pubmed_ids_input.strip().split('\n') if pid.strip()]
    words_to_find = [w.strip() for w in words_input.split(',') if w.strip()]
    for pubmed_id in pubmed_ids:
        st.subheader(f"PubMed ID: {pubmed_id}")
        abstract = get_pubmed_abstract(pubmed_id)
        if abstract and not abstract.startswith("Error"):
            # Show abstract as a scrollable, multi-line box (no extra line breaks)
            st.text_area("Abstract", abstract, height=200)
            results = analyze_words_in_abstract(abstract, words_to_find)
            if results:
                for word, data in results.items():
                    st.markdown(f"**Word:** `{word}`  \nCount: {data['count']}")
                    if data['sentences']:
                        st.markdown("Sentences containing the word:")
                        for i, sentence in enumerate(data['sentences'], 1):
                            st.markdown(f"{i}. {sentence}")
                    else:
                        st.markdown("No sentences found with this word.")
            else:
                st.warning("Could not analyze words in abstract.")
        else:
            st.error(f"Could not find the abstract for PubMed ID {pubmed_id}.\n{abstract if abstract else ''}")

