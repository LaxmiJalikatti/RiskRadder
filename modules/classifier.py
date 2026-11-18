"""
classifier.py
Trains and uses the clause classifier (TF-IDF + Logistic Regression).
"""

from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import (
    RepeatedStratifiedKFold,
    StratifiedKFold,
    cross_val_predict,
    cross_val_score,
)
from sklearn.pipeline import FeatureUnion, Pipeline

from modules.preprocessor import preprocess_for_model

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "training_data.csv"
MODEL_PATH = BASE_DIR / "models" / "risk_model.joblib"

SAFE_LABEL = "No Risk"

_model = None  # loaded lazily


def build_pipeline():
    """Word and character TF-IDF features feeding a Logistic Regression classifier."""
    features = FeatureUnion(
        [
            ("word", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)),
            (
                "char",
                TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True),
            ),
        ]
    )
    return Pipeline(
        [
            ("features", features),
            ("clf", LogisticRegression(max_iter=3000, C=20, class_weight="balanced")),
        ]
    )


def load_training_data():
    df = pd.read_csv(DATA_PATH, encoding="utf-8-sig").dropna().drop_duplicates()
    texts = df["clause"].apply(preprocess_for_model)
    labels = df["category"].str.strip()
    return texts, labels


def train_and_save(verbose=True):
    """Evaluate with cross-validation, then train on all data and save the model."""
    texts, labels = load_training_data()

    if verbose:
        repeated = RepeatedStratifiedKFold(n_splits=5, n_repeats=3, random_state=42)
        scores = cross_val_score(build_pipeline(), texts, labels, cv=repeated)
        predictions = cross_val_predict(
            build_pipeline(),
            texts,
            labels,
            cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=42),
        )
        print(f"Training examples : {len(texts)}")
        print(f"Categories        : {labels.nunique()}")
        print(f"Accuracy (5-fold x3 repeats): {scores.mean():.2%}  (+/- {scores.std():.2%})\n")
        print(classification_report(labels, predictions, zero_division=0))

    final_model = build_pipeline().fit(texts, labels)
    MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump(final_model, MODEL_PATH)
    if verbose:
        print(f"Model saved to: {MODEL_PATH}")
    return final_model


def load_model():
    global _model
    if _model is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError("Model not found. Run train_model.py first.")
        _model = joblib.load(MODEL_PATH)
    return _model


def classify_clauses(processed_texts):
    """
    Takes a list of preprocessed clause strings.
    Returns a list of {"category": str, "confidence": float} in the same order.
    """
    if not processed_texts:
        return []
    model = load_model()
    probabilities = model.predict_proba(processed_texts)
    classes = model.classes_
    results = []
    for row in probabilities:
        best = row.argmax()
        results.append({"category": classes[best], "confidence": float(row[best])})
    return results
