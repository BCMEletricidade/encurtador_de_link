import os
import string
import random
import psycopg2
from flask import Flask, request, redirect, jsonify

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DATABASE_URL)

def gerar_codigo(tamanho=6):
    caracteres = string.ascii_letters + string.digits
    return ''.join(random.choice(caracteres) for _ in range(tamanho))

@app.route("/")
def home():
    return "API de encurtador rodando 🚀"

@app.route("/encurtar", methods=["POST"])
def encurtar():
    data = request.get_json()
    url = data.get("url")

    codigo = gerar_codigo()

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO urls (codigo, url_original) VALUES (%s, %s)",
        (codigo, url)
    )

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({
        "short_url": f"{request.host_url}{codigo}"
    })

@app.route("/<codigo>")
def redirecionar(codigo):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "SELECT url_original FROM urls WHERE codigo = %s",
        (codigo,)
    )

    result = cur.fetchone()

    if result:
        url = result[0]

        cur.execute(
            "UPDATE urls SET cliques = cliques + 1 WHERE codigo = %s",
            (codigo,)
        )
        conn.commit()

        cur.close()
        conn.close()

        return redirect(url)

    return "URL não encontrada", 404

if __name__ == "__main__":
    app.run()