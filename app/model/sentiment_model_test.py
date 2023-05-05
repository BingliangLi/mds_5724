# -*- coding: utf-8 -*-
"""
Created on Sat Apr  1 16:22:27 2023

@author: Neal
"""

import joblib

import re
import string
from sklearn.base import BaseEstimator, TransformerMixin

try:
    import nltk
    from nltk.stem import PorterStemmer
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
        useless_words = ['i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've", "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', "she's", 'her', 'hers', 'herself', 'it', "it's", 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', "don't", 'should', "should've", 'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn', "couldn't", 'didn', "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 'hasn', "hasn't", 'haven', "haven't", 'isn', "isn't", 'ma', 'mightn', "mightn't", 'mustn', "mustn't", 'needn', "needn't", 'shan', "shan't", 'shouldn', "shouldn't", 'wasn', "wasn't", 'weren', "weren't", 'won', "won't", 'wouldn', "wouldn't"]
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
    
test_data = ["According to Scanfil , demand for telecommunications network products has fluctuated significantly in the third quarter of 2006 , and the situation is expected to remain unstable for the rest of the year .",
             "From: boylan@sltg04.ljo.dec.com (Steve Boylan)\nSubject: Re: Christian Daemons? [Biblical Demons, the update]\nReply-To: boylan@ljohub.enet.dec.com (Steve Boylan)\nOrganization: Digital Equipment Corporation\nLines: 61\n\n\nIn article <1993Apr1.024850.20111@sradzy.uucp>, radzy@sradzy.uucp\n(T.O. Radzykewycz) writes:\n\n> >>swaim@owlnet.rice.edu (Michael Parks Swaim) writes:\n> >>>  666, the file permission of the beast.\n> \n> >radzy@sradzy.uucp (T.O. Radzykewycz) writes:\n> >> Sorry, but the file permission of the beast is 600.\n> >> \n> >> And the file permission of the home directory of the\n> >> beast is 700.\n> \n> boylan@sltg04.ljo.dec.com (Steve Boylan) writes:\n> >Hey, radzy, it must depend on your system's access policy.\n> >I get:\n> >\t$ ls -lg /usr/users\n> >\ttotal 3\n> >\tdrwxrwxrwx 22 beast    system       1536 Jan 01  1970 beast\n> >\tdrwxr-x--x 32 boylan   users        2048 Mar 31 09:08 boylan\n> >\tdrwxr-xr-x  2 guest    users         512 Sep 18  1992 guest\n> >\t$ su\n> >\tPassword:\n> >\troot $ su beast\n> >\tbeast $ umask\n> >\t111\n> >\tbeast $ ^D\n> >\troot $ ^D\n> >\t$ \n> \n> Just a minute....\n> \n> \t$ grep beast /etc/passwd\n> \tbeast:k5tUk76RAUogQ:497:0:Not Walt Disney!:/usr/users/beast:\n> \t$ mv /usr/users/beast/.profile /usr/users/beast/.profile,\n> \t$ echo umask 077 >> /usr/users/beast/.profile\n> \t$ cat > /usr/users/beast/.profile\n> \tchmod 700 /usr/users/beast\n> \tmv .mailrc .mailrc,\n> \techo beast logged in | mail radzy%sradzy@jack.sns.com\n> \tmv .mailrc, .mailrc\n> \tmv /usr/users/beast/.profile, /usr/users/beast/.profile\n> \t^D\n> \t$ chmod 777 /usr/users/beast/.profile\n> \t$ cat /usr/users/beast/.profile, >> /usr/users/beast/.profile\n> \n> <waits a while, finally gets mail.>\n> \n> I think you made a mistake.  Check it again.\n> \n\nI see . . . you're not running Ultrix!\n\n\t:-)\n\n\t\t\t\t- - Steve\n\n\n--\nDon't miss the 49th New England Folk Festival,\nApril 23-25, 1993 in Natick, Massachusetts!\n"]

pipeline = joblib.load('text_sentiment_model_v001.joblib')
print(pipeline.predict(test_data))
