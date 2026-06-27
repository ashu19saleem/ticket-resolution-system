"""
Classifier model wrapper.
Loads the fine-tuned DistilBERT model from trained_model_v2 and exposes
a simple classify(text) function for the rest of the app to call.
"""

import json
from functools import lru_cache
from pathlib import Path

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Path to the trained model — relative to this file's location
TRAINED_MODEL_DIR = Path(__file__).resolve().parent / "trained_model_v2"
MAX_LENGTH = 256


class TicketClassifier:
    def __init__(self):
        if not TRAINED_MODEL_DIR.exists():
            raise FileNotFoundError(
                f"Trained model not found at {TRAINED_MODEL_DIR}. "
                "Make sure trained_model_v2/ is inside the models/ folder."
            )

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.tokenizer = AutoTokenizer.from_pretrained(str(TRAINED_MODEL_DIR))
        self.model = AutoModelForSequenceClassification.from_pretrained(
            str(TRAINED_MODEL_DIR)
        )
        self.model.to(self.device)
        self.model.eval()

        # Load label mapping saved during training
        label_map_path = TRAINED_MODEL_DIR / "label_mapping.json"
        with open(label_map_path) as f:
            mapping = json.load(f)
        self.id2label = {int(k): v for k, v in mapping["id2label"].items()}

        print(f"[Classifier] Loaded DistilBERT from {TRAINED_MODEL_DIR} on {self.device}")

    def classify(self, text: str) -> dict:
        """
        Classify a ticket description into a category.
        Returns:
            {
                "category": str,
                "confidence": float,  # 0-1
            }
        """
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding="max_length",
            max_length=MAX_LENGTH,
            return_tensors="pt",
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**encoding)
            probs = torch.softmax(outputs.logits, dim=1)[0]
            pred_id = torch.argmax(probs).item()

        return {
            "category": self.id2label[pred_id],
            "confidence": round(probs[pred_id].item(), 4),
        }


@lru_cache(maxsize=1)
def get_classifier() -> TicketClassifier:
    """Cached singleton — model loads once per process, not per request."""
    return TicketClassifier()
