"""
Internet Search - Search for information about detected objects
Uses DuckDuckGo to find object information without API keys
"""

try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False
    print("[InternetSearch] Warning: duckduckgo-search not installed. Search disabled.")


def search_object_info(object_name, max_results=3):
    """
    Search for information about an object using DuckDuckGo
    
    Args:
        object_name: Name of object to search for
        max_results: Maximum number of results to return
        
    Returns:
        dict with search results and summary
    """
    if not DDGS_AVAILABLE:
        return {
            'object': object_name,
            'results': [],
            'summary': '',
            'error': 'DuckDuckGo search not available. Install duckduckgo-search.'
        }
    
    try:
        # Create search query
        query = f"what is a {object_name}"
        
        # Perform search
        with DDGS() as ddgs:
            search_results = list(ddgs.text(query, max_results=max_results))
        
        if not search_results:
            return {
                'object': object_name,
                'results': [],
                'summary': f'No information found about {object_name}.',
                'success': False
            }
        
        # Extract relevant information
        results = []
        for result in search_results:
            results.append({
                'title': result.get('title', ''),
                'snippet': result.get('body', ''),
                'url': result.get('href', '')
            })
        
        # Create summary from first result
        first_snippet = results[0]['snippet'] if results else ''
        summary = f"{object_name.capitalize()}: {first_snippet}"
        
        return {
            'object': object_name,
            'results': results,
            'summary': summary,
            'success': True
        }
        
    except Exception as e:
        return {
            'object': object_name,
            'results': [],
            'summary': '',
            'error': f'Search failed: {str(e)}'
        }


def search_and_summarize(object_name, use_llm=True):
    """
    Search for object info and create LLM summary
    
    Args:
        object_name: Object to search for
        use_llm: Whether to use LLM for summarization
        
    Returns:
        dict with formatted summary
    """
    search_result = search_object_info(object_name, max_results=5)
    
    if not search_result.get('success'):
        return search_result
    
    if not use_llm:
        return search_result
    
    # Use LLM to create better summary
    try:
        from core.llm import LLM
        
        llm = LLM()
        
        # Combine snippets
        context = "\n\n".join([
            f"{r['title']}: {r['snippet']}" 
            for r in search_result['results'][:3]
        ])
        
        prompt = (
            f"Based on these search results about '{object_name}', "
            f"provide a concise 2-3 sentence summary:\n\n{context}"
        )
        
        summary = llm.generate_simple(prompt)
        
        return {
            'object': object_name,
            'summary': summary,
            'sources': search_result['results'],
            'success': True
        }
        
    except Exception as e:
        # Fallback to basic summary
        return search_result
