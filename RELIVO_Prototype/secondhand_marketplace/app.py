from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from pathlib import Path
from werkzeug.utils import secure_filename
import os
import base64
import requests
from flask import jsonify

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "marketplace.db"
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

app = Flask(__name__)
app.secret_key = "secondhand-marketplace-demo-key"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

CATEGORIES = ["Pakaian", "Elektronik", "Furniture", "Buku", "Sepatu", "Aksesoris", "Lainnya"]
CONDITIONS = ["Seperti Baru", "Baik", "Cukup", "Rusak"]

# Kondisi "Rusak" tidak boleh ditampilkan sebagai produk layak.
ELIGIBLE_CONDITIONS = {"Seperti Baru", "Baik", "Cukup"}


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            condition TEXT NOT NULL,
            price INTEGER NOT NULL,
            image TEXT,
            description TEXT,
            eligible INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    # Data demo hanya dimasukkan ketika database masih kosong.
    count = conn.execute("SELECT COUNT(*) AS c FROM products").fetchone()["c"]
    if count == 0:
        demo = [
            ("Hoodie Hitam Uniqlo", "Pakaian", "Baik", 120000, None,
             "Hoodie bekas pakai, masih nyaman dan tidak ada kerusakan besar.", 1),
            ("Keyboard Mechanical", "Elektronik", "Seperti Baru", 350000, None,
             "Keyboard masih berfungsi normal, lengkap dengan kabel USB.", 1),
            ("Rak Buku Kayu", "Furniture", "Cukup", 180000, None,
             "Rak buku bekas dengan beberapa bekas pemakaian ringan.", 1),
            ("Buku Dasar Ekonomi", "Buku", "Baik", 50000, None,
             "Buku kuliah bekas, halaman lengkap dan dapat dibaca dengan baik.", 1),
        ]
        conn.executemany("""
            INSERT INTO products
            (name, category, condition, price, image, description, eligible)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, demo)
        conn.commit()
    conn.close()


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def parse_price(value):
    try:
        price = int(value)
        return price if price >= 0 else None
    except (TypeError, ValueError):
        return None


@app.route("/")
def index():
    category = request.args.get("category", "")
    condition = request.args.get("condition", "")
    search = request.args.get("search", "").strip()
    min_price = request.args.get("min_price", "")
    max_price = request.args.get("max_price", "")

    query = """
        SELECT * FROM products
        WHERE eligible = 1
    """
    params = []

    if search:
        query += " AND (name LIKE ? OR description LIKE ?)"
        params += [f"%{search}%", f"%{search}%"]

    if category:
        query += " AND category = ?"
        params.append(category)

    if condition:
        query += " AND condition = ?"
        params.append(condition)

    min_value = parse_price(min_price)
    max_value = parse_price(max_price)

    if min_value is not None:
        query += " AND price >= ?"
        params.append(min_value)

    if max_value is not None:
        query += " AND price <= ?"
        params.append(max_value)

    query += " ORDER BY id DESC"

    conn = get_db()
    products = conn.execute(query, params).fetchall()
    conn.close()

    return render_template(
        "index.html",
        products=products,
        categories=CATEGORIES,
        conditions=list(ELIGIBLE_CONDITIONS),
        selected_category=category,
        selected_condition=condition,
        search=search,
        min_price=min_price,
        max_price=max_price
    )


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    conn = get_db()
    product = conn.execute(
        "SELECT * FROM products WHERE id = ?", (product_id,)
    ).fetchone()
    conn.close()

    if product is None:
        return "Produk tidak ditemukan", 404

    return render_template("product.html", product=product)


@app.route("/add", methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "")
        condition = request.form.get("condition", "")
        price = parse_price(request.form.get("price"))
        description = request.form.get("description", "").strip()
        image_file = request.files.get("image")

        if not name or category not in CATEGORIES or condition not in CONDITIONS:
            flash("Mohon isi data produk dengan benar.", "error")
            return render_template("add_product.html",
                                   categories=CATEGORIES, conditions=CONDITIONS)

        if price is None:
            flash("Harga harus berupa angka 0 atau lebih.", "error")
            return render_template("add_product.html",
                                   categories=CATEGORIES, conditions=CONDITIONS)

        # Solusi bisnis: sistem otomatis menentukan kelayakan.
        eligible = 1 if condition in ELIGIBLE_CONDITIONS else 0

        image_name = None
        if image_file and image_file.filename:
            if not allowed_file(image_file.filename):
                flash("Format foto harus PNG, JPG, JPEG, atau WEBP.", "error")
                return render_template("add_product.html",
                                       categories=CATEGORIES, conditions=CONDITIONS)

            safe_name = secure_filename(image_file.filename)
            image_name = f"{Path(safe_name).stem}_{os.urandom(4).hex()}{Path(safe_name).suffix.lower()}"
            image_file.save(UPLOAD_DIR / image_name)

        conn = get_db()
        cursor = conn.execute("""
            INSERT INTO products
            (name, category, condition, price, image, description, eligible)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, category, condition, price, image_name, description, eligible))
        product_id = cursor.lastrowid
        conn.commit()
        conn.close()

        if eligible:
            flash("Produk berhasil ditambahkan dan dinyatakan layak tampil.", "success")
        else:
            flash("Produk tersimpan, tetapi tidak ditampilkan karena tidak memenuhi kriteria kelayakan.", "warning")

        return redirect(url_for("product_detail", product_id=product_id))

    return render_template("add_product.html",
                           categories=CATEGORIES, conditions=CONDITIONS)




@app.route("/api/analyze-image", methods=["POST"])
def analyze_image():
    """Prototype visual check. Requires OPENAI_API_KEY in the server environment."""
    image_file = request.files.get("image")
    if not image_file or not image_file.filename:
        return jsonify({"ok": False, "message": "Pilih foto produk terlebih dahulu."}), 400
    if not allowed_file(image_file.filename):
        return jsonify({"ok": False, "message": "Format foto harus PNG, JPG, JPEG, atau WEBP."}), 400
    raw = image_file.read()
    if len(raw) > 8 * 1024 * 1024:
        return jsonify({"ok": False, "message": "Ukuran foto maksimal 8 MB."}), 400
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return jsonify({"ok": False, "configured": False,
            "message": "AI belum diaktifkan. Untuk analisis visual sungguhan, atur OPENAI_API_KEY di environment server. Foto belum dianalisis."}), 503
    mime = image_file.mimetype or "image/jpeg"
    data_url = "data:" + mime + ";base64," + base64.b64encode(raw).decode("ascii")
    try:
        response = requests.post("https://api.openai.com/v1/responses", timeout=45,
            headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"},
            json={"model": os.getenv("OPENAI_VISION_MODEL", "gpt-4.1-mini"),
                  "input": [{"role": "user", "content": [
                      {"type": "input_text", "text": "Analisis foto barang bekas untuk marketplace. Jelaskan hanya hal yang terlihat: jenis barang, kondisi visual yang tampak, kerusakan/cacat yang terlihat, dan keterbatasan foto. Jangan mengklaim dapat memastikan fungsi elektronik atau keaslian. Beri catatan bahwa ini bantuan awal dan bukan verifikasi final. Jawab ringkas dalam bahasa Indonesia."},
                      {"type": "input_image", "image_url": data_url}]}]})
        response.raise_for_status()
        payload = response.json()
        chunks = []
        for item in payload.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text": chunks.append(content.get("text", ""))
        result = "\n".join(chunks).strip()
        if not result: raise ValueError("Respons AI kosong")
        return jsonify({"ok": True, "analysis": result,
                        "notice": "Analisis visual AI adalah saran awal; periksa barang secara manual sebelum transaksi."})
    except requests.RequestException:
        app.logger.exception("AI image analysis request failed")
        return jsonify({"ok": False, "message": "Layanan AI gagal dihubungi. Coba lagi nanti."}), 502
    except (ValueError, KeyError):
        return jsonify({"ok": False, "message": "Hasil analisis AI tidak dapat dibaca."}), 502


@app.route("/admin/products")
def admin_products():
    conn = get_db()
    products = conn.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("admin.html", products=products)


@app.template_filter("rupiah")
def rupiah(value):
    return "Rp {:,}".format(value).replace(",", ".")


init_db()

if __name__ == "__main__":
    app.run(debug=True)
