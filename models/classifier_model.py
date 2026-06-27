"""
Classifier model wrapper.
Loads the fine-tuned DistilBERT model from trained_model_v2 and exposes
a simple classify(text) function. Falls back to LLM-based classification
if the trained model is not available (e.g. on Render deployment).
"""

import json
from functools import lru_cache
from pathlib import Path

TRAINED_MODEL_DIR = Path(__file__).resolve().parent / "trained_model_v2"
MAX_LENGTH = 256


class TicketClassifier:
    def __init__(self):
        if not TRAINED_MODEL_DIR.exists():
            print(f"[Classifier] Trained model not found at {TRAINED_MODEL_DIR}. "
                  "Using LLM-based classification fallback.")
            self._use_llm_fallback = True
            return

        self._use_llm_fallback = False

        try:
            import torch
            from transformers import AutoTokenizer, AutoModelForSequenceClassification

            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.tokenizer = AutoTokenizer.from_pretrained(str(TRAINED_MODEL_DIR))
            self.model = AutoModelForSequenceClassification.from_pretrained(
                str(TRAINED_MODEL_DIR)
            )
            self.model.to(self.device)
            self.model.eval()

            label_map_path = TRAINED_MODEL_DIR / "label_mapping.json"
            with open(label_map_path) as f:
                mapping = json.load(f)
            self.id2label = {int(k): v for k, v in mapping["id2label"].items()}
            print(f"[Classifier] Loaded DistilBERT from {TRAINED_MODEL_DIR} on {self.device}")

        except ImportError:
            print("[Classifier] torch/transformers not available. Using LLM fallback.")
            self._use_llm_fallback = True

    def classify(self, text: str) -> dict:
        if self._use_llm_fallback:
            return self._llm_classify(text)

        import torch
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

    def _llm_classify(self, text: str) -> dict:
        """Fallback: use the LLM to classify when DistilBERT model isn't available."""
        try:
            from rag.query_optimizer import classify_ticket
            return classify_ticket(text)
        except Exception as e:
            print(f"[Classifier] LLM fallback also failed: {e}")
            return {"category": "Other", "confidence": 0.0}


@lru_cache(maxsize=1)
def get_classifier() -> TicketClassifier:
    """Cached singleton — model loads once per process, not per request."""
    return TicketClassifier()