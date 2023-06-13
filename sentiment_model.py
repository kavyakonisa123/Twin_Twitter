import joblib

import pandas as pd
import numpy as np
import re
import emoji
import contractions
import nltk

import warnings
warnings.filterwarnings('ignore')
from nltk.tokenize import word_tokenize
nltk.download('punkt')
import string
from nltk.corpus import stopwords
nltk.download('stopwords')

from nltk.stem.snowball import SnowballStemmer

from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
nltk.download('wordnet')

from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score
from sklearn.metrics import classification_report, confusion_matrix


def simple_lr(X_train,X_test,Y_train,Y_test):
  model_var = fit_lr(X_train, Y_train)
  joblib.dump(model_var, 'sentiment_model.joblib')

  print(model_var.coef_, model_var.intercept_)
  y_pred_lr = model_var.predict(X_test)
  print(classification_report(Y_test, y_pred_lr))
  return accuracy_score(Y_test, y_pred_lr)

def fit_lr(X_train, y_train):
  model = LogisticRegression(solver='liblinear')
  model.fit(X_train, y_train)
  return model

def fit_tfidf(tweet_corpus):
  tf_vect = TfidfVectorizer(preprocessor=lambda x: x,
                            tokenizer=lambda x: x)
  tf_vect.fit(tweet_corpus)
  return tf_vect

def cleaning_tweets(tweet, user_name=" user ",blank_space=""):
    tweet = re.sub(r'(^|[^@\w])@(\w{1,15})|@\s(\w{1,15})\b',user_name,tweet)
    tweet=emoji.demojize(tweet)
    tweet = re.sub('(https?|http)://[-a-zA-Z0-9+&@#/%?=~_|!:,.;]*[-a-zA-Z0-9+&@#/%=~_|]',blank_space,tweet)
    tweet = re.sub('#+',blank_space,tweet)
    tweet= tweet.lower()
    tweet = re.sub(r'(.)\1+', r'\1\1', tweet) #single occurance of letters
    tweet = re.sub(r'[\?\.\!\,]+(?=[\?\.\!\,])', blank_space, tweet) #ingle occurance for punctuation
    tweet= contractions.fix(tweet)

    token_list = word_tokenize(tweet)
    token_list = [token for token in token_list
                    if token not in string.punctuation]

    token_list = [token for token in token_list if token.isalpha()]

    stop_words = set(stopwords.words('english'))
    stop_words.discard('not')
    token_list = [token for token in token_list if not token in stop_words]


    tokens = token_list
    stemmer = SnowballStemmer("english") # define stemmer

    stem_token_list = []
    for token in tokens:
        stem_token_list.append(stemmer.stem(token))
    stem = stem_token_list
    return stem

def predict_tweet(tweet,model):
    processed_tweet = cleaning_tweets(tweet)
    tf = fit_tfidf(X_train)
    transformed_tweet = tf.transform([processed_tweet])
    prediction = model.predict(transformed_tweet)

    if prediction == 1:
        return "Prediction is positive sentiment"
    elif  prediction == -1:
        return "Prediction is negative sentiment"
    else:
        return "Prediction is neutral sentiment"

train = pd.read_csv('data/train.csv')
train.dropna(inplace=True)
train["tokens"] = train["text"].apply(cleaning_tweets)
train["tweet_sentiment"] = train["sentiment"].apply(lambda i: 1 if i == "positive" else -1 if i == "negative" else 0)
print(train.head())
X_train = train["tokens"].tolist()


def main():
    test = pd.read_csv('data/test.csv')
    test.dropna(inplace=True)
    test["tokens"] = test["text"].apply(cleaning_tweets)
    test["tweet_sentiment"] = test["sentiment"].apply(lambda i: 1 if i == "positive" else -1 if i == "negative" else 0)
    Y_train = train["tweet_sentiment"].tolist()
    X_test = test["tokens"].tolist()
    Y_test = test["tweet_sentiment"].tolist()
    tf = fit_tfidf(X_train)
    X_train_tf = tf.transform(X_train)
    X_test_tf = tf.transform(X_test)

    simple_lr(X_train_tf,X_test_tf,Y_train,Y_test)

if __name__ == '__main__':
    main()

