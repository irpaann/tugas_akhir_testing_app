from flask import Blueprint, request, render_template
from sqlalchemy import text
from extensions import db

search = Blueprint("search", __name__)

@search.route("/search")
def search_page():
    q = request.args.get("q", "")
    query = f"SELECT * FROM product WHERE name LIKE '%{q}%' OR description LIKE '%{q}%';"

    try:
        results = db.session.execute(text(query)).fetchall()
    except Exception as e:
        return f"<h3>SQL ERROR:</h3><pre>{e}</pre>"

    return render_template("search_results.html", q=q, results=results)
