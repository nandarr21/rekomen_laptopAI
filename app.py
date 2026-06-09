import os
import sqlite3
import json
from datetime import datetime

import numpy as np
import pandas as pd
import joblib
from flask import (
    Flask, render_template, request,
    redirect, url_for, flash, jsonify,
)

# -- App setup -----------------------------------------------------------------
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
app       = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "knn-laptop-recommender-secret-2024")

DB_PATH       = os.path.join(BASE_DIR, "database.db")
MODEL_DIR     = os.path.join(BASE_DIR, "model")
DATASET_CLEAN = os.path.join(BASE_DIR, "dataset", "laptop_clean.csv")

CATEGORY_OPTIONS = ["Programming", "Gaming", "Editing", "Office"]

# Load artefak ML 
def load_artifacts():
    knn     = joblib.load(os.path.join(MODEL_DIR, "knn_model.pkl"))
    scaler  = joblib.load(os.path.join(MODEL_DIR, "scaler.pkl"))
    encoder = joblib.load(os.path.join(MODEL_DIR, "encoder.pkl"))
    df      = pd.read_csv(DATASET_CLEAN)
    return knn, scaler, encoder, df


try:
    knn_model, scaler, label_encoder, df_laptops = load_artifacts()
    MODEL_READY = True
except Exception as exc:
    MODEL_READY = False
    MODEL_ERROR = str(exc)
    print("Model belum siap: {}".format(exc))

# Database 
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    sql = (
        "CREATE TABLE IF NOT EXISTS search_history ("
        "id          INTEGER PRIMARY KEY AUTOINCREMENT, "
        "budget      REAL    NOT NULL, "
        "ram         INTEGER NOT NULL, "
        "storage     INTEGER NOT NULL, "
        "category    TEXT    NOT NULL, "
        "results     TEXT    NOT NULL, "
        "searched_at TEXT    NOT NULL"
        ")"
    )
    conn = get_db()
    try:
        conn.execute(sql)
        conn.commit()
    finally:
        conn.close()


init_db()

# Helper: rekomendasi 
def get_recommendations(budget, ram, storage, category):
    if not MODEL_READY:
        raise RuntimeError("Model belum dilatih. Jalankan train_model.py.")

    if category not in CATEGORY_OPTIONS:
        raise ValueError("Kategori tidak valid: {}".format(category))

    cat_enc     = label_encoder.transform([category])[0]
    user_raw    = np.array([[budget, ram, storage, cat_enc]], dtype=float)
    user_scaled = scaler.transform(user_raw)

    distances, indices = knn_model.kneighbors(user_scaled)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        row        = df_laptops.iloc[idx]
        similarity = round(max(0.0, 1 - dist) * 100, 1)
        results.append({
            "brand":      str(row["Brand"]),
            "model":      str(row["Model"]),
            "processor":  str(row["Processor"]),
            "ram":        int(row["RAM_GB"]),
            "storage":    int(row["Storage_SSD_GB"]),
            "gpu":        str(row["GPU"]),
            "category":   str(row["Category"]),
            "price":      float(row["Price_USD"]),
            "similarity": similarity,
        })

    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results


def save_history(budget, ram, storage, category, results):
    sql = (
        "INSERT INTO search_history "
        "(budget, ram, storage, category, results, searched_at) "
        "VALUES (?, ?, ?, ?, ?, ?)"
    )
    conn = get_db()
    try:
        conn.execute(sql, (
            budget, ram, storage, category,
            json.dumps(results),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ))
        conn.commit()
    finally:
        conn.close()

# Routes 
@app.route("/")
def index():
    return render_template(
        "index.html",
        categories=CATEGORY_OPTIONS,
        model_ready=MODEL_READY,
    )


@app.route("/recommend", methods=["GET", "POST"])
def recommend():
    if request.method == "GET":
        return redirect(url_for("index"))

    errors = []

    try:
        budget = float(request.form.get("budget", 0))
        if budget <= 0:
            errors.append("Budget harus lebih dari 0.")
    except (TypeError, ValueError):
        budget = 0
        errors.append("Budget harus berupa angka.")

    try:
        ram = int(request.form.get("ram", 0))
        if ram not in [4, 8, 16, 32, 64]:
            errors.append("Pilih nilai RAM yang valid.")
    except (TypeError, ValueError):
        ram = 0
        errors.append("RAM tidak valid.")

    try:
        storage = int(request.form.get("storage", 0))
        if storage not in [256, 512, 1000, 2000]:
            errors.append("Pilih nilai storage yang valid.")
    except (TypeError, ValueError):
        storage = 0
        errors.append("Storage tidak valid.")

    category = request.form.get("category", "").strip()
    if category not in CATEGORY_OPTIONS:
        errors.append("Pilih kategori penggunaan yang valid.")

    if errors:
        for err in errors:
            flash(err, "danger")
        return redirect(url_for("index"))

    try:
        results = get_recommendations(budget, ram, storage, category)
        save_history(budget, ram, storage, category, results)
    except Exception as exc:
        flash("Terjadi kesalahan saat memproses: {}".format(exc), "danger")
        return redirect(url_for("index"))

    return render_template(
        "recommendation.html",
        results=results,
        budget=budget,
        ram=ram,
        storage=storage,
        category=category,
        total=len(results),
    )


@app.route("/history")
def history():
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM search_history ORDER BY id DESC LIMIT 50"
        ).fetchall()
    finally:
        conn.close()

    records = []
    for row in rows:
        records.append({
            "id":          row["id"],
            "budget":      row["budget"],
            "ram":         row["ram"],
            "storage":     row["storage"],
            "category":    row["category"],
            "searched_at": row["searched_at"],
            "results":     json.loads(row["results"]),
        })

    return render_template("history.html", records=records)


@app.route("/history/delete/<int:record_id>", methods=["POST"])
def delete_history(record_id):
    conn = get_db()
    try:
        conn.execute("DELETE FROM search_history WHERE id = ?", (record_id,))
        conn.commit()
    finally:
        conn.close()
    flash("Riwayat berhasil dihapus.", "success")
    return redirect(url_for("history"))


@app.route("/history/clear", methods=["POST"])
def clear_history():
    conn = get_db()
    try:
        conn.execute("DELETE FROM search_history")
        conn.commit()
    finally:
        conn.close()
    flash("Semua riwayat berhasil dihapus.", "success")
    return redirect(url_for("history"))


@app.route("/api/stats")
def api_stats():
    if not MODEL_READY:
        return jsonify({"error": "Model belum siap."}), 503

    stats = {
        "total_laptops": int(len(df_laptops)),
        "brands":        int(df_laptops["Brand"].nunique()),
        "price_min":     float(df_laptops["Price_USD"].min()),
        "price_max":     float(df_laptops["Price_USD"].max()),
        "categories":    df_laptops["Category"].value_counts().to_dict(),
    }
    return jsonify(stats)


# Template filters 
@app.template_filter("currency")
def currency_filter(value):
    return "${:,.0f}".format(value)


@app.template_filter("similarity_color")
def similarity_color(value):
    if value >= 80:
        return "success"
    elif value >= 60:
        return "warning"
    return "danger"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
