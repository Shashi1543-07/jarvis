import json
import os
import datetime
from collections import defaultdict, Counter
import re

class BehaviorLearning:
    """
    A module for learning user behavior patterns and adapting to user preferences
    """
    
    def __init__(self, memory):
        self.memory = memory
        self.behavior_patterns = {}
        self.daily_routines = {}
        self.preference_tracker = defaultdict(lambda: {'positive': 0, 'negative': 0})
        self.interaction_timing = []
        
    def learn_from_interaction(self, user_input, ai_response, timestamp=None):
        """
        Learn from each interaction to understand user preferences and behavior
        """
        if timestamp is None:
            timestamp = datetime.datetime.now()
        
        # Track interaction timing
        self.interaction_timing.append(timestamp)
        
        # Extract keywords and topics from user input
        keywords = self.extract_keywords(user_input)
        
        # Analyze sentiment of user response (simplified)
        sentiment = self.simple_sentiment_analysis(ai_response)
        
        # Update preference tracker
        for keyword in keywords:
            if sentiment == 'positive':
                self.preference_tracker[keyword]['positive'] += 1
            elif sentiment == 'negative':
                self.preference_tracker[keyword]['negative'] += 1
            else:
                # Neutral sentiment - just increment total
                pass
        
        # Detect routines based on time patterns
        hour = timestamp.hour
        if hour not in self.daily_routines:
            self.daily_routines[hour] = {'count': 0, 'activities': Counter()}
        self.daily_routines[hour]['count'] += 1
        
        # Categorize activity based on keywords
        activity_category = self.categorize_activity(keywords)
        if activity_category:
            self.daily_routines[hour]['activities'][activity_category] += 1
            
        # Store in memory
        self.update_memory_with_patterns()
    
    def extract_keywords(self, text):
        """
        Extract meaningful keywords from text
        """
        # Convert to lowercase and remove punctuation
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        
        # Common stop words to exclude
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'about', 'as', 'into', 'through', 'during', 'before',
            'after', 'above', 'below', 'up', 'down', 'out', 'off', 'over', 'under',
            'again', 'further', 'then', 'once', 'i', 'me', 'my', 'myself', 'we', 
            'our', 'ours', 'ourselves', 'you', 'your', 'yours', 'yourself', 'yourselves',
            'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself', 'it', 
            'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what',
            'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are',
            'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do',
            'does', 'did', 'doing', 'would', 'should', 'could', 'ought', 'i\'m', 'you\'re',
            'he\'s', 'she\'s', 'it\'s', 'we\'re', 'they\'re', 'i\'ve', 'you\'ve', 'we\'ve',
            'they\'ve', 'i\'d', 'you\'d', 'he\'d', 'she\'d', 'we\'d', 'they\'d', 'i\'ll',
            'you\'ll', 'he\'ll', 'she\'ll', 'we\'ll', 'they\'ll', 'isn\'t', 'aren\'t',
            'wasn\'t', 'weren\'t', 'haven\'t', 'hasn\'t', 'hadn\'t', 'doesn\'t', 'don\'t',
            'didn\'t', 'won\'t', 'wouldn\'t', 'can\'t', 'cannot', 'couldn\'t', 'mustn\'t',
            'let\'s', 'that\'s', 'who\'s', 'what\'s', 'here\'s', 'there\'s', 'when\'s',
            'where\'s', 'why\'s', 'how\'s', 'a', 'able', 'about', 'above', 'according',
            'accordingly', 'across', 'actually', 'after', 'afterwards', 'again', 'against',
            'aint', 'all', 'allow', 'allows', 'almost', 'alone', 'along', 'already',
            'also', 'although', 'always', 'am', 'among', 'amongst', 'an', 'and', 'another',
            'any', 'anybody', 'anyhow', 'anyone', 'anything', 'anyway', 'anyways', 'anywhere',
            'apart', 'appear', 'appreciate', 'appropriate', 'are', 'arent', 'around', 'as',
            'aside', 'ask', 'asking', 'associated', 'at', 'available', 'away', 'awfully',
            'be', 'became', 'because', 'become', 'becomes', 'becoming', 'been', 'before',
            'beforehand', 'behind', 'being', 'believe', 'below', 'beside', 'besides', 'best',
            'better', 'between', 'beyond', 'both', 'brief', 'but', 'by', 'cmon', 'cs',
            'came', 'can', 'cant', 'cannot', 'cant', 'cause', 'causes', 'certain', 'certainly',
            'changes', 'clearly', 'co', 'com', 'come', 'comes', 'concerning', 'consequently',
            'consider', 'considering', 'contain', 'containing', 'contains', 'corresponding',
            'could', 'couldnt', 'course', 'currently', 'definitely', 'described', 'despite',
            'did', 'didnt', 'different', 'do', 'does', 'doesnt', 'doing', 'dont', 'done',
            'down', 'downwards', 'during', 'each', 'edu', 'eg', 'eight', 'either', 'else',
            'elsewhere', 'enough', 'entirely', 'especially', 'et', 'etc', 'even', 'ever',
            'every', 'everybody', 'everyone', 'everything', 'everywhere', 'ex', 'exactly',
            'example', 'except', 'far', 'few', 'fifth', 'first', 'five', 'followed', 'following',
            'follows', 'for', 'former', 'formerly', 'forth', 'four', 'from', 'further',
            'furthermore', 'get', 'gets', 'getting', 'given', 'gives', 'go', 'goes', 'going',
            'gone', 'got', 'gotten', 'greetings', 'had', 'hadnt', 'happens', 'hardly', 'has',
            'hasnt', 'have', 'havent', 'having', 'he', 'hes', 'hello', 'help', 'hence', 'her',
            'here', 'heres', 'hers', 'herself', 'hi', 'him', 'himself', 'his', 'hither',
            'hopefully', 'how', 'howbeit', 'however', 'i', 'id', 'ill', 'im', 'ive', 'ie',
            'if', 'ignored', 'immediate', 'in', 'inasmuch', 'inc', 'indeed', 'indicate',
            'indicated', 'indicates', 'inner', 'insofar', 'instead', 'into', 'inward', 'is',
            'isnt', 'it', 'itd', 'itll', 'its', 'its', 'itself', 'just', 'keep', 'keeps',
            'kept', 'know', 'known', 'knows', 'last', 'lately', 'later', 'latter', 'latterly',
            'least', 'less', 'lest', 'let', 'lets', 'like', 'liked', 'likely', 'little',
            'look', 'looking', 'looks', 'ltd', 'mainly', 'many', 'may', 'maybe', 'me', 'mean',
            'meanwhile', 'merely', 'might', 'more', 'moreover', 'most', 'mostly', 'much',
            'must', 'my', 'myself', 'name', 'namely', 'nd', 'near', 'nearly', 'necessary',
            'need', 'needs', 'neither', 'never', 'nevertheless', 'new', 'next', 'nine', 'no',
            'nobody', 'non', 'none', 'noone', 'nor', 'normally', 'not', 'nothing', 'novel',
            'now', 'nowhere', 'obviously', 'of', 'off', 'often', 'oh', 'ok', 'okay', 'old',
            'on', 'once', 'one', 'ones', 'only', 'onto', 'or', 'other', 'others', 'otherwise',
            'ought', 'our', 'ours', 'ourselves', 'out', 'outside', 'over', 'overall', 'own',
            'particular', 'particularly', 'per', 'perhaps', 'placed', 'please', 'plus', 'possible',
            'presumably', 'probably', 'provides', 'que', 'quite', 'qv', 'rather', 'rd', 're',
            'really', 'reasonably', 'regarding', 'regardless', 'regards', 'relatively',
            'respectively', 'right', 'said', 'same', 'saw', 'say', 'saying', 'says', 'second',
            'secondly', 'see', 'seeing', 'seem', 'seemed', 'seeming', 'seems', 'seen', 'self',
            'selves', 'sensible', 'sent', 'serious', 'seriously', 'seven', 'several', 'shall',
            'she', 'should', 'shouldnt', 'since', 'six', 'so', 'some', 'somebody', 'somehow',
            'someone', 'something', 'sometime', 'sometimes', 'somewhat', 'somewhere', 'soon',
            'sorry', 'specified', 'specify', 'specifying', 'still', 'sub', 'such', 'sup',
            'sure', 'ts', 'take', 'taken', 'tell', 'tends', 'th', 'than', 'thank', 'thanks',
            'thanx', 'that', 'thats', 'thats', 'the', 'their', 'theirs', 'them', 'themselves',
            'then', 'thence', 'there', 'theres', 'thereafter', 'thereby', 'therefore', 'therein',
            'theres', 'thereupon', 'these', 'they', 'theyd', 'theyll', 'theyre', 'theyve',
            'think', 'third', 'this', 'thorough', 'thoroughly', 'those', 'though', 'three',
            'through', 'throughout', 'thru', 'thus', 'to', 'together', 'too', 'took', 'toward',
            'towards', 'tried', 'tries', 'truly', 'try', 'trying', 'twice', 'two', 'un',
            'under', 'unfortunately', 'unless', 'unlikely', 'until', 'unto', 'up', 'upon',
            'us', 'use', 'used', 'useful', 'uses', 'using', 'usually', 'value', 'various',
            'very', 'via', 'viz', 'vs', 'want', 'wants', 'was', 'wasnt', 'way', 'we', 'wed',
            'well', 'were', 'weve', 'welcome', 'well', 'went', 'were', 'werent', 'what',
            'whats', 'whatever', 'when', 'whence', 'whenever', 'where', 'wheres', 'whereafter',
            'whereas', 'whereby', 'wherein', 'whereupon', 'wherever', 'whether', 'which',
            'while', 'whilst', 'whither', 'who', 'whos', 'whoever', 'whole', 'whom', 'whose',
            'why', 'will', 'willing', 'wish', 'with', 'within', 'without', 'wont', 'wonder',
            'would', 'would', 'wouldnt', 'yes', 'yet', 'you', 'youd', 'youll', 'youre',
            'youve', 'your', 'yours', 'yourself', 'yourselves', 'zero'
        }
        
        # Split text into words and filter
        words = text.split()
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords
    
    def simple_sentiment_analysis(self, text):
        """
        Perform a simple sentiment analysis
        """
        positive_words = {
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'brilliant',
            'perfect', 'love', 'like', 'enjoy', 'happy', 'pleased', 'satisfied', 'delighted',
            'thrilled', 'awesome', 'super', 'cool', 'nice', 'beautiful', 'incredible', 'fabulous'
        }
        
        negative_words = {
            'bad', 'terrible', 'awful', 'horrible', 'hate', 'dislike', 'disappointing',
            'sad', 'angry', 'frustrated', 'annoyed', 'upset', 'poor', 'worst', 'useless',
            'stupid', 'wrong', 'incorrect', 'fail', 'failure', 'problem', 'issue', 'difficult'
        }
        
        text_lower = text.lower()
        words = set(text_lower.split())
        
        pos_count = len(words.intersection(positive_words))
        neg_count = len(words.intersection(negative_words))
        
        if pos_count > neg_count:
            return 'positive'
        elif neg_count > pos_count:
            return 'negative'
        else:
            return 'neutral'
    
    def categorize_activity(self, keywords):
        """
        Categorize the type of activity based on keywords
        """
        work_related = {'work', 'job', 'office', 'meeting', 'project', 'task', 'deadline', 'email', 'document'}
        entertainment = {'movie', 'film', 'music', 'game', 'play', 'fun', 'entertainment', 'video', 'show', 'series'}
        learning = {'study', 'learn', 'education', 'school', 'college', 'university', 'book', 'knowledge', 'skill'}
        health = {'health', 'exercise', 'fitness', 'workout', 'diet', 'food', 'nutrition', 'sleep', 'medicine'}
        tech = {'computer', 'software', 'technology', 'ai', 'programming', 'code', 'app', 'device', 'internet'}
        
        keyword_set = set([kw.lower() for kw in keywords])
        
        if keyword_set.intersection(work_related):
            return 'work'
        elif keyword_set.intersection(entertainment):
            return 'entertainment'
        elif keyword_set.intersection(learning):
            return 'learning'
        elif keyword_set.intersection(health):
            return 'health'
        elif keyword_set.intersection(tech):
            return 'technology'
        else:
            return 'general'
    
    def update_memory_with_patterns(self):
        """
        Update the memory with learned behavior patterns
        """
        # Update habits based on routines
        for hour, data in self.daily_routines.items():
            if data['count'] > 2:  # If this hour has significant activity
                most_common_activity = data['activities'].most_common(1)
                if most_common_activity:
                    activity, count = most_common_activity[0]
                    habit_desc = f"Active during {hour}:00 with {activity} activities"
                    self.memory.remember_habit(habit_desc, "routine")
        
        # Update interests based on preference tracker
        for item, counts in self.preference_tracker.items():
            total_interactions = counts['positive'] + counts['negative']
            if total_interactions > 2:  # At least 3 interactions
                positive_ratio = counts['positive'] / total_interactions
                if positive_ratio > 0.6:  # More than 60% positive
                    self.memory.remember_interest(item)
                    self.memory.remember_favorite("liked_items", item)
                elif positive_ratio < 0.4:  # Less than 40% positive
                    self.memory.remember_favorite("disliked_items", item)
    
    def get_user_preferences_summary(self):
        """
        Get a summary of learned user preferences
        """
        preferences = {}
        
        # Get top liked items
        liked_items = []
        for item, counts in self.preference_tracker.items():
            total = counts['positive'] + counts['negative']
            if total > 0 and counts['positive'] > counts['negative']:
                liked_items.append((item, counts['positive'] / total))
        
        liked_items.sort(key=lambda x: x[1], reverse=True)
        preferences['liked'] = [item[0] for item in liked_items[:5]]  # Top 5 liked items
        
        # Get top disliked items
        disliked_items = []
        for item, counts in self.preference_tracker.items():
            total = counts['positive'] + counts['negative']
            if total > 0 and counts['negative'] > counts['positive']:
                disliked_items.append((item, counts['negative'] / total))
        
        disliked_items.sort(key=lambda x: x[1], reverse=True)
        preferences['disliked'] = [item[0] for item in disliked_items[:5]]  # Top 5 disliked items
        
        # Get daily routines
        active_hours = []
        for hour, data in self.daily_routines.items():
            if data['count'] > 1:  # Active at least twice
                most_common = data['activities'].most_common(1)
                if most_common:
                    activity = most_common[0][0]
                    active_hours.append({
                        'hour': hour,
                        'activity': activity,
                        'frequency': data['count']
                    })
        
        preferences['routines'] = sorted(active_hours, key=lambda x: x['frequency'], reverse=True)[:5]
        
        return preferences
    
    def suggest_based_on_patterns(self):
        """
        Suggest actions based on learned patterns
        """
        suggestions = []
        
        # Get user preferences
        prefs = self.get_user_preferences_summary()
        
        # Suggest based on liked items
        if prefs.get('liked'):
            suggestions.append(f"I've noticed you enjoy {', '.join(prefs['liked'][:2])}. Would you like to explore more related topics?")
        
        # Suggest based on routines
        if prefs.get('routines'):
            most_active = prefs['routines'][0] if prefs['routines'] else None
            if most_active:
                suggestions.append(f"I notice you're often active around {most_active['hour']}:00 doing {most_active['activity']}. Should I prepare for that activity when it's time?")
        
        return suggestions