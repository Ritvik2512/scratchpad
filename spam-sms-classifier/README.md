# SMS Spam Classifier

A machine learning project that classifies SMS messages as **Spam** or **Not Spam** using Natural Language Processing (NLP) techniques.

---

## Project Overview

This project builds a text classification model using TF-IDF vectorization and Logistic Regression.
It processes raw text messages, converts them into numerical features, and predicts whether a message is spam.

The project demonstrates the complete ML pipeline:

* Data preprocessing
* Feature engineering
* Model training
* Evaluation
* Deployment-ready setup

---

## Dataset

The model is trained on the **SMS Spam Dataset** containing labeled messages:

* **Ham (0)** → Normal messages
* **Spam (1)** → Unwanted / promotional messages

---

## Tech Stack

* Python
* pandas
* scikit-learn
* Streamlit (for UI)

---

## Approach

### 1. Data Preprocessing

* Converted text to lowercase
* Removed punctuation and special characters using regex
* Normalized repeated characters (e.g., *"moneyyyy" → "money"*)

---

### 2. Feature Extraction

Used **TF-IDF Vectorization** with bigrams:

* Captures word importance
* Includes phrase-level features like:

  * *"free money"*
  * *"call now"*

---

### 3. Model Selection

Two models were tested:

* Multinomial Naive Bayes
* Logistic Regression

Logistic Regression performed better due to its ability to learn feature relationships.

---

### 4. Handling Class Imbalance

Used:
```python
class_weight='balanced'
```

This improved spam detection by giving more importance to minority class (spam).

---

## Model Performance

**Final Model: Logistic Regression**

* Accuracy: **~95%**
* Spam Precision: **~0.88**
* Spam Recall: **~0.87**
* F1 Score: **~0.88**

---

## Confusion Matrix

```
[[1648   58]
[  62  425]]
```

### Interpretation:

* Low false positives → minimal disruption to normal messages
* Good recall → most spam messages are detected

---

## Limitations

* Struggles with heavily misspelled or exaggerated text

  * Example: *"winn moneeyyy"*
* TF-IDF relies on known vocabulary and does not understand semantic meaning

---

## Model Persistence

The trained model and vectorizer are saved using `pickle`:

* `model.pkl`
* `vectorizer.pkl`

This allows fast predictions without retraining.

---

## Running the Project

### 1. Clone repository

```bash
git clone <your-repo-link>
cd spam-classifier
```

---

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 3. Train model

```bash
python train.py
```

---

### 4. Run Streamlit app

```bash
streamlit run app.py
```

---

## Key Learnings

* Importance of text preprocessing in NLP
* Trade-off between precision and recall
* Handling class imbalance improves minority class detection
* Feature engineering (n-grams) significantly impacts performance
* Difference between probabilistic and linear models

---

## Future Improvements

* Use character-level features for better handling of noisy text
* Try deep learning models (LSTM, Transformers)
* Deploy application online

---

## 👨‍💻 Author

Developed as part of a machine learning project to understand text classification and model deployment.
