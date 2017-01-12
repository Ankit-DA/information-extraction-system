from itertools import chain
import nltk
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import LabelBinarizer
import sklearn
import pycrfsuite
import csv
import math
import io

from generate_database import GenerateDataset

class CrfSuite:

    train_sents = []
    test_sents = []

    total_sents = []

    
    def get_dataset(self):
        gd = GenerateDataset()
        total_sents = gd.read_tagged_tokens()
        print("Read " + str(len(total_sents)) + " documents")

    def split_dataset(self):
        split_point = math.ceil(len(total_sents) * 0.7)
        train_sents = total_sents[0:split_point]
        test_sents = total_sents[split_point+1:]
        print("Split dataset")


    def first_letter_upper(token):
        return token[0].isupper()

    def word2features(sent, i):
        word = sent[i][0]
        postag = sent[i][1]
        nonlocalnertag = sent[i][2]
        features = [
            'bias',
            'word.lower=' + word.lower(),
            'word[-3:]=' + word[-3:],
            'word[-2:]=' + word[-2:],
            'word.isupper=%s' % word.isupper(),
            'word.istitle=%s' % word.istitle(),
            'word.isdigit=%s' % word.isdigit(),
            'word.firstletterupper=%s' % first_letter_upper(word),
            'word.idx=' + str(i),
            'postag=' + postag,
            'postag[:2]=' + postag[:2],
            'nonlocalnertag=' + nonlocalnertag,
        ]
        
        if i > 0:
            word1 = sent[i-1][0]
            postag1 = sent[i-1][1]
            nonlocalnertag1 = sent[i-1][2]
            features.extend([
                '-1:word.lower=' + word1.lower(),
                '-1:word.istitle=%s' % word1.istitle(),
                '-1:word.isupper=%s' % word1.isupper(),
                '-1word.firstletterupper=%s' % first_letter_upper(word1),
                '-1word.idx=' + str(i-1),
                '-1:postag=' + postag1,
                '-1:postag[:2]=' + postag1[:2],
                '-1:nonlocalnertag=' + nonlocalnertag,
            ])
        else:
            features.append('BOD')
            
        if i < len(sent)-1:
            word1 = sent[i+1][0]
            postag1 = sent[i+1][1]
            nonlocalnertag1 = sent[i+1][2]
            features.extend([
                '+1:word.lower=' + word1.lower(),
                '+1:word.istitle=%s' % word1.istitle(),
                '+1:word.isupper=%s' % word1.isupper(),
                '+1word.firstletterupper=%s' % first_letter_upper(word1),
                '+1word.idx=' + str(i+1),
                '+1:postag=' + postag1,
                '+1:postag[:2]=' + postag1[:2],
                '+1:nonlocalnertag=' + nonlocalnertag,
            ])

        else:
            features.append('EOD')

        return features

    def sent2features(sent):
        return [word2features(sent, i) for i in range(len(sent))]

    def sent2labels(sent):
        return [label for token, postag, nonlocalnertag, label in sent]

    def sent2tokens(sent):
        return [token for token, postag, nonlocalnertag, label in sent] 

    def generate_features(self):
        X_train = [sent2features(s) for s in train_sents]
        y_train = [sent2labels(s) for s in train_sents]

        X_test = [sent2features(s) for s in test_sents]
        y_test = [sent2labels(s) for s in test_sents]
        print("Features created for train and test data")

    def train_model(self):
        trainer = pycrfsuite.Trainer(verbose=True)
        print("pycrfsuite Trainer init")

        for xseq, yseq in zip(X_train, y_train):
            trainer.append(xseq, yseq)
        print("pycrfsuite Trainer has data")

        trainer.set_params({
            'c1': 1.0,   # coefficient for L1 penalty
            'c2': 1,  # coefficient for L2 penalty
            'max_iterations': 50,  # stop earlier

            # include transitions that are possible, but not observed
            'feature.possible_transitions': True
        })
        print(trainer.params())
        trainer.train('test_NER.crfsuite')

print("printint last iteration")
print(trainer.logparser.last_iteration)

print(str(len(trainer.logparser.iterations)) + ", " +
        str(trainer.logparser.iterations[-1]))

#predictions
tagger = pycrfsuite.Tagger()
tagger.open('test_NER.crfsuite')

# example tag
example_sent = test_sents[0]
print(' '.join(sent2tokens(example_sent)), end='\n\n')

print("Predicted:", ' '.join(tagger.tag(sent2features(example_sent))))
print("Correct:  ", ' '.join(sent2labels(example_sent)))

#evaluate model
def bio_classification_report(y_true, y_pred):

    """
    Classification report for a list of BIO-encoded sequences.
    It computes token-level metrics and discards "O" labels.
    
    Note that it requires scikit-learn 0.15+ (or a version from github master)
    to calculate averages properly!
    """

    lb = LabelBinarizer()
    y_true_combined = lb.fit_transform(list(chain.from_iterable(y_true)))
    y_pred_combined = lb.transform(list(chain.from_iterable(y_pred)))
        
    tagset = set(lb.classes_) - {'O'}
    tagset = sorted(tagset, key=lambda tag: tag.split('-', 1)[::-1])
    class_indices = {cls: idx for idx, cls in enumerate(lb.classes_)}
    
    return classification_report(
        y_true_combined,
        y_pred_combined,
        labels = [class_indices[cls] for cls in tagset],
        target_names = tagset,
    )

y_pred = [tagger.tag(xseq) for xseq in X_test]

def basic_classification_report(y_true, y_pred):
    lb = LabelBinarizer()
    y_true_combined = lb.fit_transform(list(chain.from_iterable(y_true)))
    y_pred_combined = lb.transform(list(chain.from_iterable(y_pred)))

    return classification_report(y_true_combined, y_pred_combined)

print(basic_classification_report(y_test, y_pred))

#print(bio_classification_report(y_test, y_pred))