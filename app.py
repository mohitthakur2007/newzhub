from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
import requests
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/newsx'  # Adjust MySQL connection string as needed
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define SQLAlchemy model for subscriptions
class Subscription(db.Model):
    __tablename__ = 'subscription'  # Explicitly define table name
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f'<Subscription {self.email}>'

def get_news(api_key, country='in', category='general', page_size=30):
    url = 'https://newsapi.org/v2/top-headlines'
    params = {'apiKey': api_key, 'country': country, 'category': category, 'pageSize': page_size}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        news_data = response.json()
        articles = news_data.get('articles', [])
        return articles
    except requests.exceptions.RequestException as e:
        print(f"Error fetching news: {e}")
        return None

def truncate_text(text, word_limit=20):
    if not text:
        return ''  # Return an empty string if the text is None
    words = text.split()
    if len(words) > word_limit:
        return ' '.join(words[:word_limit]) + '...'
    return text

@app.route('/', methods=['GET', 'POST'])
def index():
    api_key = '32dcd016c35c4449a829fa2923c2ba51'  # Replace with your NewsAPI key
    
    categories = ['business', 'entertainment', 'general', 'health', 'science', 'sports', 'technology']
    country = 'in'
    page_size = 30  # Adjust the page size as needed
    
    if request.method == 'POST':
        category = request.form.get('category', 'general')
    else:
        category = 'general'
    
    try:
        # Get selected news
        news = get_news(api_key, country, category, page_size)
        
        # Get trending news (using the same category)
        trending_news = get_news(api_key, country, category, page_size)  # Adjust as needed for actual trending news fetching
        
        if news is not None:
            # Shuffle and select a subset of articles to display
            random.shuffle(news)
            selected_news = [{
                'title': article['title'],
                'description': truncate_text(article.get('description', ''), 30),
                'url': article['url'],
                'image_url': article.get('urlToImage', '')  # Add image URL if available
            } for article in news[:30]]  # Display 30 random articles
            
            if trending_news is not None:
                trending_news = [{
                    'title': article['title'],
                    'description': truncate_text(article.get('description', ''), 20),
                    'url': article['url'],
                    'image_url': article.get('urlToImage', '')  # Add image URL if available
                } for article in trending_news[:20]]  # Display 20 trending articles
            
            return render_template('index.html', news=selected_news, trending_news=trending_news, country=country, category=category, categories=categories)
        else:
            return render_template('index.html', error='Error fetching news. Please try again.', categories=categories)
    except Exception as e:
        return render_template('index.html', error=f'An error occurred: {e}', categories=categories)

@app.route('/subscribe', methods=['POST'])
def subscribe():
    if request.method == 'POST':
        email = request.form.get('email')
        if email:
            new_subscription = Subscription(email=email)
            try:
                db.session.add(new_subscription)
                db.session.commit()
                return render_template('index.html', message='Subscription successful!')
            except Exception as e:
                db.session.rollback()
                return render_template('index.html', error=f'Error subscribing: {e}')
        else:
            return render_template('index.html', error='Email cannot be empty!')
    else:
        return render_template('index.html', error='Method not allowed.')

if __name__ == "__main__":
    app.run(debug=True)
