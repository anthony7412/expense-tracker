import re

# Define category keywords
CATEGORY_KEYWORDS = {
    'Groceries': ['grocery', 'supermarket', 'food', 'market', 'walmart', 'target', 'kroger', 'safeway', 'trader', 'whole foods'],
    'Dining': ['restaurant', 'cafe', 'coffee', 'starbucks', 'mcdonald', 'burger', 'pizza', 'taco', 'dining', 'doordash', 'ubereats', 'grubhub'],
    'Transportation': ['uber', 'lyft', 'taxi', 'gas', 'fuel', 'transit', 'train', 'bus', 'subway', 'metro', 'parking', 'toll'],
    'Entertainment': ['movie', 'cinema', 'theater', 'netflix', 'spotify', 'hulu', 'disney', 'amazon prime', 'ticket', 'concert', 'event'],
    'Shopping': ['amazon', 'ebay', 'etsy', 'shop', 'store', 'mall', 'retail', 'clothing', 'shoes', 'electronics'],
    'Utilities': ['electric', 'water', 'gas', 'power', 'utility', 'internet', 'phone', 'mobile', 'bill', 'cable', 'tv'],
    'Housing': ['rent', 'mortgage', 'apartment', 'home', 'house', 'property', 'real estate', 'hoa', 'maintenance'],
    'Healthcare': ['doctor', 'hospital', 'medical', 'pharmacy', 'health', 'dental', 'vision', 'insurance', 'clinic'],
    'Education': ['school', 'college', 'university', 'tuition', 'book', 'course', 'class', 'education', 'student'],
    'Personal': ['haircut', 'salon', 'spa', 'gym', 'fitness', 'beauty', 'cosmetic', 'personal care'],
    'Travel': ['hotel', 'flight', 'airline', 'airbnb', 'vacation', 'travel', 'booking', 'trip', 'tour', 'cruise'],
    'Subscription': ['subscription', 'membership', 'monthly', 'annual', 'fee', 'dues'],
}

def categorize_expense(description):
    """
    Categorize an expense based on its description.
    Returns the category name.
    """
    description = description.lower()
    
    categories = {
        'groceries': ['grocery', 'food', 'supermarket', 'market', 'supremo food'],
        'dining': ['restaurant', 'cafe', 'coffee', 'tst* gregorys'],
        'transportation': ['uber', 'lyft', 'taxi', 'njt bus', 'transit'],
        'shopping': ['amazon', 'zara', 'walmart', 'target'],
        'utilities': ['electric', 'water', 'gas', 'internet'],
        'entertainment': ['movie', 'theatre', 'netflix', 'spotify'],
        'healthcare': ['pharmacy', 'doctor', 'medical'],
    }
    
    for category, keywords in categories.items():
        if any(keyword in description for keyword in keywords):
            return category.title()
    
    return 'Other'

def categorize_expense_old(description):
    """
    Categorize an expense based on its description.
    Returns the category name.
    """
    description = description.lower()
    
    # Define keywords for each category with more specific matches
    categories = {
        'Transportation': [
            'njt bus', 'my-tix', 'mta', 'nyct', 'paygo', 'transit', 'uber', 'lyft',
            'taxi', 'train', 'subway', 'metro', 'path', 'parking', 'nj transit',
            'amtrak', 'rail'
        ],
        'Dining': [
            'restaurant', 'cafe', 'coffee', 'food', 'deli', 'kitchen', 'grill',
            'pizzeria', 'bar', 'tavern', 'pub', 'eatery', 'bistro', 'doordash',
            'uber eats', 'grubhub', 'seamless', 'veloce', 'gregorys', 'starbucks',
            'dunkin', 'mcdonalds', 'burger', 'wendy', 'chipotle', 'subway',
            'nunu ethiopian', 'supremo food'
        ],
        'Groceries': [
            'grocery', 'market', 'food market', 'supermarket', 'trader joe',
            'whole foods', 'wegmans', 'shop rite', 'stop & shop', 'aldi',
            'food bazaar', 'supremo food market'
        ],
        'Shopping': [
            'amazon', 'walmart', 'target', 'costco', 'best buy', 'apple',
            'zara', 'uniqlo', 'macy', 'nordstrom', 'tj maxx', 'marshall',
            'retail', 'store', 'market'
        ],
        'Entertainment': [
            'netflix', 'hulu', 'spotify', 'apple music', 'prime video',
            'disney+', 'hbo', 'movie', 'cinema', 'theatre', 'concert',
            'ticket', 'stubhub', 'eventbrite'
        ],
        'Bills & Utilities': [
            'verizon', 'at&t', 't-mobile', 'sprint', 'comcast', 'xfinity',
            'spectrum', 'con edison', 'pseg', 'national grid', 'water',
            'utility', 'bill', 'insurance'
        ]
    }
    
    # Check each category's keywords
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in description:
                return category
                
    # Special cases for specific merchants
    if any(term in description for term in ['mta*nyct', 'paygo']):
        return 'Transportation'
    
    if 'nunu ethiopian' in description:
        return 'Dining'
    
    if 'supremo food' in description and 'market' not in description:
        return 'Dining'
    
    return 'Miscellaneous' 