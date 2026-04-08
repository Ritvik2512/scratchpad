import pandas as pd
import re
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import pickle
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(BASE_DIR, "spam.csv")

df = pd.read_csv(file_path, encoding='latin-1')

df = df[['target', 'text']]
df.columns = ['label', 'message']

df['label'] = df['label'].map({'ham': 0, 'spam': 1})

def normalize_text(text):
    return re.sub(r'(.)\1+', r'\1\1', text)

def clean_text(text):
    text = text.lower()
    text = normalize_text(text)
    text = re.sub(r'[^\w\s]', '', text)
    return text

df['message'] = df['message'].apply(clean_text)

vectorizer = TfidfVectorizer(ngram_range=(1,2),min_df=2)
X = vectorizer.fit_transform(df['message'])
y = df['label']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = LogisticRegression(max_iter=1000, class_weight='balanced')
model.fit(X_train, y_train)

y_pred = model.predict(X_test)

print("Accuracy:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred))
print("Confusion Matrix:\n", confusion_matrix(y_test, y_pred))

#saving model
pickle.dump(model, open("model.pkl", "wb"))
pickle.dump(vectorizer, open("vectorizer.pkl", "wb"))

def predict_spam(text):
    text = clean_text(text)
    text_vector = vectorizer.transform([text])
    prediction = model.predict(text_vector)
    return "Spam" if prediction[0] == 1 else "Not Spam"

print(predict_spam("Congratulations! You won a free iPhone"))