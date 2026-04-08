import streamlit as st
import pickle
import re
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(BASE_DIR, "model.pkl")
vectorizer_path = os.path.join(BASE_DIR, "vectorizer.pkl")

model = pickle.load(open(model_path, "rb"))
vectorizer = pickle.load(open(vectorizer_path, "rb"))

def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    return text

st.set_page_config(page_title="SMS Spam Classifier", page_icon="📧")

st.title("📱 SMS Spam Classifier")
st.write("Enter a message to check whether it is spam or not.")

input_text = st.text_area("Enter your message here:")

if st.button("Predict"):

    if input_text.strip() == "":
        st.warning("Please enter some text.")
    else:
        cleaned_text = clean_text(input_text)

        vector_input = vectorizer.transform([cleaned_text])

        prediction = model.predict(vector_input)[0]
        probability = model.predict_proba(vector_input)[0]

        if prediction == 1:
            st.error(f"🚫 Spam Message (Confidence: {max(probability)*100:.2f}%)")
        else:
            st.success(f"✅ Not Spam (Confidence: {max(probability)*100:.2f}%)")