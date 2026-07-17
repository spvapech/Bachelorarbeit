"""
Topic Rating Analysis Service
Combines LDA topic modeling with sentiment analysis and star ratings from database.
"""

from typing import List, Dict, Any, Optional
from models.lda_topic_model import LDATopicAnalyzer
from models.sentiment_analyzer import SentimentAnalyzer
from services.topic_model_service import TopicModelDatabase


class TopicRatingAnalyzer:
    """
    Service that combines topic modeling, sentiment analysis, and star ratings.
    """
    
    def __init__(self):
        self.db = TopicModelDatabase()
        # Use transformer mode for accurate rating analysis
        self.sentiment_analyzer = SentimentAnalyzer(mode="transformer")
        
    def analyze_employee_reviews_with_ratings(
        self, 
        lda_model: LDATopicAnalyzer,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Analyze employee reviews combining topics, sentiment, and star ratings.
        
        Args:
            lda_model: Trained LDA model
            limit: Maximum number of reviews to analyze
            
        Returns:
            Comprehensive analysis with topics, sentiment, and ratings
        """
        # Fetch employee data with all fields
        query = self.db.supabase.table('employee').select('*')
        if limit:
            query = query.limit(limit)
        
        response = query.execute()
        reviews = response.data
        
        # Rating fields mapping
        rating_fields = {
            'arbeitsatmosphaere': 'sternebewertung_arbeitsatmosphaere',
            'image': 'sternebewertung_image',
            'work_life_balance': 'sternebewertung_work_life_balance',
            'karriere_weiterbildung': 'sternebewertung_karriere_weiterbildung',
            'gehalt_sozialleistungen': 'sternebewertung_gehalt_sozialleistungen',
            'kollegenzusammenhalt': 'sternebewertung_kollegenzusammenhalt',
            'umwelt_sozialbewusstsein': 'sternebewertung_umwelt_sozialbewusstsein',
            'vorgesetztenverhalten': 'sternebewertung_vorgesetztenverhalten',
            'kommunikation': 'sternebewertung_kommunikation',
            'interessante_aufgaben': 'sternebewertung_interessante_aufgaben',
            'umgang_mit_aelteren_kollegen': 'sternebewertung_umgang_mit_aelteren_kollegen',
            'arbeitsbedingungen': 'sternebewertung_arbeitsbedingungen',
            'gleichberechtigung': 'sternebewertung_gleichberechtigung'
        }
        
        # Text fields to analyze
        text_fields = [
            'gut_am_arbeitgeber_finde_ich',
            'schlecht_am_arbeitgeber_finde_ich',
            'verbesserungsvorschlaege'
        ]
        
        analyzed_reviews = []
        
        for review in reviews:
            review_analysis = {
                'id': review.get('id'),
                'titel': review.get('titel'),
                'datum': review.get('datum'),
                'durchschnittsbewertung': review.get('durchschnittsbewertung'),
                'text_analyses': [],
                'ratings': {},
                'overall_sentiment': None,
                'topics_summary': []
            }
            
            # Analyze text fields
            all_sentiments = []
            all_topics = []
            
            for field in text_fields:
                text = review.get(field)
                if text and text.strip():
                    # Get topics
                    topics = lda_model.predict_topics(text, threshold=0.1)
                    
                    # Get sentiment
                    sentiment = self.sentiment_analyzer.analyze_sentiment(text)
                    all_sentiments.append(sentiment)
                    
                    # Combine
                    review_analysis['text_analyses'].append({
                        'field': field,
                        'text_preview': text[:100] + '...' if len(text) > 100 else text,
                        'topics': topics,
                        'sentiment': sentiment,
                        'dominant_topic': topics[0]['topic_id'] if topics else None
                    })
                    
                    # Collect all topics
                    all_topics.extend(topics)
            
            # Calculate overall sentiment
            if all_sentiments:
                avg_polarity = sum(s['polarity'] for s in all_sentiments) / len(all_sentiments)
                avg_subjectivity = sum(s['subjectivity'] for s in all_sentiments) / len(all_sentiments)
                
                if avg_polarity > 0.1:
                    overall_sentiment = 'positive'
                elif avg_polarity < -0.1:
                    overall_sentiment = 'negative'
                else:
                    overall_sentiment = 'neutral'
                
                review_analysis['overall_sentiment'] = {
                    'sentiment': overall_sentiment,
                    'avg_polarity': float(avg_polarity),
                    'avg_subjectivity': float(avg_subjectivity)
                }
            
            # Get star ratings
            for category, field_name in rating_fields.items():
                rating = review.get(field_name)
                if rating is not None:
                    review_analysis['ratings'][category] = float(rating)
            
            # Summarize topics
            if all_topics:
                topic_counts = {}
                for topic_data in all_topics:
                    topic_id = topic_data['topic_id']
                    prob = topic_data['probability']
                    if topic_id not in topic_counts:
                        topic_counts[topic_id] = {'count': 0, 'total_prob': 0.0}
                    topic_counts[topic_id]['count'] += 1
                    topic_counts[topic_id]['total_prob'] += prob
                
                review_analysis['topics_summary'] = [
                    {
                        'topic_id': topic_id,
                        'mentions': data['count'],
                        'avg_probability': data['total_prob'] / data['count']
                    }
                    for topic_id, data in topic_counts.items()
                ]
                review_analysis['topics_summary'].sort(key=lambda x: x['avg_probability'], reverse=True)
            
            analyzed_reviews.append(review_analysis)
        
        return {
            'total_reviews': len(analyzed_reviews),
            'reviews': analyzed_reviews
        }

    def analyze_employee_reviews_with_ratings_for_company(
        self,
        lda_model: LDATopicAnalyzer,
        company_id: int,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Same as `analyze_employee_reviews_with_ratings` but filtered by `company_id`.
        """
        query = self.db.supabase.table('employee').select('*').eq('company_id', company_id)
        if limit:
            query = query.limit(limit)

        response = query.execute()
        reviews = response.data

        # Reuse existing logic by temporarily assigning reviews and running analysis loop
        analyzed_reviews = []

        rating_fields = {
            'arbeitsatmosphaere': 'sternebewertung_arbeitsatmosphaere',
            'image': 'sternebewertung_image',
            'work_life_balance': 'sternebewertung_work_life_balance',
            'karriere_weiterbildung': 'sternebewertung_karriere_weiterbildung',
            'gehalt_sozialleistungen': 'sternebewertung_gehalt_sozialleistungen',
            'kollegenzusammenhalt': 'sternebewertung_kollegenzusammenhalt',
            'umwelt_sozialbewusstsein': 'sternebewertung_umwelt_sozialbewusstsein',
            'vorgesetztenverhalten': 'sternebewertung_vorgesetztenverhalten',
            'kommunikation': 'sternebewertung_kommunikation',
            'interessante_aufgaben': 'sternebewertung_interessante_aufgaben',
            'umgang_mit_aelteren_kollegen': 'sternebewertung_umgang_mit_aelteren_kollegen',
            'arbeitsbedingungen': 'sternebewertung_arbeitsbedingungen',
            'gleichberechtigung': 'sternebewertung_gleichberechtigung'
        }

        text_fields = [
            'gut_am_arbeitgeber_finde_ich',
            'schlecht_am_arbeitgeber_finde_ich',
            'verbesserungsvorschlaege'
        ]

        for review in reviews:
            review_analysis = {
                'id': review.get('id'),
                'titel': review.get('titel'),
                'datum': review.get('datum'),
                'durchschnittsbewertung': review.get('durchschnittsbewertung'),
                'text_analyses': [],
                'ratings': {},
                'overall_sentiment': None,
                'topics_summary': []
            }

            all_sentiments = []
            all_topics = []

            for field in text_fields:
                text = review.get(field)
                if text and text.strip():
                    topics = lda_model.predict_topics(text, threshold=0.1)
                    sentiment = self.sentiment_analyzer.analyze_sentiment(text)
                    all_sentiments.append(sentiment)

                    review_analysis['text_analyses'].append({
                        'field': field,
                        'text_preview': text[:100] + '...' if len(text) > 100 else text,
                        'topics': topics,
                        'sentiment': sentiment,
                        'dominant_topic': topics[0]['topic_id'] if topics else None
                    })

                    all_topics.extend(topics)

            if all_sentiments:
                avg_polarity = sum(s['polarity'] for s in all_sentiments) / len(all_sentiments)
                avg_subjectivity = sum(s.get('subjectivity', 0.0) for s in all_sentiments) / len(all_sentiments)

                if avg_polarity > 0.1:
                    overall_sentiment = 'positive'
                elif avg_polarity < -0.1:
                    overall_sentiment = 'negative'
                else:
                    overall_sentiment = 'neutral'

                review_analysis['overall_sentiment'] = {
                    'sentiment': overall_sentiment,
                    'avg_polarity': float(avg_polarity),
                    'avg_subjectivity': float(avg_subjectivity)
                }

            for category, field_name in rating_fields.items():
                rating = review.get(field_name)
                if rating is not None:
                    review_analysis['ratings'][category] = float(rating)

            if all_topics:
                topic_counts = {}
                for topic_data in all_topics:
                    topic_id = topic_data['topic_id']
                    prob = topic_data['probability']
                    if topic_id not in topic_counts:
                        topic_counts[topic_id] = {'count': 0, 'total_prob': 0.0}
                    topic_counts[topic_id]['count'] += 1
                    topic_counts[topic_id]['total_prob'] += prob

                review_analysis['topics_summary'] = [
                    {
                        'topic_id': topic_id,
                        'mentions': data['count'],
                        'avg_probability': data['total_prob'] / data['count']
                    }
                    for topic_id, data in topic_counts.items()
                ]
                review_analysis['topics_summary'].sort(key=lambda x: x['avg_probability'], reverse=True)

            analyzed_reviews.append(review_analysis)

        return {
            'total_reviews': len(analyzed_reviews),
            'reviews': analyzed_reviews
        }

    def analyze_candidate_reviews_with_ratings_for_company(
        self,
        lda_model: LDATopicAnalyzer,
        company_id: int,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Same as `analyze_candidate_reviews_with_ratings` but filtered by `company_id`.
        """
        query = self.db.supabase.table('candidates').select('*').eq('company_id', company_id)
        if limit:
            query = query.limit(limit)

        response = query.execute()
        reviews = response.data

        # reuse candidate logic
        rating_fields = {
            'erklaerung_der_weiteren_schritte': 'sternebewertung_erklaerung_der_weiteren_schritte',
            'zufriedenstellende_reaktion': 'sternebewertung_zufriedenstellende_reaktion',
            'vollstaendigkeit_der_infos': 'sternebewertung_vollstaendigkeit_der_infos',
            'zufriedenstellende_antworten': 'sternebewertung_zufriedenstellende_antworten',
            'angenehme_atmosphaere': 'sternebewertung_angenehme_atmosphaere',
            'professionalitaet_des_gespraechs': 'sternebewertung_professionalitaet_des_gespraechs',
            'wertschaetzende_behandlung': 'sternebewertung_wertschaetzende_behandlung',
            'erwartbarkeit_des_prozesses': 'sternebewertung_erwartbarkeit_des_prozesses',
            'zeitgerechte_zu_oder_absage': 'sternebewertung_zeitgerechte_zu_oder_absage',
            'schnelle_antwort': 'sternebewertung_schnelle_antwort'
        }

        text_fields = ['stellenbeschreibung', 'verbesserungsvorschlaege']

        analyzed_reviews = []

        for review in reviews:
            review_analysis = {
                'id': review.get('id'),
                'titel': review.get('titel'),
                'datum': review.get('datum'),
                'durchschnittsbewertung': review.get('durchschnittsbewertung'),
                'text_analyses': [],
                'ratings': {},
                'overall_sentiment': None,
                'topics_summary': []
            }

            all_sentiments = []
            all_topics = []

            for field in text_fields:
                text = review.get(field)
                if text and text.strip():
                    topics = lda_model.predict_topics(text, threshold=0.1)
                    sentiment = self.sentiment_analyzer.analyze_sentiment(text)
                    all_sentiments.append(sentiment)

                    review_analysis['text_analyses'].append({
                        'field': field,
                        'text_preview': text[:100] + '...' if len(text) > 100 else text,
                        'topics': topics,
                        'sentiment': sentiment,
                        'dominant_topic': topics[0]['topic_id'] if topics else None
                    })

                    all_topics.extend(topics)

            if all_sentiments:
                avg_polarity = sum(s['polarity'] for s in all_sentiments) / len(all_sentiments)

                if avg_polarity > 0.1:
                    overall_sentiment = 'positive'
                elif avg_polarity < -0.1:
                    overall_sentiment = 'negative'
                else:
                    overall_sentiment = 'neutral'

                review_analysis['overall_sentiment'] = {
                    'sentiment': overall_sentiment,
                    'avg_polarity': float(avg_polarity)
                }

            for category, field_name in rating_fields.items():
                rating = review.get(field_name)
                if rating is not None:
                    review_analysis['ratings'][category] = float(rating)

            if all_topics:
                topic_counts = {}
                for topic_data in all_topics:
                    topic_id = topic_data['topic_id']
                    prob = topic_data['probability']
                    if topic_id not in topic_counts:
                        topic_counts[topic_id] = {'count': 0, 'total_prob': 0.0}
                    topic_counts[topic_id]['count'] += 1
                    topic_counts[topic_id]['total_prob'] += prob

                review_analysis['topics_summary'] = [
                    {
                        'topic_id': topic_id,
                        'mentions': data['count'],
                        'avg_probability': data['total_prob'] / data['count']
                    }
                    for topic_id, data in topic_counts.items()
                ]
                review_analysis['topics_summary'].sort(key=lambda x: x['avg_probability'], reverse=True)

            analyzed_reviews.append(review_analysis)

        return {
            'total_reviews': len(analyzed_reviews),
            'reviews': analyzed_reviews
        }

    def get_topic_rating_correlation_for_company(
        self,
        lda_model: LDATopicAnalyzer,
        company_id: int,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Aggregate topic-rating correlation but only for reviews belonging to `company_id`.
        """
        employee_analysis = self.analyze_employee_reviews_with_ratings_for_company(lda_model, company_id, limit)
        candidate_analysis = self.analyze_candidate_reviews_with_ratings_for_company(lda_model, company_id, limit)

        all_reviews = employee_analysis['reviews'] + candidate_analysis['reviews']

        topic_stats = {}

        for review in all_reviews:
            avg_rating = review.get('durchschnittsbewertung')
            sentiment = review.get('overall_sentiment')

            for topic_summary in review.get('topics_summary', []):
                topic_id = topic_summary['topic_id']

                if topic_id not in topic_stats:
                    topic_stats[topic_id] = {
                        'topic_id': topic_id,
                        'mention_count': 0,
                        'ratings': [],
                        'sentiments': {'positive': 0, 'neutral': 0, 'negative': 0},
                        'avg_rating': 0.0,
                        'avg_sentiment_polarity': 0.0
                    }

                topic_stats[topic_id]['mention_count'] += topic_summary['mentions']

                if avg_rating is not None:
                    try:
                        topic_stats[topic_id]['ratings'].append(float(avg_rating))
                    except:
                        pass

                if sentiment:
                    sentiment_type = sentiment.get('sentiment', 'neutral')
                    topic_stats[topic_id]['sentiments'][sentiment_type] += 1

        for topic_id, stats in topic_stats.items():
            if stats['ratings']:
                stats['avg_rating'] = sum(stats['ratings']) / len(stats['ratings'])

            try:
                topic_words = lda_model.lda_model.show_topic(topic_id, 5)
                stats['top_words'] = [
                    {'word': word, 'weight': float(weight)}
                    for word, weight in topic_words
                ]
            except:
                stats['top_words'] = []

            # compute a simple avg sentiment polarity proxy: negative - positive counts
            neg = stats['sentiments'].get('negative', 0)
            pos = stats['sentiments'].get('positive', 0)
            stats['avg_sentiment_polarity'] = float((neg * -1) + pos)

        topic_list = list(topic_stats.values())
        topic_list.sort(key=lambda x: x['mention_count'], reverse=True)

        return {
            'total_topics': len(topic_list),
            'topics': topic_list,
            'summary': {
                'total_reviews_analyzed': len(all_reviews)
            }
        }
    
    def get_topic_rating_correlation(
        self,
        lda_model: LDATopicAnalyzer,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Analyze correlation between topics and star ratings.
        
        Args:
            lda_model: Trained LDA model
            limit: Maximum number of reviews to analyze
            
        Returns:
            Topic-rating correlation analysis
        """
        analysis = self.analyze_employee_reviews_with_ratings(lda_model, limit)
        
        # Aggregate by topic
        topic_stats = {}
        
        for review in analysis['reviews']:
            avg_rating = review.get('durchschnittsbewertung')
            sentiment = review.get('overall_sentiment')
            
            for topic_summary in review.get('topics_summary', []):
                topic_id = topic_summary['topic_id']
                
                if topic_id not in topic_stats:
                    topic_stats[topic_id] = {
                        'topic_id': topic_id,
                        'mention_count': 0,
                        'ratings': [],
                        'sentiments': {'positive': 0, 'neutral': 0, 'negative': 0},
                        'avg_rating': 0.0,
                        'avg_sentiment_polarity': 0.0
                    }
                
                topic_stats[topic_id]['mention_count'] += topic_summary['mentions']
                
                if avg_rating is not None:
                    topic_stats[topic_id]['ratings'].append(float(avg_rating))
                
                if sentiment:
                    sentiment_type = sentiment.get('sentiment', 'neutral')
                    topic_stats[topic_id]['sentiments'][sentiment_type] += 1
        
        # Calculate averages
        for topic_id, stats in topic_stats.items():
            if stats['ratings']:
                stats['avg_rating'] = sum(stats['ratings']) / len(stats['ratings'])
            
            # Get topic details from model
            try:
                topic_words = lda_model.lda_model.show_topic(topic_id, 5)
                stats['top_words'] = [
                    {'word': word, 'weight': float(weight)}
                    for word, weight in topic_words
                ]
            except:
                stats['top_words'] = []
        
        # Convert to list and sort by mention count
        topic_list = list(topic_stats.values())
        topic_list.sort(key=lambda x: x['mention_count'], reverse=True)
        
        return {
            'total_topics': len(topic_list),
            'topics': topic_list,
            'summary': {
                'total_reviews_analyzed': analysis['total_reviews']
            }
        }
    
    def analyze_candidate_reviews_with_ratings(
        self,
        lda_model: LDATopicAnalyzer,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Analyze candidate reviews with topics, sentiment, and ratings.
        
        Args:
            lda_model: Trained LDA model
            limit: Maximum number of reviews to analyze
            
        Returns:
            Comprehensive analysis for candidates
        """
        # Fetch candidate data
        query = self.db.supabase.table('candidates').select('*')
        if limit:
            query = query.limit(limit)
        
        response = query.execute()
        reviews = response.data
        
        # Rating fields for candidates
        rating_fields = {
            'erklaerung_der_weiteren_schritte': 'sternebewertung_erklaerung_der_weiteren_schritte',
            'zufriedenstellende_reaktion': 'sternebewertung_zufriedenstellende_reaktion',
            'vollstaendigkeit_der_infos': 'sternebewertung_vollstaendigkeit_der_infos',
            'zufriedenstellende_antworten': 'sternebewertung_zufriedenstellende_antworten',
            'angenehme_atmosphaere': 'sternebewertung_angenehme_atmosphaere',
            'professionalitaet_des_gespraechs': 'sternebewertung_professionalitaet_des_gespraechs',
            'wertschaetzende_behandlung': 'sternebewertung_wertschaetzende_behandlung',
            'erwartbarkeit_des_prozesses': 'sternebewertung_erwartbarkeit_des_prozesses',
            'zeitgerechte_zu_oder_absage': 'sternebewertung_zeitgerechte_zu_oder_absage',
            'schnelle_antwort': 'sternebewertung_schnelle_antwort'
        }
        
        text_fields = ['stellenbeschreibung', 'verbesserungsvorschlaege']
        
        analyzed_reviews = []
        
        for review in reviews:
            review_analysis = {
                'id': review.get('id'),
                'titel': review.get('titel'),
                'datum': review.get('datum'),
                'durchschnittsbewertung': review.get('durchschnittsbewertung'),
                'text_analyses': [],
                'ratings': {},
                'overall_sentiment': None,
                'topics_summary': []
            }
            
            all_sentiments = []
            all_topics = []
            
            for field in text_fields:
                text = review.get(field)
                if text and text.strip():
                    topics = lda_model.predict_topics(text, threshold=0.1)
                    sentiment = self.sentiment_analyzer.analyze_sentiment(text)
                    all_sentiments.append(sentiment)
                    
                    review_analysis['text_analyses'].append({
                        'field': field,
                        'text_preview': text[:100] + '...' if len(text) > 100 else text,
                        'topics': topics,
                        'sentiment': sentiment,
                        'dominant_topic': topics[0]['topic_id'] if topics else None
                    })
                    
                    all_topics.extend(topics)
            
            # Overall sentiment
            if all_sentiments:
                avg_polarity = sum(s['polarity'] for s in all_sentiments) / len(all_sentiments)
                
                if avg_polarity > 0.1:
                    overall_sentiment = 'positive'
                elif avg_polarity < -0.1:
                    overall_sentiment = 'negative'
                else:
                    overall_sentiment = 'neutral'
                
                review_analysis['overall_sentiment'] = {
                    'sentiment': overall_sentiment,
                    'avg_polarity': float(avg_polarity)
                }
            
            # Ratings
            for category, field_name in rating_fields.items():
                rating = review.get(field_name)
                if rating is not None:
                    review_analysis['ratings'][category] = float(rating)
            
            # Topics summary
            if all_topics:
                topic_counts = {}
                for topic_data in all_topics:
                    topic_id = topic_data['topic_id']
                    prob = topic_data['probability']
                    if topic_id not in topic_counts:
                        topic_counts[topic_id] = {'count': 0, 'total_prob': 0.0}
                    topic_counts[topic_id]['count'] += 1
                    topic_counts[topic_id]['total_prob'] += prob
                
                review_analysis['topics_summary'] = [
                    {
                        'topic_id': topic_id,
                        'mentions': data['count'],
                        'avg_probability': data['total_prob'] / data['count']
                    }
                    for topic_id, data in topic_counts.items()
                ]
                review_analysis['topics_summary'].sort(key=lambda x: x['avg_probability'], reverse=True)
            
            analyzed_reviews.append(review_analysis)
        
        return {
            'total_reviews': len(analyzed_reviews),
            'reviews': analyzed_reviews
        }
