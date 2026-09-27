"""
SmartSpend - Machine Learning: Smart Category Classifier
Uses Natural Language Processing (TF-IDF Vectorization + Logistic Regression)
to classify transaction descriptions/merchant names into appropriate expense categories.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import config
from database.db_manager import DatabaseManager


# Seed corpus grounded in realistic Indian & international transaction terms
BASE_TRAINING_CORPUS = [
    # Food & Dining
    ("Swiggy food order delivery", "Food & Dining"),
    ("Zomato dinner biryani", "Food & Dining"),
    ("Chai Point tea and samosa", "Food & Dining"),
    ("Starbucks coffee latte frappuccino", "Food & Dining"),
    ("McDonalds burger meal fries", "Food & Dining"),
    ("KFC fried chicken bucket", "Food & Dining"),
    ("Dominos pizza cheese burst", "Food & Dining"),
    ("Subway sandwich wrap", "Food & Dining"),
    ("Local darshini dosa idli filter coffee", "Food & Dining"),
    ("Restaurant dining with friends buffet", "Food & Dining"),
    ("Cafe coffee day cappuccino snack", "Food & Dining"),
    ("Barbeque Nation dinner table reservation", "Food & Dining"),

    # Groceries
    ("BigBasket weekly grocery vegetables fruits", "Groceries"),
    ("D-Mart supermarket provisions cooking oil", "Groceries"),
    ("Zepto instant 10 min grocery delivery milk", "Groceries"),
    ("Blinkit eggs bread vegetables butter", "Groceries"),
    ("Nature Basket organic gourmet food", "Groceries"),
    ("Local vegetable vendor sabzi mandi", "Groceries"),
    ("Spencers retail rice wheat flour dal", "Groceries"),
    ("Supermarket monthly kitchen supplies", "Groceries"),

    # Transportation
    ("Uber cab ride to office airport", "Transportation"),
    ("Ola auto rickshaw ride", "Transportation"),
    ("Namma Metro smart card recharge travel", "Transportation"),
    ("Indian Oil petrol diesel full tank", "Transportation"),
    ("Shell petrol pump fuel refill", "Transportation"),
    ("HPCL Bharat Petroleum petrol fuel", "Transportation"),
    ("Rapido bike taxi commute", "Transportation"),
    ("Fastag toll plaza highway payment", "Transportation"),
    ("Train ticket IRCTC reservation", "Transportation"),
    ("Flight airfare ticket Indigo flight travel", "Transportation"),

    # Housing & Rent
    ("Monthly house apartment flat rent payment", "Housing & Rent"),
    ("Landlord rental security deposit", "Housing & Rent"),
    ("Apartment society maintenance charges", "Housing & Rent"),
    ("Home painter maintenance repair plumbing", "Housing & Rent"),

    # Utilities & Bills
    ("Electricity bill BESCOM power supply payment", "Utilities & Bills"),
    ("Airtel fiber broadband wifi internet bill", "Utilities & Bills"),
    ("Jio mobile 5G prepaid postpaid recharge plan", "Utilities & Bills"),
    ("Water utility BWSSB tanker bill payment", "Utilities & Bills"),
    ("Indane HP Bharat LPG cooking gas cylinder refill", "Utilities & Bills"),
    ("Tata Play DTH satellite dish tv recharge", "Utilities & Bills"),

    # Entertainment
    ("Netflix 4K subscription monthly charge", "Entertainment"),
    ("Spotify Premium family music stream", "Entertainment"),
    ("Amazon Prime Video subscription annual", "Entertainment"),
    ("BookMyShow PVR Inox cinema movie tickets", "Entertainment"),
    ("Steam video game store counter-strike purchase", "Entertainment"),
    ("Disney Hotstar cricket premium streaming", "Entertainment"),
    ("YouTube Premium ad-free subscription", "Entertainment"),

    # Shopping
    ("Amazon India electronics headphones gadgets", "Shopping"),
    ("Flipkart shopping sale clothes mobile", "Shopping"),
    ("Myntra fashion shoes shirts dress apparel", "Shopping"),
    ("Decathlon sports gym running shoes gear", "Shopping"),
    ("Zara HM clothing fashion apparel jacket", "Shopping"),
    ("Ikea home furniture desk chair decor", "Shopping"),
    ("Reliance Digital laptop tablet accessories", "Shopping"),

    # Healthcare
    ("Apollo Pharmacy medicines tablets vitamins", "Healthcare"),
    ("Netmeds 1mg prescription online medicine", "Healthcare"),
    ("Doctor clinic consultation physician fee", "Healthcare"),
    ("Diagnostic lab blood test health checkup", "Healthcare"),
    ("Dentist teeth cleaning dental clinic", "Healthcare"),

    # Personal Care
    ("Salon haircut beard trim grooming spa", "Personal Care"),
    ("Urban Company salon haircut at home massage", "Personal Care"),
    ("Skincare face wash lotion shampoo cosmetics", "Personal Care"),

    # Education
    ("Udemy online course web development python", "Education"),
    ("Coursera certificate program specialization", "Education"),
    ("College university semester exam fee", "Education"),
    ("Textbooks study material notebook stationery", "Education"),

    # Investments
    ("Mutual fund monthly SIP investment index fund", "Investments"),
    ("Zerodha Groww stocks equity share purchase", "Investments"),
    ("Fixed deposit recurring deposit bank savings", "Investments"),

    # Salary / Income
    ("Monthly corporate salary credit payroll bonus", "Salary / Income"),
    ("Freelance client project payment invoice", "Salary / Income"),
    ("Consulting dividend cashback interest received", "Salary / Income"),
]


class CategoryClassifier:
    """
    NLP Text Classifier for automated expense category prediction.
    Utilizes TF-IDF n-gram vectorization and regularized Logistic Regression.
    """

    def __init__(self, model_path: Optional[Path] = None):
        self.model_path = model_path or config.ML_CONFIG["category_model_path"]
        self.pipeline: Optional[Pipeline] = None
        self._load_or_train_initial()

    def _build_pipeline(self) -> Pipeline:
        """Constructs scikit-learn TF-IDF + MultinomialNB pipeline."""
        return Pipeline([
            ("tfidf", TfidfVectorizer(
                ngram_range=(1, 2),
                lowercase=True,
                stop_words="english",
                sublinear_tf=True
            )),
            ("clf", MultinomialNB(
                alpha=0.1,
                fit_prior=True
            ))
        ])

    def _load_or_train_initial(self) -> None:
        """Loads cached model from disk if present, else trains on base corpus."""
        if self.model_path.exists():
            try:
                self.pipeline = joblib.load(self.model_path)
                return
            except Exception:
                # If cached model is corrupted or version mismatched, re-train
                pass

        # Train on initial base corpus
        texts = [item[0] for item in BASE_TRAINING_CORPUS]
        labels = [item[1] for item in BASE_TRAINING_CORPUS]
        self.pipeline = self._build_pipeline()
        self.pipeline.fit(texts, labels)
        self.save_model()

    def save_model(self) -> None:
        """Persists trained model pipeline to disk."""
        if self.pipeline:
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            joblib.dump(self.pipeline, self.model_path)

    def train_on_database(self, db: DatabaseManager) -> Dict[str, Any]:
        """
        Gathers transaction records from the database, merges them with the base corpus,
        and fits the classifier.
        """
        rows = db.fetch_all("""
            SELECT title, notes, category
            FROM expenses
            WHERE category IS NOT NULL AND category != ''
        """)

        # Combine title and notes as text input
        db_texts = []
        db_labels = []
        for r in rows:
            text = f"{r['title']} {r['notes'] or ''}".strip()
            if text and r["category"]:
                db_texts.append(text)
                db_labels.append(r["category"])

        # Merge with base training corpus to retain general knowledge
        corpus_texts = [item[0] for item in BASE_TRAINING_CORPUS]
        corpus_labels = [item[1] for item in BASE_TRAINING_CORPUS]

        all_texts = corpus_texts + db_texts
        all_labels = corpus_labels + db_labels

        self.pipeline = self._build_pipeline()
        self.pipeline.fit(all_texts, all_labels)
        self.save_model()

        return {
            "total_samples": len(all_texts),
            "user_samples": len(db_texts),
            "classes": list(self.pipeline.classes_)
        }

    def predict(self, text: str) -> Dict[str, Any]:
        """
        Predicts category for a given expense note or merchant title.
        Returns:
            predicted_category: str
            confidence: float (0.0 to 100.0)
            top_3: List[Tuple[category, confidence]]
        """
        cleaned_text = (text or "").strip()
        if not cleaned_text:
            return {
                "predicted_category": "Other Expense",
                "confidence": 0.0,
                "top_predictions": []
            }

        if not self.pipeline:
            self._load_or_train_initial()

        probs = self.pipeline.predict_proba([cleaned_text])[0]
        classes = self.pipeline.classes_

        # Sort classes by descending probability
        sorted_indices = np.argsort(probs)[::-1]
        top_category = classes[sorted_indices[0]]
        top_confidence = round(float(probs[sorted_indices[0]]) * 100.0, 1)

        top_3 = []
        for idx in sorted_indices[:3]:
            top_3.append({
                "category": classes[idx],
                "confidence": round(float(probs[idx]) * 100.0, 1)
            })

        return {
            "predicted_category": top_category,
            "confidence": top_confidence,
            "top_predictions": top_3
        }
