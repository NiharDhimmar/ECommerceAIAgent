# intent_core.py
import os, json, numpy as np
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Embedding, GlobalAveragePooling1D, Dense
from tensorflow.keras.preprocessing.text import Tokenizer, tokenizer_from_json
from tensorflow.keras.preprocessing.sequence import pad_sequences

BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
MODEL_FILE      = os.path.join(BASE_DIR, "intent_model.keras")
TOKENIZER_PATH  = os.path.join(BASE_DIR, "tokenizer.json")
LABELS_PATH     = os.path.join(BASE_DIR, "labels.json")

# ---------- globals (populated on first import / train) ----------
model = None
tokenizer = None
index_label = {}
maxlen = 20    # default – overwritten after training


# ───────────────────────────────────────────────────────────────────
def load_saved_assets() -> bool:
    """Return True if a saved model was found & loaded."""
    global model, tokenizer, index_label, maxlen
    try:
        model = load_model(MODEL_FILE)
        with open(TOKENIZER_PATH) as f:
            tokenizer = tokenizer_from_json(f.read())
        with open(LABELS_PATH) as f:
            meta = json.load(f)
        index_label = {i: l for l, i in meta["labels"].items()}
        maxlen = meta["maxlen"]
        return True
    except Exception:
        return False


# ───────────────────────────────────────────────────────────────────
def train_from_txt(txt_path: str) -> dict:
    """Train model on a `intent: sentence` text file and save assets."""
    global model, tokenizer, index_label, maxlen

    texts, labels = [], []
    with open(txt_path, encoding="utf-8") as f:
        for line in f:
            if ":" in line:
                lbl, txt = line.strip().split(":", 1)
                texts.append(txt.strip())
                labels.append(lbl.strip())
    if not texts:
        raise ValueError("No valid 'intent: sentence' lines found.")

    # label maps
    label_index = {l: i for i, l in enumerate(sorted(set(labels)))}
    index_label = {i: l for l, i in label_index.items()}
    y = np.array([label_index[l] for l in labels])

    # tokenizer & padded seqs
    tokenizer = Tokenizer(oov_token="<OOV>")
    tokenizer.fit_on_texts(texts)
    seqs = tokenizer.texts_to_sequences(texts)
    maxlen = max(len(s) for s in seqs)
    padded = pad_sequences(seqs, maxlen=maxlen, padding="post")

    # build & train model
    vocab_size, num_classes = len(tokenizer.word_index) + 1, len(label_index)
    model = Sequential(
        [
            Embedding(vocab_size, 16),
            GlobalAveragePooling1D(),
            Dense(16, activation="relu"),
            Dense(num_classes, activation="softmax"),
        ]
    )
    model.compile(
        loss="sparse_categorical_crossentropy", optimizer="adam", metrics=["accuracy"]
    )
    model.fit(padded, y, epochs=100, verbose=0)

    # save assets
    model.save(MODEL_FILE, overwrite=True)
    with open(TOKENIZER_PATH, "w") as f:
        f.write(tokenizer.to_json())
    with open(LABELS_PATH, "w") as f:
        json.dump({"labels": label_index, "maxlen": maxlen}, f)

    return {"num_intents": num_classes, "samples": len(texts), "maxlen": maxlen}


# ───────────────────────────────────────────────────────────────────
def predict_intent(text: str, threshold: float = 0.85) -> dict:
    
    if model is None or tokenizer is None:
        raise RuntimeError("Model not loaded. Train first or supply saved assets.")

    # text → integer sequence → padded array
    seq  = tokenizer.texts_to_sequences([text])
    pad  = pad_sequences(seq, maxlen=maxlen, padding="post")
    probs = model.predict(pad, verbose=0)[0]

    conf = float(np.max(probs))          # top soft‑max probability
    if conf >= threshold:
        intent = index_label[int(np.argmax(probs))]
    else:
        intent = "I could not understand"

    return {"intent": intent, "confidence": conf}