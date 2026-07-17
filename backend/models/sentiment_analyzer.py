"""
Sentiment Analysis for German Text
Analyzes sentiment (positive, neutral, negative) of text data.
Supports both lexicon-based and transformer-based approaches.
"""

from typing import Dict, Any, List, Optional
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """
    Sentiment analyzer for German text supporting multiple approaches:
    - transformer: ML-based approach using German BERT models (accurate, primary mode)
    - lexicon: Rule-based approach with predefined word lists (fast, fallback/reserve)
    """
    
    def __init__(self, mode: str = "transformer"):
        """
        Initialize the sentiment analyzer.
        
        Args:
            mode: Analysis mode - either "transformer" (default, primary) or "lexicon" (fallback/reserve)
        """
        self.mode = mode
        self._transformer_pipeline = None
        self._transformer_available = False
        
        # Always initialize lexicon as fallback/reserve
        self._init_lexicon()
        
        # Initialize transformer (primary mode)
        if mode == "transformer":
            try:
                self._init_transformer()
                self._transformer_available = True
                logger.info("Transformer mode initialized as primary analyzer.")
            except Exception as e:
                logger.warning(
                    f"Could not initialize transformer mode: {e}. "
                    "Falling back to lexicon (reserve) mode."
                )
                self.mode = "lexicon"
        else:
            logger.info("Using lexicon (reserve) mode explicitly.")
    
    def _init_lexicon(self):
        """
        Initialize lexicon-based sentiment analysis components.
        
        Version 2.1: Expanded with 50+ workplace-specific sentiment words
        """
        # Positive German words (expanded with workplace-specific terms)
        self.positive_words = {
            # General positive
            'gut', 'super', 'toll', 'ausgezeichnet', 'hervorragend', 'wunderbar',
            'großartig', 'perfekt', 'prima', 'klasse', 'spitze', 'fantastisch',
            'exzellent', 'positiv', 'freundlich', 'hilfsbereit', 'nett', 'angenehm',
            'zufrieden', 'glücklich', 'erfreut', 'begeistert', 'motiviert',
            'professionell', 'kompetent', 'effizient', 'flexibel', 'modern',
            'innovativ', 'kreativ', 'dynamisch', 'fair', 'transparent', 'offen',
            'wertschätzend', 'respektvoll', 'unterstützend', 'fördernd',
            'beste', 'besten', 'besser', 'hervorragend', 'empfehlenswert',
            'liebe', 'mögen', 'gefällt', 'schätzen', 'loben', 'dankbar',
            # Workplace-specific positive (NEW in v2.1)
            'weiterbildung', 'weiterbildungsmöglichkeiten', 'karrierechancen', 
            'aufstiegsmöglichkeiten', 'entwicklungsmöglichkeiten', 'perspektive',
            'teamgeist', 'teamwork', 'kollegial', 'kooperativ', 'zusammenhalt',
            'ausgewogen', 'balance', 'familienfreundlich', 'vereinbarkeit',
            'wertschätzung', 'anerkennung', 'lob', 'förderung', 'unterstützung',
            'eigenverantwortung', 'selbstständig', 'gestaltungsspielraum',
            'spannend', 'interessant', 'abwechslungsreich', 'vielfältig',
            'strukturiert', 'organisiert', 'verlässlich', 'pünktlich',
            'kommunikativ', 'partizipativ', 'mitbestimmung', 'einbindung'
        }
        
        # Negative German words (expanded with workplace-specific terms)
        self.negative_words = {
            # General negative
            'schlecht', 'schlechtes', 'schlechte', 'mies', 'katastrophal', 
            'furchtbar', 'schrecklich', 'grausam', 'schlimm', 'übel', 'negativ',
            'unzufrieden', 'enttäuscht', 'frustriert', 'ärgerlich', 'stressig',
            'chaotisch', 'unprofessionell', 'inkompetent', 'ineffizient',
            'unfreundlich', 'unhöflich', 'respektlos', 'unfair', 'intransparent',
            'mangelhaft', 'ungenügend', 'unzureichend', 'problematisch',
            'schwierig', 'kompliziert', 'langsam', 'veraltet', 'altmodisch',
            'niedrig', 'gering', 'wenig', 'kaum', 'nicht', 'nie', 'kein',
            'fehlt', 'fehlen', 'vermissen', 'mangel', 'problem', 'probleme',
            'kritik', 'kritisch', 'beschwerde', 'ärger', 'hassen', 'hasse',
            # Workplace-specific negative (NEW in v2.1)
            'burnout', 'überlastung', 'überstunden', 'überarbeitet', 
            'unterbezahlt', 'ausbeutung', 'ausbeuten', 'unterbezahlung',
            'unorganisiert', 'desorganisiert', 'planlos', 'chaotisch',
            'perspektivlos', 'aussichtslos', 'stagnation', 'stillstand',
            'eintönig', 'monoton', 'langweilig', 'routiniert',
            'hierarchisch', 'autoritär', 'bevormundend', 'kontrollierend',
            'bürokratisch', 'umständlich', 'starr', 'unflexibel', 'rigid',
            'mikromanagement', 'misstrauisch', 'kontrollwahn',
            'mobbing', 'ausgrenzung', 'diskriminierung', 'benachteiligung',
            'befristet', 'unsicher', 'instabil', 'wackelig',
            'intransparent', 'undurchsichtig', 'verschlossen', 'geheimniskrämerei'
        }
        
        # Intensifiers
        self.intensifiers = {
            'sehr': 1.5,
            'extrem': 2.0,
            'total': 1.8,
            'absolut': 1.8,
            'wirklich': 1.3,
            'ziemlich': 1.2,
            'besonders': 1.5,
            'außerordentlich': 2.0,
            'unglaublich': 1.8
        }
        
        # Negations
        self.negations = {
            'nicht', 'kein', 'keine', 'keiner', 'keines', 'nie', 'niemals',
            'nimmer', 'nirgends', 'nichts', 'kaum', 'wenig'
        }
        
        # Neutral/mixed indicator patterns (regex)
        # These phrases signal neutral or mixed sentiment even when
        # individual words may carry positive or negative weight
        self._neutral_patterns = [
            r'\bnicht\s+schlecht\b',           # "nicht schlecht" = neutral
            r'\bnicht\s+besonders\b',          # "nicht besonders" = neutral
            r'\bes\s+ist\s+okay\b',            # "es ist okay" = neutral
            r'\bgeht\s+so\b',                  # "geht so" = neutral
            r'\bnichts\s+besonderes\b',        # "nichts besonderes" = neutral
            r'\bnichts\s+besonders\b',         # variant
            r'\bkönnte\s+besser\b',            # "könnte besser" = mixed
            r'\bkönnte\s+schlimmer\b',         # "könnte schlimmer" = mixed
            r'\bganz\s+okay\b',                # "ganz okay" = neutral
            r'\bganz\s+in\s+ordnung\b',        # "ganz in ordnung" = neutral
            r'\bmal\s+so\s+mal\s+so\b',       # "mal so mal so" = neutral
            r'\bdurchschnitt',                   # "durchschnittlich" = neutral
            r'\bmittelmäßig\b',                 # middling
            r'\bin\s+ordnung\b',               # "in ordnung" = neutral
            r'\bnaja\b',                        # "naja" = mixed
            r'\bsolide\b',                      # "solide" = neutral-positive
            r'\bakzeptabel\b',                  # acceptable
        ]
        self._compiled_neutral_patterns = [
            re.compile(p, re.IGNORECASE) for p in self._neutral_patterns
        ]
        
        # Negation-positive patterns: negated negative = neutral/positive
        self._negated_negative_patterns = [
            r'\bnicht\s+schlecht\b',
            r'\bnicht\s+schlimm\b',
            r'\bnicht\s+übel\b',
            r'\bkein\w*\s+problem\b',
            r'\bkein\w*\s+beschwerde\b',
        ]
        self._compiled_negated_negative = [
            re.compile(p, re.IGNORECASE) for p in self._negated_negative_patterns
        ]
    
    def _init_transformer(self):
        """Initialize transformer-based sentiment analysis."""
        try:
            from transformers import pipeline
            logger.info("Loading German sentiment analysis model...")
            
            # Primary model: oliverguhr/german-sentiment-bert
            # - Trained specifically on German text
            # - Supports positive/negative/neutral labels
            # Fallback: cardiffnlp multilingual model
            
            model_options = [
                "oliverguhr/german-sentiment-bert",  # Primary
                "cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual"  # Fallback
            ]
            
            loaded = False
            for model_name in model_options:
                try:
                    logger.info(f"Attempting to load: {model_name}")
                    self._transformer_pipeline = pipeline(
                        "sentiment-analysis",
                        model=model_name,
                        top_k=None  # Return all label scores
                    )
                    logger.info(f"✅ Transformer model loaded: {model_name}")
                    self._model_name = model_name
                    loaded = True
                    break
                except Exception as e:
                    logger.warning(f"Could not load {model_name}: {e}")
                    continue
            
            if not loaded:
                raise RuntimeError("Could not load any sentiment model")
            
        except ImportError:
            logger.error(
                "transformers library not found. "
                "Install with: pip install transformers torch"
            )
            raise ImportError(
                "Please install transformers: pip install transformers torch"
            )
        except Exception as e:
            logger.error(f"Error loading transformer model: {e}")
            raise
    
    def _has_neutral_indicators(self, text: str) -> bool:
        """Check if text contains neutral/mixed sentiment indicator phrases."""
        for pattern in self._compiled_neutral_patterns:
            if pattern.search(text):
                return True
        return False
    
    def _has_negated_negative(self, text: str) -> bool:
        """Check if text contains negated negative phrases (e.g. 'nicht schlecht')."""
        for pattern in self._compiled_negated_negative:
            if pattern.search(text):
                return True
        return False
    
    def _analyze_with_transformer(self, text: str, star_rating: Optional[float] = None) -> Dict[str, Any]:
        """
        Analyze sentiment using transformer model with hybrid lexicon validation.
        
        Version 2.3: Hybrid approach — transformer is primary, lexicon only corrects
        when transformer is genuinely uncertain (tightened thresholds).
        
        Strategy:
        1. Get transformer prediction
        2. Detect neutral indicator phrases (pattern-based)
        3. Cross-validate with lexicon when transformer and patterns disagree
        4. Apply adaptive neutral zone
        
        Args:
            text: Input text to analyze
            star_rating: Optional star rating (1-5) to use as calibration hint
            
        Returns:
            Sentiment analysis results
        """
        if not self._transformer_pipeline:
            raise RuntimeError("Transformer model not initialized")
        
        if not text or not isinstance(text, str) or not text.strip():
            return {
                "polarity": 0.0,
                "sentiment": "neutral",
                "subjectivity": 0.0,
                "confidence": 0.0
            }
        
        try:
            # Step 1: Get transformer prediction
            results = self._transformer_pipeline(text[:512])[0]
            
            best_result = max(results, key=lambda x: x['score'])
            label = best_result['label'].lower()
            confidence = best_result['score']
            
            # Get all scores for comparison
            score_map = {r['label'].lower(): r['score'] for r in results}
            pos_score = score_map.get('positive', 0.0)
            neg_score = score_map.get('negative', 0.0)
            neu_score = score_map.get('neutral', 0.0)
            
            # Map to our format
            sentiment_map = {
                'positive': ('positive', 1.0),
                'neutral': ('neutral', 0.0),
                'negative': ('negative', -1.0)
            }
            
            sentiment, polarity_base = sentiment_map.get(
                label, 
                ('neutral', 0.0)
            )
            polarity = polarity_base * confidence
            
            # Step 2: Neutral indicator detection
            has_neutral_phrases = self._has_neutral_indicators(text)
            has_negated_neg = self._has_negated_negative(text)
            
            # Step 3: Hybrid lexicon cross-validation
            lexicon_result = self._analyze_with_lexicon(text)
            lexicon_sentiment = lexicon_result['sentiment']
            lexicon_polarity = lexicon_result['polarity']
            
            # Step 4: Apply corrections for negative bias
            
            # Case A: Neutral indicators detected → override to neutral
            if has_neutral_phrases:
                # Text contains explicit neutral phrases like "nicht schlecht",
                # "es ist okay", "nichts besonderes" etc.
                sentiment = 'neutral'
                polarity = 0.0
                confidence = max(confidence * 0.8, neu_score, 0.6)
                logger.debug(f"Neutral indicator override: '{text[:40]}...'")
            
            # Case B: Negated negative phrases → should be neutral, not negative
            elif has_negated_neg and sentiment == 'negative':
                sentiment = 'neutral'
                polarity = 0.0
                confidence = max(confidence * 0.7, 0.5)
                logger.debug(f"Negated-negative override: '{text[:40]}...'")

            # Case F: Transformer says positive, lexicon says negative.
            # The transformer can be fooled by semantically positive words that appear
            # in a clearly negative context (e.g. "kein Respekt" — "Respekt" has a
            # positive embedding even when negated).  This fires BEFORE the confidence
            # hard cap so the lexicon can still correct obvious model errors.
            elif sentiment == 'positive' and lexicon_sentiment == 'negative' and lexicon_result['confidence'] > 0.3:
                sentiment = 'negative'
                polarity = lexicon_polarity * 0.6
                confidence = confidence * 0.6   # reduces but stays above 0.55 for typical scores
                logger.debug(f"Case F reversal (positive→negative): '{text[:40]}...'")

            # Hard cap: wenn der Transformer sehr sicher ist (>= 0.75),
            # vertrauen wir ihm komplett — kein Lexikon-Override mehr.
            elif confidence >= 0.75:
                logger.debug(f"Transformer high confidence ({confidence:.2f}), skipping lexicon correction.")
            
            # Case C: Transformer says negative but lexicon says neutral
            # → only correct if transformer is genuinely uncertain
            elif sentiment == 'negative' and lexicon_sentiment == 'neutral':
                # Require both a small margin AND low confidence before overriding
                margin = neg_score - max(pos_score, neu_score)
                if margin < 0.2 and confidence < 0.55:
                    sentiment = 'neutral'
                    polarity = 0.0
                    confidence = confidence * 0.7
                    logger.debug(f"Hybrid neutral correction: '{text[:40]}...'")
            
            # Case D: Transformer says negative but lexicon says positive
            # → only override if lexicon is very confident
            elif sentiment == 'negative' and lexicon_sentiment == 'positive':
                # Strong disagreement: lexicon must be very confident to override transformer
                if lexicon_result['confidence'] > 0.7:
                    sentiment = lexicon_sentiment
                    polarity = lexicon_polarity * 0.7
                    confidence = (confidence + lexicon_result['confidence']) / 2
                    logger.debug(f"Hybrid positive correction: '{text[:40]}...'")
                else:
                    # Low lexicon confidence too: go neutral
                    sentiment = 'neutral'
                    polarity = 0.0
                    confidence = confidence * 0.6
            
            # Case E: Transformer says neutral but lexicon says positive
            # → only boost if lexicon is confident
            elif sentiment == 'neutral' and lexicon_sentiment == 'positive':
                if lexicon_result['confidence'] > 0.6:
                    sentiment = 'positive'
                    polarity = lexicon_polarity * 0.8
                    confidence = (confidence + lexicon_result['confidence']) / 2
                    logger.debug(f"Hybrid positive boost: '{text[:40]}...'")
            
            # Optional: Use star_rating as calibration hint
            if star_rating is not None:
                rating_hint = 'neutral'
                if star_rating <= 2.5:
                    rating_hint = 'negative'
                elif star_rating >= 3.5:
                    rating_hint = 'positive'
                
                if (rating_hint == 'positive' and sentiment == 'negative') or \
                   (rating_hint == 'negative' and sentiment == 'positive'):
                    confidence *= 0.7
                    if confidence < 0.6:
                        sentiment = 'neutral'
                        polarity = 0.0
            
            subjectivity = confidence
            
            return {
                "polarity": float(polarity),
                "sentiment": sentiment,
                "subjectivity": float(subjectivity),
                "confidence": float(confidence),
                "raw_results": results
            }
            
        except Exception as e:
            logger.error(f"Error in transformer analysis: {e}")
            return {
                "polarity": 0.0,
                "sentiment": "neutral",
                "subjectivity": 0.0,
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _analyze_with_lexicon(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment using lexicon-based approach.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Sentiment analysis results
        """
        if not text or not isinstance(text, str) or not text.strip():
            return {
                "polarity": 0.0,
                "sentiment": "neutral",
                "subjectivity": 0.0,
                "confidence": 0.0
            }
        
        try:
            # Tokenize and lowercase
            words = text.lower().split()
            
            if not words:
                return {
                    "polarity": 0.0,
                    "sentiment": "neutral",
                    "subjectivity": 0.0,
                    "confidence": 0.0
                }
            
            positive_score = 0.0
            negative_score = 0.0
            sentiment_word_count = 0
            
            # Analyze each word with context
            for i, word in enumerate(words):
                # Check for intensifier
                multiplier = 1.0
                if i > 0 and words[i-1] in self.intensifiers:
                    multiplier = self.intensifiers[words[i-1]]
                
                # Check for negation
                is_negated = False
                if i > 0 and words[i-1] in self.negations:
                    is_negated = True
                if i > 1 and words[i-2] in self.negations:
                    is_negated = True
                
                # Score the word
                if word in self.positive_words:
                    sentiment_word_count += 1
                    score = 1.0 * multiplier
                    if is_negated:
                        negative_score += score
                    else:
                        positive_score += score
                        
                elif word in self.negative_words:
                    sentiment_word_count += 1
                    score = 1.0 * multiplier
                    if is_negated:
                        positive_score += score
                    else:
                        negative_score += score
            
            # Calculate polarity
            if positive_score + negative_score > 0:
                polarity = (positive_score - negative_score) / (positive_score + negative_score)
            else:
                polarity = 0.0
            
            # Calculate subjectivity (ratio of sentiment words to total words)
            subjectivity = min(sentiment_word_count / len(words), 1.0)
            
            # Version 2.1: Improved sentiment classification with adaptive thresholds
            # Tighter thresholds for better neutral detection
            if polarity > 0.15:
                sentiment = "positive"
            elif polarity < -0.15:
                sentiment = "negative"
            else:
                sentiment = "neutral"
            
            # Version 2.1: Improved confidence calculation
            # Takes into account both polarity strength and sentiment word density
            base_confidence = min(abs(polarity), 1.0)
            word_density_factor = min(sentiment_word_count / 10.0, 1.0)
            
            # Combine both factors (70% polarity strength, 30% word density)
            confidence = base_confidence * 0.7 + word_density_factor * 0.3
            confidence = min(confidence, 1.0)
            
            return {
                "polarity": float(polarity),
                "sentiment": sentiment,
                "subjectivity": float(subjectivity),
                "confidence": float(confidence)
            }
            
        except Exception as e:
            # Fallback on error
            return {
                "polarity": 0.0,
                "sentiment": "neutral",
                "subjectivity": 0.0,
                "confidence": 0.0,
                "error": str(e)
            }
    
    def analyze_sentiment(self, text: str, star_rating: Optional[float] = None) -> Dict[str, Any]:
        """
        Analyze sentiment of a single text.
        
        Version 2.1: Added optional star_rating parameter for calibration.
        
        Args:
            text: Input text to analyze
            star_rating: Optional star rating (1-5) to use as calibration hint
            
        Returns:
            Dictionary with sentiment analysis results:
            - polarity: float between -1 (negative) and 1 (positive)
            - sentiment: 'positive', 'neutral', or 'negative'
            - subjectivity: float between 0 (objective) and 1 (subjective)
            - confidence: float representing confidence in the classification
        """
        if self.mode == "transformer" and self._transformer_available:
            return self._analyze_with_transformer(text, star_rating)
        else:
            return self._analyze_with_lexicon(text)
    
    def analyze_with_rating_hint(
        self, 
        text: str, 
        star_rating: float
    ) -> Dict[str, Any]:
        """
        Analyze sentiment with star rating as calibration hint.
        
        Version 2.1: NEW METHOD - Hybrid approach combining model prediction
        with star rating information for improved accuracy on edge cases.
        
        Args:
            text: Input text to analyze
            star_rating: Star rating (1-5) to use as calibration hint
            
        Returns:
            Sentiment analysis results with rating-adjusted confidence
        """
        # Get base prediction
        result = self.analyze_sentiment(text, star_rating)
        
        # Add rating hint information
        result['star_rating'] = star_rating
        result['rating_hint'] = 'neutral'
        
        if star_rating <= 2.5:
            result['rating_hint'] = 'negative'
        elif star_rating >= 3.5:
            result['rating_hint'] = 'positive'
        
        return result
    
    def set_mode(self, mode: str):
        """
        Switch between analysis modes.
        
        Args:
            mode: Either "lexicon" or "transformer"
        """
        if mode not in ["lexicon", "transformer"]:
            raise ValueError("Mode must be 'lexicon' or 'transformer'")
        
        if mode == "transformer" and not self._transformer_pipeline:
            try:
                self._init_transformer()
                self._transformer_available = True
            except Exception as e:
                logger.warning(
                    f"Could not initialize transformer mode: {e}. "
                    "Staying in lexicon mode."
                )
                return
        
        self.mode = mode
        logger.info(f"Switched to {mode} mode")
    
    def analyze_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Analyze sentiment for multiple texts.
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            List of sentiment analysis results
        """
        return [self.analyze_sentiment(text) for text in texts]
    
    def get_sentiment_summary(self, sentiments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get summary statistics for a list of sentiment analyses.
        
        Args:
            sentiments: List of sentiment analysis results
            
        Returns:
            Summary statistics
        """
        if not sentiments:
            return {
                "count": 0,
                "avg_polarity": 0.0,
                "avg_subjectivity": 0.0,
                "positive_count": 0,
                "neutral_count": 0,
                "negative_count": 0,
                "positive_percentage": 0.0,
                "neutral_percentage": 0.0,
                "negative_percentage": 0.0
            }
        
        count = len(sentiments)
        avg_polarity = sum(s["polarity"] for s in sentiments) / count
        avg_subjectivity = sum(s["subjectivity"] for s in sentiments) / count
        
        positive_count = sum(1 for s in sentiments if s["sentiment"] == "positive")
        neutral_count = sum(1 for s in sentiments if s["sentiment"] == "neutral")
        negative_count = sum(1 for s in sentiments if s["sentiment"] == "negative")
        
        return {
            "count": count,
            "avg_polarity": float(avg_polarity),
            "avg_subjectivity": float(avg_subjectivity),
            "positive_count": positive_count,
            "neutral_count": neutral_count,
            "negative_count": negative_count,
            "positive_percentage": float(positive_count / count * 100),
            "neutral_percentage": float(neutral_count / count * 100),
            "negative_percentage": float(negative_count / count * 100)
        }
    
    def categorize_by_sentiment(
        self, 
        items: List[Dict[str, Any]], 
        sentiment_key: str = "sentiment_analysis"
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Categorize items by their sentiment.
        
        Args:
            items: List of items with sentiment analysis
            sentiment_key: Key in items that contains sentiment analysis
            
        Returns:
            Dictionary with items grouped by sentiment
        """
        categorized = {
            "positive": [],
            "neutral": [],
            "negative": []
        }
        
        for item in items:
            sentiment = item.get(sentiment_key, {}).get("sentiment", "neutral")
            categorized[sentiment].append(item)
        
        return categorized
