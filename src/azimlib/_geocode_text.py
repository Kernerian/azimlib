"""Independent, bounded search normalization; display text is never rewritten.

This is Unicode category tokenization, not a language dictionary, transliterator
or implementation of Unicode word/grapheme segmentation or text shaping.
"""
import unicodedata


def normalize_name(value, *, accents=False):
    if not isinstance(value, str) or len(value) > 4096:
        raise ValueError('Search text must be a string of at most 4096 characters')
    value = unicodedata.normalize('NFKC', value).casefold()
    if not accents:
        value = ''.join(c for c in unicodedata.normalize('NFKD', value)
                        if not unicodedata.category(c).startswith('M'))
    return ' '.join(value.split())


def tokens(value):
    words = []; word = []
    for c in normalize_name(value):
        if unicodedata.category(c)[0] in 'LNM':
            word.append(c)
        elif word:
            words.append(''.join(word)); word = []
    if word: words.append(''.join(word))
    if len(words) > 64: raise ValueError('Search text exceeds 64 tokens')
    return tuple(dict.fromkeys(words))


def grams(word):
    # Unpadded substrings also support prefixes and scripts without spaces.
    size = min(3, len(word))
    return tuple(sorted({word[i:i+size] for i in range(len(word)-size+1)}))


def edit_distance(a, b, limit=2):
    """Own bounded Levenshtein dynamic program, over Unicode code points."""
    if abs(len(a)-len(b)) > limit: return limit+1
    previous = list(range(len(b)+1))
    for i, ca in enumerate(a, 1):
        current = [i]
        for j, cb in enumerate(b, 1):
            current.append(min(current[-1]+1, previous[j]+1, previous[j-1]+(ca != cb)))
        if min(current) > limit: return limit+1
        previous = current
    return previous[-1]
