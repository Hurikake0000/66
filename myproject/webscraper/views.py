import json
import re
from collections import Counter
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from bs4 import BeautifulSoup
import requests
from .models import CrawledData
from .app import start_crawling, stop_crawling_task
import math
from urllib.parse import urlparse
from django.core.paginator import Paginator

crawling_active = False

def index(request):
    return render(request, 'webscraper/index.html')

@csrf_exempt
def start_crawling_view(request):
    if request.method == "POST":
        data = json.loads(request.body)
        url = data.get('url')
        keywords = data.get('keywords', [])

        global crawling_active
        crawling_active = True

        for keyword in keywords:
            start_crawling(url, keyword)

        return JsonResponse({"status": "started"})

@csrf_exempt
def stop_crawling_view(request):
    if request.method == "POST":
        global crawling_active
        crawling_active = False

        stop_crawling_task()

        return JsonResponse({"status": "stopped"})

def notifications(request):
    return render(request, 'webscraper/notifications.html')

def crawling_status(request):
    global crawling_active
    status = "running" if crawling_active else "completed"
    return JsonResponse({"status": status})

@csrf_exempt
def clear_database_view(request):
    if request.method == 'POST':
        CrawledData.objects.all().delete()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'failed'})

def check_updates(request):
    new_data = CrawledData.objects.filter(is_new=True)
    new_data_found = new_data.exists()
    if (new_data_found):
        new_data.update(is_new=False)
    return JsonResponse({"new_data_found": new_data_found})

def preprocess_text(text):
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'[^\w\s가-힣]', '', text)
    return text.lower()

def extract_noun_phrases(text):
    return re.findall(r'\b([가-힣]{2,}(\s[가-힣]{2,})?)\b', text)

def calculate_tfidf(documents):
    word_count = Counter()
    doc_count = Counter()
    for doc in documents:
        words = set(doc)
        for word in words:
            doc_count[word] += 1
        word_count.update(doc)
    
    total_docs = len(documents)
    tfidf = {}
    for word, count in word_count.items():
        tf = count / sum(word_count.values())
        idf = math.log(total_docs / (doc_count[word] + 1))
        tfidf[word] = tf * idf
    return tfidf

@csrf_exempt
def recommend_keywords(request):
    if request.method == "POST":
        data = json.loads(request.body)
        url = data.get('url')

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            return JsonResponse({"status": "failed", "error": str(e)})

        soup = BeautifulSoup(response.text, 'html.parser')

        meta_keywords = soup.find("meta", attrs={"name": "keywords"})
        meta_keywords = meta_keywords["content"].split(",") if meta_keywords else []

        title_keywords = extract_noun_phrases(soup.title.string) if soup.title else []

        text = ' '.join(soup.stripped_strings)
        text = preprocess_text(text)
        
        noun_phrases = extract_noun_phrases(text)
        
        stopwords = set(['것', '등', '및', '이', '그', '또', '수', '더', '한', '을', '를', '에', '의', '로', '도'])
        filtered_words = [word for word in noun_phrases if word not in stopwords]

        sentences = re.split(r'[.!?]\s', text)
        documents = [extract_noun_phrases(sentence) for sentence in sentences]

        tfidf_scores = calculate_tfidf(documents)
    
        domain = urlparse(url).netloc

        for word, score in tfidf_scores.items():
            word_str = word[0] if isinstance(word, tuple) else word
            
            if word_str in title_keywords:
                tfidf_scores[word] *= 1.5
            
            if word_str in meta_keywords:
                tfidf_scores[word] *= 1.3
            
            if word_str in domain:
                tfidf_scores[word] *= 1.2

        top_keywords = sorted(tfidf_scores.items(), key=lambda x: x[1], reverse=True)[:10]
        keywords = [word[0] if isinstance(word, tuple) else word for word, _ in top_keywords]

        return JsonResponse({"status": "success", "keywords": keywords})

    return JsonResponse({"status": "failed", "error": "Invalid request method"})


def toggle_data_view(request):
    show_data = request.session.get('show_data', False)
    request.session['show_data'] = not show_data
    return JsonResponse({'show_data': not show_data})


def get_crawled_data(request):
    page_number = request.GET.get('page', 1)
    items_per_page = 10

    all_data = CrawledData.objects.all().order_by('-timestamp')
    paginator = Paginator(all_data, items_per_page)
    page_obj = paginator.get_page(page_number)

    data = [{'url': item.url, 'keyword': item.keyword, 'data': item.data, 'timestamp': item.timestamp.strftime('%Y-%m-%d %H:%M:%S')} for item in page_obj]
    
    return JsonResponse({
        'data': data,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'total_pages': paginator.num_pages,
        'current_page': page_obj.number
    })