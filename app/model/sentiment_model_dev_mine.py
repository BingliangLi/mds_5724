# -*- coding: utf-8 -*-
"""
Created on Sat Apr  1 14:35:51 2023

@author: Neal
"""
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.naive_bayes import MultinomialNB
# lr
from sklearn.linear_model import LogisticRegression # 84.8%
# svm
from sklearn.svm import SVC # 85.3%
# knn
from sklearn.neighbors import KNeighborsClassifier # 79.3%
# dt
from sklearn.tree import DecisionTreeClassifier # 80.6%
# ElasticNet
from sklearn.linear_model import PassiveAggressiveClassifier # 82.9%
# MLPClassifier
from sklearn.neural_network import MLPClassifier # 81.9%
# SGDClassifier
from sklearn.linear_model import SGDClassifier # 84.4%
# RidgeClassifier
from sklearn.linear_model import RidgeClassifier # 85.9%
# BernoulliNB
from sklearn.naive_bayes import BernoulliNB # 84.8%
# LGBMClassifier
from lightgbm import LGBMClassifier # 83.9%
import pandas as pd
import joblib

##############################################################################
import re
import string
import nltk
from nltk.stem import PorterStemmer
from sklearn.base import BaseEstimator, TransformerMixin

# #############################################################################
# Define a pipeline combining a text feature extractor with a simple

try:
    nltk.download('stopwords')
    # raise Exception
except:
    class PorterStemmer:
        def isCons(self, letter):
            if letter == 'a' or letter == 'e' or letter == 'i' or letter == 'o' or letter == 'u':
                return False
            else:
                return True

        def isConsonant(self, word, i):
            letter = word[i]
            if self.isCons(letter):
                if letter == 'y' and self.isCons(word[i-1]):
                    return False
                else:
                    return True
            else:
                return False

        def isVowel(self, word, i):
            return not (self.isConsonant(word, i))

        # *S
        def endsWith(self, stem, letter):
            if stem.endswith(letter):
                return True
            else:
                return False

        # *v*
        def containsVowel(self, stem):
            for i in stem:
                if not self.isCons(i):
                    return True
            return False

        # *d
        def doubleCons(self, stem):
            if len(stem) >= 2:
                if self.isConsonant(stem, -1) and self.isConsonant(stem, -2):
                    return True
                else:
                    return False
            else:
                return False

        def getForm(self, word):
            form = []
            formStr = ''
            for i in range(len(word)):
                if self.isConsonant(word, i):
                    if i != 0:
                        prev = form[-1]
                        if prev != 'C':
                            form.append('C')
                    else:
                        form.append('C')
                else:
                    if i != 0:
                        prev = form[-1]
                        if prev != 'V':
                            form.append('V')
                    else:
                        form.append('V')
            for j in form:
                formStr += j
            return formStr

        def getM(self, word):
            form = self.getForm(word)
            m = form.count('VC')
            return m

        # *o
        def cvc(self, word):
            if len(word) >= 3:
                f = -3
                s = -2
                t = -1
                third = word[t]
                if self.isConsonant(word, f) and self.isVowel(word, s) and self.isConsonant(word, t):
                    if third != 'w' and third != 'x' and third != 'y':
                        return True
                    else:
                        return False
                else:
                    return False
            else:
                return False

        def replace(self, orig, rem, rep):
            result = orig.rfind(rem)
            base = orig[:result]
            replaced = base + rep
            return replaced

        def replaceM0(self, orig, rem, rep):
            result = orig.rfind(rem)
            base = orig[:result]
            if self.getM(base) > 0:
                replaced = base + rep
                return replaced
            else:
                return orig

        def replaceM1(self, orig, rem, rep):
            result = orig.rfind(rem)
            base = orig[:result]
            if self.getM(base) > 1:
                replaced = base + rep
                return replaced
            else:
                return orig

        def step1a(self, word):
            if word.endswith('sses'):
                word = self.replace(word, 'sses', 'ss')
            elif word.endswith('ies'):
                word = self.replace(word, 'ies', 'i')
            elif word.endswith('ss'):
                word = self.replace(word, 'ss', 'ss')
            elif word.endswith('s'):
                word = self.replace(word, 's', '')
            else:
                pass
            return word

        def step1b(self, word):
            flag = False
            if word.endswith('eed'):
                result = word.rfind('eed')
                base = word[:result]
                if self.getM(base) > 0:
                    word = base
                    word += 'ee'
            elif word.endswith('ed'):
                result = word.rfind('ed')
                base = word[:result]
                if self.containsVowel(base):
                    word = base
                    flag = True
            elif word.endswith('ing'):
                result = word.rfind('ing')
                base = word[:result]
                if self.containsVowel(base):
                    word = base
                    flag = True
            if flag:
                if word.endswith('at') or word.endswith('bl') or word.endswith('iz'):
                    word += 'e'
                elif self.doubleCons(word) and not self.endsWith(word, 'l') and not self.endsWith(word, 's') and not self.endsWith(word, 'z'):
                    word = word[:-1]
                elif self.getM(word) == 1 and self.cvc(word):
                    word += 'e'
                else:
                    pass
            else:
                pass
            return word

        def step1c(self, word):
            if word.endswith('y'):
                result = word.rfind('y')
                base = word[:result]
                if self.containsVowel(base):
                    word = base
                    word += 'i'
            return word

        def step2(self, word):
            if word.endswith('ational'):
                word = self.replaceM0(word, 'ational', 'ate')
            elif word.endswith('tional'):
                word = self.replaceM0(word, 'tional', 'tion')
            elif word.endswith('enci'):
                word = self.replaceM0(word, 'enci', 'ence')
            elif word.endswith('anci'):
                word = self.replaceM0(word, 'anci', 'ance')
            elif word.endswith('izer'):
                word = self.replaceM0(word, 'izer', 'ize')
            elif word.endswith('abli'):
                word = self.replaceM0(word, 'abli', 'able')
            elif word.endswith('alli'):
                word = self.replaceM0(word, 'alli', 'al')
            elif word.endswith('entli'):
                word = self.replaceM0(word, 'entli', 'ent')
            elif word.endswith('eli'):
                word = self.replaceM0(word, 'eli', 'e')
            elif word.endswith('ousli'):
                word = self.replaceM0(word, 'ousli', 'ous')
            elif word.endswith('ization'):
                word = self.replaceM0(word, 'ization', 'ize')
            elif word.endswith('ation'):
                word = self.replaceM0(word, 'ation', 'ate')
            elif word.endswith('ator'):
                word = self.replaceM0(word, 'ator', 'ate')
            elif word.endswith('alism'):
                word = self.replaceM0(word, 'alism', 'al')
            elif word.endswith('iveness'):
                word = self.replaceM0(word, 'iveness', 'ive')
            elif word.endswith('fulness'):
                word = self.replaceM0(word, 'fulness', 'ful')
            elif word.endswith('ousness'):
                word = self.replaceM0(word, 'ousness', 'ous')
            elif word.endswith('aliti'):
                word = self.replaceM0(word, 'aliti', 'al')
            elif word.endswith('iviti'):
                word = self.replaceM0(word, 'iviti', 'ive')
            elif word.endswith('biliti'):
                word = self.replaceM0(word, 'biliti', 'ble')
            return word

        def step3(self, word):
            if word.endswith('icate'):
                word = self.replaceM0(word, 'icate', 'ic')
            elif word.endswith('ative'):
                word = self.replaceM0(word, 'ative', '')
            elif word.endswith('alize'):
                word = self.replaceM0(word, 'alize', 'al')
            elif word.endswith('iciti'):
                word = self.replaceM0(word, 'iciti', 'ic')
            elif word.endswith('ful'):
                word = self.replaceM0(word, 'ful', '')
            elif word.endswith('ness'):
                word = self.replaceM0(word, 'ness', '')
            return word

        def step4(self, word):
            if word.endswith('al'):
                word = self.replaceM1(word, 'al', '')
            elif word.endswith('ance'):
                word = self.replaceM1(word, 'ance', '')
            elif word.endswith('ence'):
                word = self.replaceM1(word, 'ence', '')
            elif word.endswith('er'):
                word = self.replaceM1(word, 'er', '')
            elif word.endswith('ic'):
                word = self.replaceM1(word, 'ic', '')
            elif word.endswith('able'):
                word = self.replaceM1(word, 'able', '')
            elif word.endswith('ible'):
                word = self.replaceM1(word, 'ible', '')
            elif word.endswith('ant'):
                word = self.replaceM1(word, 'ant', '')
            elif word.endswith('ement'):
                word = self.replaceM1(word, 'ement', '')
            elif word.endswith('ment'):
                word = self.replaceM1(word, 'ment', '')
            elif word.endswith('ent'):
                word = self.replaceM1(word, 'ent', '')
            elif word.endswith('ou'):
                word = self.replaceM1(word, 'ou', '')
            elif word.endswith('ism'):
                word = self.replaceM1(word, 'ism', '')
            elif word.endswith('ate'):
                word = self.replaceM1(word, 'ate', '')
            elif word.endswith('iti'):
                word = self.replaceM1(word, 'iti', '')
            elif word.endswith('ous'):
                word = self.replaceM1(word, 'ous', '')
            elif word.endswith('ive'):
                word = self.replaceM1(word, 'ive', '')
            elif word.endswith('ize'):
                word = self.replaceM1(word, 'ize', '')
            elif word.endswith('ion'):
                result = word.rfind('ion')
                base = word[:result]
                if self.getM(base) > 1 and (self.endsWith(base, 's') or self.endsWith(base, 't')):
                    word = base
                word = self.replaceM1(word, '', '')
            return word

        def step5a(self, word):
            if word.endswith('e'):
                base = word[:-1]
                if self.getM(base) > 1:
                    word = base
                elif self.getM(base) == 1 and not self.cvc(base):
                    word = base
            return word

        def step5b(self, word):
            if self.getM(word) > 1 and self.doubleCons(word) and self.endsWith(word, 'l'):
                word = word[:-1]
            return word

        def stem(self, word):
            word = self.step1a(word)
            word = self.step1b(word)
            word = self.step1c(word)
            word = self.step2(word)
            word = self.step3(word)
            word = self.step4(word)
            word = self.step5a(word)
            word = self.step5b(word)
            return word


class CleanText(BaseEstimator, TransformerMixin):
    def __init__(self, stem="None"):
        self.stem = stem

    def clean_string(self, text):
        final_string = ""

        # Make lower
        text = text.lower()

        # Remove line breaks
        text = re.sub(r'\n', '', text)

        # Remove puncuation
        translator = str.maketrans('', '', string.punctuation)
        text = text.translate(translator)

        # Remove stop words
        text = text.split()
        useless_words = nltk.corpus.stopwords.words("english")
        useless_words = useless_words + ['hi', 'im']

        text_filtered = [word for word in text if not word in useless_words]

        # Remove numbers
        text_filtered = [re.sub(r'\w*\d\w*', '', w) for w in text_filtered]

        # Stem or Lemmatize
        if self.stem == 'Stem':
            stemmer = PorterStemmer() 
            text_stemmed = [stemmer.stem(y) for y in text_filtered]
        elif self.stem == 'Lem':
            # Raise NotImplementedError
            raise NotImplementedError
            # lem = WordNetLemmatizer()
            # text_stemmed = [lem.lemmatize(y) for y in text_filtered]
        elif self.stem == 'Spacy':
            raise NotImplementedError
            # nlp = spacy.load('en_core_web_sm')
            # text_filtered = nlp(' '.join(text_filtered))
            # text_stemmed = [y.lemma_ for y in text_filtered]
        else:
            text_stemmed = text_filtered

        final_string = ' '.join(text_stemmed)

        return final_string

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X_cleaned = [self.clean_string(text) for text in X]
        return X_cleaned
# classifier
pipeline = Pipeline([
    ('cleanText', CleanText(stem='Stem')),
    ('vect', CountVectorizer(ngram_range=(1, 1))),
    ('tfidf', TfidfTransformer(use_idf=False, norm='l2')),
    # ('clf', LGBMClassifier(learning_rate=0.16, max_depth=7, num_leaves=8)),
    ('clf', RidgeClassifier(alpha=1.4, class_weight={-1: 1.05, 1: 1}))
])

# uncommenting more parameters will give better exploring power but will
# increase processing time in a combinatorial way
parameters = {
    'vect__max_df': (0.4, 0.5),
    # 'vect__ngram_range': ((1, 1)),
    # 'tfidf__use_idf': (True, False),
    # 'tfidf__norm': ('l1', 'l2'),
    # MultinomialNB parameters
    
    # lightgbm parameters
    # 'clf__num_leaves': (7, 8, 9, 10),
    # 'clf__max_depth': (5, 6, 7, 8),
    # 'clf__learning_rate': (0.16, 0.2, 0.23, 0.26),
    
    # RidgeClassifier parameters
    # 'clf__alpha': (0.9, 1, 1.1, 1.2, 1.3, 1.4, 1.5),
    # 'clf__solver': ('auto', 'sparse_cg',),
    # 'clf__class_weight': ('balanced', None, {-1: 1.05, 1: 1}),
    # 'clf__fit_intercept': (True, False),
}

if __name__ == "__main__":
    # multiprocessing requires the fork to happen in a __main__ protected
    # block

    # find the best parameters for both the feature extraction and the
    # classifier
    
    print('Performing grid search...')
    
    grid_search = GridSearchCV(pipeline, parameters, scoring='f1', n_jobs=-1, verbose=1)
    df = pd.read_excel('./data/Task-2/train.xlsx')
    X= df.text
    grid_search.fit(df.text,df.label)
    print("Performing grid search...")
    print("pipeline:", [name for name, _ in pipeline.steps])
    print("parameters:")
    print("Best score: %0.3f" % grid_search.best_score_)
    print("Best parameters set:")
    best_parameters = grid_search.best_estimator_.get_params()
    for param_name in sorted(parameters.keys()):
        print("\t%s: %r" % (param_name, best_parameters[param_name]))
    joblib.dump(grid_search, "text_sentiment_model_v001.joblib")