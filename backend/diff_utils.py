import difflib
import re
from typing import Dict, List

def split_into_sentences_or_chunks(text: str) -> List[str]:
    """Splits text into readable sentences or paragraph blocks."""
    if not text:
        return []
    # Split on sentence boundaries (. ! ?) or line breaks
    chunks = re.split(r'(?<=[.!?])\s+|\n+', text)
    return [c.strip() for c in chunks if c.strip()]

def generate_content_diff(text1: str, text2: str) -> Dict:
    """
    Computes differences between main page text of two pages:
    - shared_content: list of text chunks common to both
    - unique_to_page1: list of text chunks present only on page 1
    - unique_to_page2: list of text chunks present only on page 2
    - diff_tokens_p1: word tokens with status ('equal', 'delete')
    - diff_tokens_p2: word tokens with status ('equal', 'insert')
    """
    chunks1 = split_into_sentences_or_chunks(text1)
    chunks2 = split_into_sentences_or_chunks(text2)

    matcher = difflib.SequenceMatcher(None, chunks1, chunks2)
    shared_chunks = []
    unique_p1 = []
    unique_p2 = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            shared_chunks.extend(chunks1[i1:i2])
        elif tag == 'delete':
            unique_p1.extend(chunks1[i1:i2])
        elif tag == 'insert':
            unique_p2.extend(chunks2[j1:j2])
        elif tag == 'replace':
            unique_p1.extend(chunks1[i1:i2])
            unique_p2.extend(chunks2[j1:j2])

    # Word-level inline diff for high-precision side-by-side view
    words1 = re.findall(r'\S+', text1)
    words2 = re.findall(r'\S+', text2)
    word_matcher = difflib.SequenceMatcher(None, words1, words2)

    diff_tokens1 = []
    diff_tokens2 = []

    for tag, i1, i2, j1, j2 in word_matcher.get_opcodes():
        if tag == 'equal':
            for w in words1[i1:i2]:
                diff_tokens1.append({'text': w, 'type': 'same'})
            for w in words2[j1:j2]:
                diff_tokens2.append({'text': w, 'type': 'same'})
        elif tag == 'delete':
            for w in words1[i1:i2]:
                diff_tokens1.append({'text': w, 'type': 'removed'})
        elif tag == 'insert':
            for w in words2[j1:j2]:
                diff_tokens2.append({'text': w, 'type': 'added'})
        elif tag == 'replace':
            for w in words1[i1:i2]:
                diff_tokens1.append({'text': w, 'type': 'removed'})
            for w in words2[j1:j2]:
                diff_tokens2.append({'text': w, 'type': 'added'})

    return {
        'shared_content': shared_chunks,
        'unique_to_page1': unique_p1,
        'unique_to_page2': unique_p2,
        'diff_tokens_p1': diff_tokens1[:500],  # Limit size for fast transfer
        'diff_tokens_p2': diff_tokens2[:500]
    }

def get_detailed_pair_comparison(page1: Dict, page2: Dict, pair_summary: Dict) -> Dict:
    """
    Constructs a complete comparison object for side-by-side diff view.
    """
    text1 = page1.get('main_text', '')
    text2 = page2.get('main_text', '')
    diff_data = generate_content_diff(text1, text2)

    h1_1 = page1.get('h1', [])
    h1_2 = page2.get('h1', [])
    h2_1 = page1.get('h2', [])
    h2_2 = page2.get('h2', [])

    return {
        'pair_id': pair_summary.get('pair_id'),
        'url1': page1.get('original_url'),
        'url2': page2.get('original_url'),
        'final_url1': page1.get('final_url'),
        'final_url2': page2.get('final_url'),
        'similarity_score': pair_summary.get('similarity_score'),
        'classification': pair_summary.get('classification'),
        'recommended_action': pair_summary.get('recommended_action'),
        # Titles
        'title1': page1.get('title', ''),
        'title2': page2.get('title', ''),
        'title_match': pair_summary.get('title_match', False),
        # Meta description
        'meta_desc1': page1.get('meta_description', ''),
        'meta_desc2': page2.get('meta_description', ''),
        # Headings
        'h1_1': h1_1,
        'h1_2': h1_2,
        'h1_match': pair_summary.get('h1_match', False),
        'h2_1': h2_1,
        'h2_2': h2_2,
        # Canonicals
        'canonical1': page1.get('canonical_url'),
        'canonical2': page2.get('canonical_url'),
        'same_canonical': pair_summary.get('same_canonical', False),
        'canonical_status': pair_summary.get('canonical_status'),
        # Status & Stats
        'status_code1': page1.get('status_code'),
        'status_code2': page2.get('status_code'),
        'word_count1': page1.get('word_count', 0),
        'word_count2': page2.get('word_count', 0),
        # Diff Content
        'shared_content': diff_data['shared_content'],
        'unique_to_page1': diff_data['unique_to_page1'],
        'unique_to_page2': diff_data['unique_to_page2'],
        'diff_tokens_p1': diff_data['diff_tokens_p1'],
        'diff_tokens_p2': diff_data['diff_tokens_p2']
    }
