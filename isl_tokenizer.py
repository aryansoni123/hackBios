# isl_tokenizer.py
import os
import sys
import time
import zipfile
import pprint
import ssl
import re
from typing import List, Tuple, Dict

# stanza for tokenization/lemmatization
import stanza
stanza.download('en', model_dir='stanza_resources', verbose=False)
en_nlp = stanza.Pipeline('en', processors={'tokenize': 'spacy'}, verbose=False)

# NLTK / Stanford Parser
from nltk.parse.stanford import StanfordParser
from nltk.tree import ParentedTree

# glue to make TLS downloads work in some envs
ssl._create_default_https_context = ssl._create_unverified_context

# default base dir (folder containing this file)
BASE_DIR = os.path.dirname(os.path.realpath(__file__))

# Default stanford dir names (matches your script)
stanford_dir = os.path.join(BASE_DIR, 'stanford-parser-full-2018-10-17')
os.environ.setdefault('CLASSPATH', stanford_dir)
os.environ.setdefault('STANFORD_PARSER', os.path.join(stanford_dir, 'stanford-parser.jar'))
os.environ.setdefault('STANFORD_MODELS', os.path.join(stanford_dir,
                                                     'edu/stanford/nlp/models/lexparser/englishPCFG.ser.gz'))

# Stop words to remove (same as your list)
STOP_WORDS = set([
    "am","are","is","was","were","be","being","been",
    "have","has","had","does","did","could","should","would",
    "can","shall","will","may","might","must","let"
])

# --------- Utilities to download/extract Stanford parser if missing ----------
def is_parser_jar_file_present():
    stanford_parser_zip_file_path = os.environ.get('CLASSPATH') + ".jar"
    return os.path.exists(stanford_parser_zip_file_path)

def reporthook(count, block_size, total_size):
    global start_time
    if count == 0:
        start_time = time.perf_counter()
        return
    duration = time.perf_counter() - start_time
    progress_size = int(count * block_size)
    speed = int(progress_size / (1024 * duration)) if duration > 0 else 0
    percent = min(int(count*block_size*100/total_size),100) if total_size else 0
    sys.stdout.write("\r...%d%%, %d MB, %d KB/s, %d seconds passed" %
                    (percent, progress_size / (1024 * 1024), speed, duration))
    sys.stdout.flush()

def download_parser_jar_file():
    from six.moves import urllib
    stanford_parser_zip_file_path = os.environ.get('CLASSPATH') + ".jar"
    url = "https://nlp.stanford.edu/software/stanford-parser-full-2018-10-17.zip"
    print("Downloading Stanford parser zip (this can be large)...")
    urllib.request.urlretrieve(url, stanford_parser_zip_file_path, reporthook)
    print("\nDownload complete:", stanford_parser_zip_file_path)

def extract_parser_jar_file():
    stanford_parser_zip_file_path = os.environ.get('CLASSPATH') + ".jar"
    if not os.path.exists(stanford_parser_zip_file_path):
        raise FileNotFoundError(f"Stanford parser zip not found at {stanford_parser_zip_file_path}")
    print("Extracting Stanford parser zip...")
    with zipfile.ZipFile(stanford_parser_zip_file_path) as z:
        z.extractall(path=BASE_DIR)
    print("Extraction complete.")

def extract_models_jar_file():
    stanford_models_zip_file_path = os.path.join(os.environ.get('CLASSPATH'), 'stanford-parser-3.9.2-models.jar')
    stanford_models_dir = os.environ.get('CLASSPATH')
    if not os.path.exists(stanford_models_zip_file_path):
        raise FileNotFoundError(f"Stanford models jar not found at {stanford_models_zip_file_path}")
    with zipfile.ZipFile(stanford_models_zip_file_path) as z:
        z.extractall(path=stanford_models_dir)

def download_required_packages():
    # safe: only run if required files missing
    if not os.path.exists(os.environ.get('CLASSPATH')):
        if is_parser_jar_file_present():
            # If zip exists but not extracted, extract it
            extract_parser_jar_file()
        else:
            download_parser_jar_file()
            extract_parser_jar_file()

    if not os.path.exists(os.environ.get('STANFORD_MODELS')):
        try:
            extract_models_jar_file()
        except FileNotFoundError:
            # models jar may be inside the zip already extracted; ignore if missing
            pass

# ----------------- Core pipeline functions (ported from your script) -----------------

def convert_to_sentence_list(doc):
    sent_list = []
    sent_list_detailed = []
    for sentence in doc.sentences:
        sent_list.append(sentence.text)
        sent_list_detailed.append(sentence)
    return sent_list, sent_list_detailed

def convert_to_word_list(sent_list_detailed):
    word_list = []
    word_list_detailed = []
    for sentence in sent_list_detailed:
        temp_list = []
        temp_list_detailed = []
        for word in sentence.words:
            temp_list.append(word.text)
            temp_list_detailed.append(word)
        word_list.append(temp_list.copy())
        word_list_detailed.append(temp_list_detailed.copy())
    return word_list, word_list_detailed

def remove_punct(word_list, word_list_detailed):
    # remove punctuation tokens (in-place)
    for words, words_detailed in zip(word_list, word_list_detailed):
        # iterate backwards to safely delete
        for i in range(len(words_detailed)-1, -1, -1):
            if words_detailed[i].upos == 'PUNCT':
                del words_detailed[i]
                # remove corresponding token in words (first matching)
                try:
                    words.remove(words_detailed[i].text)  # may raise if modified; tolerate
                except Exception:
                    pass

def filter_words(word_list, word_list_detailed):
    final_words = []
    # remove stop words from word_list
    for words in word_list:
        temp = [w for w in words if w.lower() not in STOP_WORDS]
        final_words.append(temp)
    # remove stop words from word_list_detailed (modify in place)
    for words in word_list_detailed:
        for i in range(len(words)-1, -1, -1):
            if words[i].text.lower() in STOP_WORDS:
                del words[i]
    return final_words

def lemmatize(final_word_list, word_list_detailed):
    # Replace tokens in final_word_list by their lemmas from word_list_detailed (if available)
    for words_detailed, final in zip(word_list_detailed, final_word_list):
        for i in range(len(final)):
            if i < len(words_detailed):
                wobj = words_detailed[i]
                # if final entry is single letter keep it
                if len(final[i]) == 1:
                    final[i] = final[i]
                else:
                    final[i] = getattr(wobj, 'lemma', final[i])

# ---------- Functions that modify parse tree (ported) -----------------
def label_parse_subtrees(parent_tree):
    tree_traversal_flag = {}
    for sub_tree in parent_tree.subtrees():
        tree_traversal_flag[sub_tree.treeposition()] = 0
    return tree_traversal_flag

def handle_noun_clause(i, tree_traversal_flag, modified_parse_tree, sub_tree):
    if tree_traversal_flag[sub_tree.treeposition()] == 0 and tree_traversal_flag[sub_tree.parent().treeposition()] == 0:
        tree_traversal_flag[sub_tree.treeposition()] = 1
        modified_parse_tree.insert(i, sub_tree)
        i = i + 1
    return i, modified_parse_tree

def handle_verb_prop_clause(i, tree_traversal_flag, modified_parse_tree, sub_tree):
    for child_sub_tree in sub_tree.subtrees():
        if child_sub_tree.label() == "NP" or child_sub_tree.label() == 'PRP':
            if tree_traversal_flag[child_sub_tree.treeposition()] == 0 and tree_traversal_flag[child_sub_tree.parent().treeposition()] == 0:
                tree_traversal_flag[child_sub_tree.treeposition()] = 1
                modified_parse_tree.insert(i, child_sub_tree)
                i = i + 1
    return i, modified_parse_tree

def modify_tree_structure(parent_tree):
    tree_traversal_flag = label_parse_subtrees(parent_tree)
    modified_parse_tree = ParentedTree('ROOT', [])
    i = 0
    for sub_tree in parent_tree.subtrees():
        if sub_tree.label() == "NP":
            i, modified_parse_tree = handle_noun_clause(i, tree_traversal_flag, modified_parse_tree, sub_tree)
        if sub_tree.label() == "VP" or sub_tree.label() == "PRP":
            i, modified_parse_tree = handle_verb_prop_clause(i, tree_traversal_flag, modified_parse_tree, sub_tree)

    # insert omitted single-leaf clauses
    for sub_tree in parent_tree.subtrees():
        for child_sub_tree in sub_tree.subtrees():
            if len(child_sub_tree.leaves()) == 1:
                if tree_traversal_flag[child_sub_tree.treeposition()] == 0 and tree_traversal_flag[child_sub_tree.parent().treeposition()] == 0:
                    tree_traversal_flag[child_sub_tree.treeposition()] = 1
                    modified_parse_tree.insert(i, child_sub_tree)
                    i = i + 1

    return modified_parse_tree

# ---------------- reorder_eng_to_isl (uses StanfordParser) ------------------
def reorder_eng_to_isl(word_list: List[str]) -> List[str]:
    """
    word_list: list of tokens for one sentence (strings)
    returns reordered list (based on parse) or original if parser unavailable/errors
    """
    # ensure stanford parser resources available (downloads/extracts if needed)
    try:
        download_required_packages()
    except Exception:
        # if download fails, just continue and attempt parser (it will error if jars missing)
        pass

    # if all words are single letters then skip parsing
    if all(len(w) == 1 for w in word_list):
        return word_list

    # attempt parsing with StanfordParser (NLTK wrapper)
    try:
        parser = StanfordParser(path_to_jar=os.environ.get('STANFORD_PARSER'),
                                model_path=os.environ.get('STANFORD_MODELS'))
        # parser.parse expects a list of tokens or a sentence string; we pass the token list
        possible_parse_tree_list = [tree for tree in parser.parse(word_list)]
        if not possible_parse_tree_list:
            return word_list
    except Exception as e:
        # parser initialization failed (common causes: Java missing or wrong CLASSPATH)
        # fallback to original order
        # print("StanfordParser init/parse failed:", e)
        return word_list

    parse_tree = possible_parse_tree_list[0]
    parent_tree = ParentedTree.convert(parse_tree)
    modified_parse_tree = modify_tree_structure(parent_tree)
    parsed_sent = modified_parse_tree.leaves()
    return parsed_sent

# ---------------- final_output: map words -> words.txt or letters ----------------
def final_output(word_sequence: List[str], words_txt_path: str) -> List[str]:
    """
    For each word in sequence, if the exact word exists in words.txt -> keep it,
    otherwise fall back to letters (each letter as separate token).
    """
    # load valid words (lowercase)
    if not os.path.exists(words_txt_path):
        raise FileNotFoundError(f"words.txt not found at: {words_txt_path}")
    with open(words_txt_path, 'r', encoding='utf-8') as f:
        valid_words = [ln.strip().lower() for ln in f if ln.strip()]
    valid_set = set([w.replace(" ", "_") for w in valid_words])

    fin_words = []
    for word in word_sequence:
        w = word.lower()
        w_norm = w.replace(" ", "_")
        if w_norm in valid_set:
            fin_words.append(w_norm)
        else:
            # fall back to characters (letters)
            for ch in w:
                if ch == "_":
                    continue
                fin_words.append(ch.lower())
    return fin_words

# ---------------- top-level function: text_to_isl ----------------
def text_to_isl(text: str, words_txt_path: str) -> Tuple[List[str], List[str], Dict]:
    """
    Convert input text -> list of final tokens and filenames.
    Returns (tokens, filenames, meta)
    meta includes parser_used flag and any errors.
    """
    meta = {"parser_used": False, "parser_error": None}

    # sanitize input
    txt = text.strip().replace("\n", " ").replace("\t", " ").strip()
    if not txt:
        return [], [], meta

    # run stanza tokenizer
    doc = en_nlp(txt)
    sent_list, sent_list_detailed = convert_to_sentence_list(doc)
    word_list, word_list_detailed = convert_to_word_list(sent_list_detailed)

    # reorder each sentence with parser
    reordered_sentences = []
    for words in word_list:
        try:
            reordered = reorder_eng_to_isl(words)
            reordered_sentences.append(reordered)
            meta["parser_used"] = True
        except Exception as e:
            meta["parser_used"] = False
            meta["parser_error"] = str(e)
            reordered_sentences.append(words)

    # preprocess: remove punctuation & filter stopwords & lemmatize (as per your script)
    # run remove_punct in place (it expects lists)
    # but our remove_punct expects both lists; we already have word_list and word_list_detailed
    try:
        remove_punct(word_list, word_list_detailed)
    except Exception:
        pass

    final_words = filter_words(reordered_sentences, word_list_detailed)
    # lemmatize final_words using word_list_detailed
    try:
        lemmatize(final_words, word_list_detailed)
    except Exception:
        pass

    # convert to final token list with letter fallbacks
    final_tokens = []
    for words in final_words:
        out = final_output(words, words_txt_path)
        final_tokens.append(out)

    # flatten sequences if multiple sentences
    flat_tokens = [tok for sent in final_tokens for tok in sent]
    filenames = [t + ".sigml" if len(t) > 1 else t.upper() + ".sigml" for t in flat_tokens]  # letters uppercase for sigml naming
    meta["sentences"] = len(reordered_sentences)
    return flat_tokens, filenames, meta

# ---------------- CLI test ----------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ISL Tokenizer (stanford + stanza pipeline)")
    parser.add_argument("--words", "-w", required=True, help="path to words.txt (one token per line)")
    parser.add_argument("--text", "-t", required=True, help="input english text (quoted)")
    args = parser.parse_args()

    tokens, files, meta = text_to_isl(args.text, args.words)
    print("Input:", args.text)
    print("Tokens:", tokens)
    print("Filenames:", files)
    print("Meta:", meta)
