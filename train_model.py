import os
import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
import joblib

# Path
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DATASET    = os.path.join(BASE_DIR, "dataset", "laptop_dataset.csv")
MODEL_DIR  = os.path.join(BASE_DIR, "model")
os.makedirs(MODEL_DIR, exist_ok=True)

CATEGORY_MAP = {
    "Programming": 0,
    "Gaming":      1,
    "Editing":     2,
    "Office":      3,
}


def load_and_clean(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()

    # Hapus baris duplikat & NaN pada kolom penting
    df.drop_duplicates(inplace=True)
    df.dropna(subset=["Brand", "Model", "Price_USD", "RAM_GB",
                       "Storage_SSD_GB", "Category"], inplace=True)

    # Pastikan tipe numerik
    df["Price_USD"]       = pd.to_numeric(df["Price_USD"],       errors="coerce")
    df["RAM_GB"]          = pd.to_numeric(df["RAM_GB"],          errors="coerce")
    df["Storage_SSD_GB"]  = pd.to_numeric(df["Storage_SSD_GB"], errors="coerce")
    df.dropna(subset=["Price_USD", "RAM_GB", "Storage_SSD_GB"], inplace=True)

    return df.reset_index(drop=True)


def encode_category(df: pd.DataFrame):
   
    le = LabelEncoder()
    le.fit(list(CATEGORY_MAP.keys()))
    df["Category_enc"] = le.transform(df["Category"])
    joblib.dump(le, os.path.join(MODEL_DIR, "encoder.pkl"))
    return df, le


def normalize_features(df: pd.DataFrame):
   
    feature_cols = ["Price_USD", "RAM_GB", "Storage_SSD_GB", "Category_enc"]
    scaler = MinMaxScaler()
    X = scaler.fit_transform(df[feature_cols])
    joblib.dump(scaler, os.path.join(MODEL_DIR, "scaler.pkl"))
    return X, scaler, feature_cols


def train_knn(X: np.ndarray, n_neighbors: int = 5):
   
    knn = NearestNeighbors(
        n_neighbors=n_neighbors,
        metric="euclidean",
        algorithm="auto",
    )
    knn.fit(X)
    joblib.dump(knn, os.path.join(MODEL_DIR, "knn_model.pkl"))
    return knn


def main():
    print("📂  Memuat dataset …")
    df = load_and_clean(DATASET)
    print(f"    → {len(df)} baris valid ditemukan.")

    print("🔤  Encoding kategori …")
    df, le = encode_category(df)

    print("📏  Normalisasi fitur …")
    X, scaler, feature_cols = normalize_features(df)

    print("🤖  Melatih model KNN …")
    knn = train_knn(X)

    # Simpan dataset bersih 
    df.to_csv(os.path.join(BASE_DIR, "dataset", "laptop_clean.csv"), index=False)

    print("✅  Semua model tersimpan di folder /model/")
    print(f"    • knn_model.pkl  – {knn}")
    print(f"    • scaler.pkl     – fitur: {feature_cols}")
    print(f"    • encoder.pkl    – kelas: {list(le.classes_)}")


if __name__ == "__main__":
    main()
