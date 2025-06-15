import pandas as pd
import numpy as np
import requests
import os
import time
import re
from sklearn.metrics.pairwise import cosine_similarity

# Gemini API key (use environment variables in production)
API_KEY = "AIzaSyAIu8sBTvcURlDf1dAPs8sIo1CmXc2fnz0"
EMBEDDING_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent"

def cute_print(message, emoji="✨"):
    """Print messages with cute emojis"""
    print(f"{emoji} {message} {emoji}")

def load_books_data():
    """Load and validate books data from CSV"""
    try:
        # Try to load from the provided CSV structure
        books_df = pd.read_csv("books.csv")
        print(f"📊 Loaded CSV with {len(books_df)} books")
        
        # Map column names to standardized format
        column_mapping = {
            'title': 'Book Name',
            'author': 'Author Name', 
            'rating': 'Rating',
            'description': 'Description',
            'genres': 'Genre'
        }
        
        # Rename columns if they exist
        for old_name, new_name in column_mapping.items():
            if old_name in books_df.columns:
                books_df = books_df.rename(columns={old_name: new_name})
        
        # Clean and validate data
        books_df['Book Name'] = books_df['Book Name'].fillna('Unknown Title')
        books_df['Author Name'] = books_df['Author Name'].fillna('Unknown Author')
        books_df['Genre'] = books_df['Genre'].fillna('Fiction')
        books_df['Description'] = books_df['Description'].fillna('No description available')
        books_df['Rating'] = pd.to_numeric(books_df['Rating'], errors='coerce').fillna(4.0)
        
        # Add missing columns with defaults
        if 'Length' not in books_df.columns:
            books_df['Length'] = 300  # Default page count
        else:
            books_df['Length'] = pd.to_numeric(books_df['Length'], errors='coerce').fillna(300)
            
        if 'Release Year' not in books_df.columns:
            books_df['Release Year'] = 2000  # Default year
        else:
            books_df['Release Year'] = pd.to_numeric(books_df['Release Year'], errors='coerce').fillna(2000)
        
        cute_print(f"Successfully loaded {len(books_df)} books!", "📚")
        return books_df
        
    except FileNotFoundError:
        cute_print("Couldn't find books.csv. Please make sure the file exists!", "📄")
        exit()
    except Exception as e:
        cute_print(f"Error loading data: {str(e)}", "😔")
        exit()

def get_single_embedding(text, max_retries=3):
    """Get embedding for a single text using Gemini API"""
    if not text or not str(text).strip():
        return None
    
    headers = {"Content-Type": "application/json"}
    
    # Clean and prepare text
    clean_text = str(text)[:1500].replace('\n', ' ').strip()
    
    payload = {
        "model": "models/text-embedding-004",
        "content": {"parts": [{"text": clean_text}]}
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{EMBEDDING_ENDPOINT}?key={API_KEY}", 
                headers=headers, 
                json=payload, 
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                if "embedding" in result and "values" in result["embedding"]:
                    return np.array(result["embedding"]["values"])
                else:
                    return None
                
            else:
                if attempt == 0:  # Only show error on first attempt
                    print(f"⚠️ API Error {response.status_code}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    
        except requests.exceptions.RequestException as e:
            if attempt == 0:
                print(f"⚠️ Network Error: {e}")
            if attempt < max_retries - 1:
                time.sleep(1)
    
    return None

def generate_or_load_embeddings(books_df, max_books=1000):
    """Generate embeddings or load from cache - limit to reasonable number for demo"""
    cache_file = "book_embeddings.npy"
    
    # Limit dataset size for practical usage
    if len(books_df) > max_books:
        cute_print(f"Dataset has {len(books_df)} books. Using top {max_books} highest-rated books for faster processing...", "⚡")
        books_df = books_df.nlargest(max_books, 'Rating').reset_index(drop=True)
    
    # Try to load cached embeddings
    if os.path.exists(cache_file):
        try:
            cute_print("Loading cached embeddings...", "📂")
            cached_data = np.load(cache_file, allow_pickle=True)
            if len(cached_data) == len(books_df):
                books_df = books_df.copy()
                books_df["embedding"] = cached_data.tolist()
                cute_print("Cached embeddings loaded successfully!", "✅")
                return books_df
        except Exception as e:
            print(f"⚠️ Error loading cache: {e}")
    
    cute_print(f"Generating embeddings for {len(books_df)} books using Gemini...", "🤖")
    embeddings = []
    
    # Create comprehensive text descriptions for each book
    book_texts = []
    for _, row in books_df.iterrows():
        # Create concise but informative description
        text_parts = [
            f"Title: {row['Book Name']}",
            f"Author: {row['Author Name']}", 
            f"Genre: {row['Genre']}",
            f"Description: {str(row['Description'])[:300]}..."  # Limit description length
        ]
        book_text = " | ".join(text_parts)
        book_texts.append(book_text)
    
    # Process with progress updates every 50 books
    success_count = 0
    for idx, book_text in enumerate(book_texts):
        if idx % 50 == 0 or idx < 10:
            print(f"🔄 Processing book {idx + 1}/{len(books_df)}...")
        
        embedding = get_single_embedding(book_text)
        embeddings.append(embedding)
        
        if embedding is not None:
            success_count += 1
        
        # Very short delay to avoid overwhelming the API
        time.sleep(0.1)
        
        # Show progress every 100 books
        if (idx + 1) % 100 == 0:
            cute_print(f"Progress: {idx + 1}/{len(books_df)} ({success_count} successful)", "📊")
    
    # Add embeddings to dataframe
    books_df = books_df.copy()
    books_df["embedding"] = embeddings
    
    # Save to cache
    try:
        np.save(cache_file, np.array(embeddings, dtype=object))
        cute_print("Embeddings saved to cache!", "💾")
    except Exception as e:
        print(f"⚠️ Error saving embeddings: {e}")
    
    # Remove books without valid embeddings
    valid_embeddings = books_df['embedding'].notna()
    books_df = books_df[valid_embeddings].reset_index(drop=True)
    
    cute_print(f"Ready with {len(books_df)} books with embeddings!", "🎉")
    return books_df

def extract_query_info(query):
    """Enhanced query parsing to understand user intent"""
    query_lower = query.lower()
    
    # Extract number of recommendations
    num_books = 10  # default
    number_patterns = [
        r'top\s+(\d+)',
        r'give\s+me\s+(\d+)',
        r'show\s+me\s+(\d+)', 
        r'(\d+)\s+books?',
        r'best\s+(\d+)',
        r'find\s+(\d+)',
        r'recommend\s+(\d+)'
    ]
    
    for pattern in number_patterns:
        match = re.search(pattern, query_lower)
        if match:
            num_books = min(int(match.group(1)), 20)  # Cap at 20
            break
    
    # Check for genre-specific requests
    genre_keywords = {
        'comedy': ['comedy', 'funny', 'humor', 'humorous', 'comic'],
        'romance': ['romance', 'romantic', 'love', 'dating'],
        'mystery': ['mystery', 'detective', 'crime', 'murder', 'thriller'],
        'fantasy': ['fantasy', 'magic', 'magical', 'wizard', 'dragon'],
        'sci-fi': ['sci-fi', 'science fiction', 'space', 'future', 'alien'],
        'horror': ['horror', 'scary', 'frightening', 'ghost', 'vampire'],
        'drama': ['drama', 'dramatic', 'emotional'],
        'adventure': ['adventure', 'quest', 'journey', 'exploration']
    }
    
    detected_genres = []
    for genre, keywords in genre_keywords.items():
        if any(keyword in query_lower for keyword in keywords):
            detected_genres.append(genre)
    
    # Check for rating preferences
    rating_filter = None
    if any(phrase in query_lower for phrase in ['highly rated', 'best rated', 'top rated', 'high rating', 'popular']):
        rating_filter = 4.0
    elif any(phrase in query_lower for phrase in ['good rating', 'well rated']):
        rating_filter = 3.5
    
    return {
        'num_books': num_books,
        'detected_genres': detected_genres,
        'rating_filter': rating_filter,
        'original_query': query
    }

def find_similar_books(books_df, user_query, num_recommendations=10):
    """Find books similar to user query using embeddings"""
    query_info = extract_query_info(user_query)
    num_books = query_info['num_books']
    
    cute_print(f"Searching for {num_books} books matching your preferences...", "🔍")
    
    # Get embedding for user query
    user_embedding = get_single_embedding(user_query)
    if user_embedding is None:
        cute_print("Failed to process your query. Please try again!", "😔")
        return pd.DataFrame()
    
    # Start with all books
    filtered_books = books_df.copy()
    
    # Apply rating filter if detected
    if query_info['rating_filter']:
        initial_count = len(filtered_books)
        filtered_books = filtered_books[filtered_books['Rating'] >= query_info['rating_filter']]
        print(f"🌟 Filtered to {len(filtered_books)} highly rated books (rating >= {query_info['rating_filter']})")
    
    # Apply genre filter if specific genres detected
    if query_info['detected_genres']:
        genre_pattern = '|'.join(query_info['detected_genres'])
        genre_mask = filtered_books['Genre'].str.contains(genre_pattern, case=False, na=False)
        if genre_mask.any():
            filtered_books = filtered_books[genre_mask]
            print(f"🏷️ Filtered to {len(filtered_books)} books in genres: {', '.join(query_info['detected_genres'])}")
    
    if filtered_books.empty:
        cute_print("No books match your specific filters. Showing general recommendations!", "🔄")
        filtered_books = books_df.copy()
    
    # Calculate similarity scores
    similarities = []
    for _, row in filtered_books.iterrows():
        if row['embedding'] is not None:
            try:
                similarity = cosine_similarity([user_embedding], [row['embedding']])[0][0]
                similarities.append(similarity)
            except:
                similarities.append(0)
        else:
            similarities.append(0)
    
    filtered_books = filtered_books.copy()
    filtered_books['similarity_score'] = similarities
    
    # Sort by similarity and return top results
    recommendations = filtered_books.sort_values('similarity_score', ascending=False).head(num_books)
    
    return recommendations

def display_recommendations(recommendations, user_query):
    """Display book recommendations in a beautiful format"""
    if recommendations.empty:
        cute_print("Hmm, couldn't find perfect matches! Try a different query? 🤔", "😅")
        print("\n💡 Try queries like:")
        print("   • 'I like books with murder and magic'")
        print("   • 'top 5 comedy books'") 
        print("   • 'fantasy books with dragons'")
        print("   • 'highly rated romance novels'")
        return
    
    num_books = len(recommendations)
    cute_print(f"Found {num_books} great recommendations for: '{user_query}'", "🎯")
    print("\n" + "="*80)
    
    for idx, (_, book) in enumerate(recommendations.iterrows(), 1):
        match_score = int(book.get('similarity_score', 0) * 100)
        
        print(f"\n📖 #{idx}: {book['Book Name']}")
        print(f"   ✍️ Author: {book['Author Name']}")
        print(f"   ⭐ Rating: {book['Rating']:.1f}/5")
        print(f"   🏷️ Genre: {book['Genre']}")
        
        # Show description with word limit
        desc = str(book['Description'])
        if len(desc) > 200:
            desc = desc[:200] + "..."
        print(f"   📝 Description: {desc}")
        print(f"   🎯 Match Score: {match_score}%")
        print("   " + "-"*70)

def show_collection_stats(books_df):
    """Show interesting statistics about the book collection"""
    cute_print("📊 Your Book Collection Statistics", "📈")
    print(f"\n📚 Total Books: {len(books_df)}")
    print(f"✍️ Unique Authors: {books_df['Author Name'].nunique()}")
    print(f"⭐ Average Rating: {books_df['Rating'].mean():.2f}/5")
    
    print(f"\n🏆 Top Genres:")
    # Handle multiple genres in single field
    all_genres = []
    for genres in books_df['Genre'].dropna():
        genre_list = [g.strip() for g in str(genres).split(',')]
        all_genres.extend(genre_list)
    
    from collections import Counter
    genre_counts = Counter(all_genres)
    for genre, count in genre_counts.most_common(5):
        print(f"   {genre}: {count} books")
    
    print(f"\n⭐ Highest Rated Books:")
    top_rated = books_df.nlargest(3, 'Rating')[['Book Name', 'Author Name', 'Rating']]
    for _, book in top_rated.iterrows():
        print(f"   • {book['Book Name']} by {book['Author Name']} - {book['Rating']:.1f}⭐")

def interactive_chat():
    """Main interactive chat interface"""
    cute_print("Welcome to Mamgo's AI-Powered Book Recommender! 🤖📚", "🎉")
    
    print("\n⚡ QUICK SETUP OPTIONS:")
    print("1. Full dataset (13k+ books) - Will take 30+ minutes to process")
    print("2. Top 1000 books (recommended) - Takes 3-5 minutes")
    print("3. Top 500 books (quick demo) - Takes 1-2 minutes")
    print("4. Use cached embeddings (instant if available)")
    
    while True:
        choice = input("\nChoose option (1-4) or press Enter for option 2: ").strip()
        if choice == "1":
            max_books = None
            break
        elif choice == "3":
            max_books = 500
            break
        elif choice == "4":
            max_books = 0  # Will try cache only
            break
        else:  # Default option 2
            max_books = 1000
            break
    
    cute_print("Loading your book collection...", "🔄")
    
    # Load and prepare data
    books_df = load_books_data()
    
    if max_books == 0:
        # Try cache only
        cache_file = "book_embeddings.npy"
        if os.path.exists(cache_file):
            try:
                cached_data = np.load(cache_file, allow_pickle=True)
                books_df = books_df.head(len(cached_data)).copy()
                books_df["embedding"] = cached_data.tolist()
                cute_print("Using cached embeddings!", "✅")
            except:
                cute_print("Cache loading failed. Using top 500 books instead.", "⚠️")
                max_books = 500
        else:
            cute_print("No cache found. Using top 500 books instead.", "⚠️") 
            max_books = 500
    
    if max_books != 0:
        books_df = generate_or_load_embeddings(books_df, max_books or len(books_df))
    
    if books_df.empty:
        cute_print("No books available for recommendations!", "😔")
        return
    
    cute_print("I'm ready to help you discover amazing books!", "🤖")
    print("\n" + "="*70)
    print("💬 WHAT I CAN DO:")
    print("   📖 Find books: 'I like books with murder and magic'")
    print("   🔢 Get top books: 'top 10 comedy books', 'best 5 fantasy novels'")
    print("   🏷️ Search genres: 'romance books', 'sci-fi adventures'")  
    print("   ⭐ Find popular: 'highly rated mystery books'")
    print("   📊 Show stats: type 'stats'")
    print("   🚪 Exit: type 'quit' or 'exit'")
    print("="*70)
    
    while True:
        try:
            print("\n" + "🗣️" + "="*68)
            user_input = input("What kind of books are you looking for? ").strip()
            
            if not user_input:
                cute_print("Please tell me what you're looking for!", "😊")
                continue
            
            user_input_lower = user_input.lower()
            
            # Handle exit commands
            if user_input_lower in ['quit', 'exit', 'bye', 'q', 'stop']:
                cute_print("Happy reading! Thanks for using the book recommender!", "👋")
                break
            
            # Handle stats command
            if user_input_lower in ['stats', 'statistics', 'info', 'collection']:
                show_collection_stats(books_df)
                continue
            
            # Handle help command
            if user_input_lower in ['help', '?']:
                print("\n💡 Examples of what you can ask:")
                print("   • 'I want books with magic and adventure'")
                print("   • 'top 7 romance books'")
                print("   • 'mystery books with high ratings'")
                print("   • 'funny books about relationships'")
                continue
            
            # Process book recommendation request
            recommendations = find_similar_books(books_df, user_input)
            display_recommendations(recommendations, user_input)
            
        except KeyboardInterrupt:
            cute_print("\nThanks for using the book recommender! Goodbye!", "👋")
            break
        except Exception as e:
            print(f"😅 Oops! Something went wrong: {str(e)}")
            cute_print("Let's try again!", "🔄")

if __name__ == "__main__":
    interactive_chat()