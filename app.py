from flask import Flask, render_template, request, jsonify, redirect, session
from datetime import date
import sqlite3
import qrcode
import io
import base64

app = Flask(__name__)
app.secret_key = "abc123"


@app.route("/")
def login():
    	return render_template("login.html")

@app.route("/login", methods=["POST"])
def do_login():

    email = request.form["email"]
    password = request.form["password"]
    role = request.form["role"]

    conn = sqlite3.connect("app.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM users
        WHERE email=?
        AND password=?
        AND role=?
    """, (email, password, role))

    user = cur.fetchone()

    conn.close()

    if user is None:
        return "メールアドレス・パスワード・役割が違います"

    # ---------- session保存 ----------
    session["user_id"] = user["id"]
    session["role"] = user["role"]
    session["family_id"] = user["family_id"]
    session["name"] = user["name"]

    # ---------- 親子で画面を分ける ----------
    if user["role"] == "parent":
        return redirect("/parent_home")

    return redirect("/home")

@app.route("/logout",methods=["POST"])
def logout():

    session.clear()

    return redirect("/")

@app.route("/home")
def home():

    if "user_id" not in session:
        return redirect("/")

    if session["role"] != "child":
        return redirect("/parent_home")

    return render_template(
        "Home_child.html",
        today=date.today()
    )

@app.route("/parent_home")
def parent_home():

    if "user_id" not in session:
        return redirect("/")

    if session["role"] != "parent":
        return redirect("/home")

    return render_template(
        "Home_parent.html",
        family_id=session["family_id"]
    )

@app.route("/touroku", methods=["GET", "POST"])
def touroku():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        conn = sqlite3.connect("app.db")
        conn.row_factory=sqlite3.Row
        cur = conn.cursor()
	  #-----親登録-----
        if role=="parent":
            cur.execute("""
                  INSERT INTO users
                  (name,email,password,role)
                  VALUES(?,?,?,?)
                  """,(name,email,password,role))
            #今追加した親のID
            parent_id=cur.lastrowid
            #family_id=親のid
            cur.execute("""
                  UPDATE users
                  SET family_id=?
                  WHERE id=?
                  """,(parent_id,parent_id))
        #-----子供登録-----
        else:
            family_id=request.form["family_id"]
            cur.execute("""
                  INSERT INTO users
                  (name,email,password,role,family_id)
                  VALUES(?,?,?,?,?)
                  """,(name,email,password,role,family_id))
        conn.commit()
        conn.close()
        return redirect("/")
    return render_template("touroku.html")


@app.route("/get_schedule")
def get_schedule():

    # カレンダーで押された日付を取得
    date = request.args.get("date")
    conn = sqlite3.connect("app.db")
    # DBのデータを辞書形式で取得するため
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT
            hl.id,
            h.title,
            h.color,
            h.reward,
            hl.status
        FROM help_log hl
        JOIN help h
        ON hl.help_id = h.id
        WHERE hl.done_date = ?
        AND hl.child_id = ?
    """, (
        date,
        session["user_id"]
    ))

    rows = cur.fetchall()
    conn.close()
    # JavaScriptへ渡すデータ
    tasks = []

    for row in rows:

        tasks.append({

            "id": row["id"],

            "title": row["title"],

            "color": row["color"],

            "reward": row["reward"],

            "status": row["status"]

        })
    return jsonify(tasks)

@app.route("/get_parent_schedule")
def get_parent_schedule():

    date = request.args.get("date")

    conn = sqlite3.connect("app.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT
            hl.id,
            h.title,
            h.color,
            h.reward,
            hl.status

        FROM help_log hl

        JOIN help h
        ON hl.help_id = h.id

        WHERE hl.done_date = ?
        AND h.family_id = ?
    """, (
        date,
        session["family_id"]
    ))

    rows = cur.fetchall()

    conn.close()

    tasks = []

    for row in rows:

        tasks.append({
            "id": row["id"],
            "title": row["title"],
            "color": row["color"],
            "reward": row["reward"],
            "status": row["status"]
        })

    return jsonify(tasks)

@app.route("/get_parent_calendar")
def get_parent_calendar():

    conn = sqlite3.connect("app.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT
            hl.done_date,
            h.title,
            h.color
        FROM help_log hl
        JOIN help h
        ON hl.help_id = h.id
        WHERE h.family_id = ?
    """, (
        session["family_id"],
    ))

    rows = cur.fetchall()
    conn.close()

    events = []

    for row in rows:

        events.append({
            "title": row["title"],
            "start": row["done_date"],
            "color": row["color"]
        })

    return jsonify(events)

@app.route("/approve_help", methods=["POST"])
def approve_help():

    data = request.get_json()

    help_log_id = data["id"]

    conn = sqlite3.connect("app.db")
    cur = conn.cursor()

    cur.execute("""
        UPDATE help_log
        SET status = 'approved'
        WHERE id = ?
    """, (
        help_log_id,
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "message": "承認しました！"
    })

@app.route("/get_calendar")
def get_calendar():

    conn = sqlite3.connect("app.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT
            hl.done_date,
            h.title,
            h.color
        FROM help_log hl
        JOIN help h
        ON hl.help_id = h.id
        WHERE hl.child_id = ?
    """, (session["user_id"],))

    rows = cur.fetchall()

    conn.close()

    events = []

    for row in rows:

        events.append({
            "title": row["title"],
            "start": row["done_date"],
            "color": row["color"]
        })

    return jsonify(events)

@app.route("/money")
def money():
    today = date.today()
    year = int(request.args.get("year", today.year))
    month = int(request.args.get("month", today.month))

    mode = request.args.get("mode", "month")

    conn = sqlite3.connect("app.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    if mode == "month":
        cur.execute("""
            SELECT
                h.title,
                COUNT(*) AS days,
                COUNT(*) * h.reward AS reward
            FROM help_log hl
            JOIN help h
            ON hl.help_id = h.id
            WHERE h.family_id = ?
            AND hl.status='approved'
            AND strftime('%Y', hl.done_date) = ?
            AND strftime('%m', hl.done_date) = ?
            GROUP BY h.id
        """, (
            session["family_id"],
            str(year),
            f"{month:02d}"
        ))

        help_list = cur.fetchall()

        total_days = sum(row["days"] for row in help_list)
        total_money = sum(row["reward"] for row in help_list)

    else:
        cur.execute("""
            SELECT
                strftime('%m', hl.done_date) AS title,
                SUM(h.reward) AS reward
            FROM help_log hl
            JOIN help h
            ON hl.help_id = h.id
            WHERE h.family_id = ?
            AND hl.status='approved'
            AND strftime('%Y', hl.done_date) = ?
            GROUP BY strftime('%m', hl.done_date)
            ORDER BY title
        """, (
            session["family_id"],
            str(year)
        ))

        help_list = cur.fetchall()

        total_days = 0
        total_money = sum(row["reward"] for row in help_list)

    target = 12000

    conn.close()

    return render_template(
        "Money_child_1.html",
        help_list=help_list,
        total_days=total_days,
        total_money=total_money,
        target=target,
        mode=mode,
        year=year,
        month=month
    )

@app.route("/complete_help", methods=["POST"])
def complete_help():

    data = request.get_json()

    help_log_id = data["id"]


    conn = sqlite3.connect("app.db")
    cur = conn.cursor()


    cur.execute("""
        UPDATE help_log
        SET status = 'completed'
        WHERE id = ?
    """, (
        help_log_id,
    ))


    conn.commit()
    conn.close()


    return jsonify({
        "message": "完了しました！"
    })


@app.route("/add_money", methods=["GET", "POST"])
def add_money():
    conn = sqlite3.connect("app.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # ＋ボタンが押された時
    if request.method == "POST":
        memo = request.form["memo"]
        amount = request.form["amount"]

        cur.execute("""
            INSERT INTO money
            (users_id, amount, type, memo)
            VALUES (?, ?, ?, ?)
        """, (session["user_id"], amount, "spend", memo))

        conn.commit()
        conn.close()
        return redirect("/add_money")

    # 一覧を取得
    cur.execute("""
        SELECT memo, amount
        FROM money
        WHERE type = 'spend'
        ORDER BY created DESC
    """)

    spend_list = cur.fetchall()
    conn.close()

    return render_template(
        "Money_child_2.html",
        spend_list=spend_list
    )

#お手伝い追加画面
@app.route("/parent_help", methods=["GET","POST"])
def parent_help():

    if session["role"] != "parent":
        return redirect("/")

    conn=sqlite3.connect("app.db")
    conn.row_factory=sqlite3.Row
    cur=conn.cursor()

    if request.method=="POST":

        title=request.form["title"]
        reward=request.form["reward"]
        color=request.form["color"]

        cur.execute("""
        INSERT INTO help
        (family_id,title,reward,color)
        VALUES(?,?,?,?)
        """,(
            session["family_id"],
            title,
            reward,
            color
        ))

        conn.commit()

        return redirect("/parent_help")

    cur.execute("""
    SELECT *
    FROM help
    WHERE family_id=?
    AND is_deleted=0
    ORDER BY id DESC
    """,(session["family_id"],))

    help_list=cur.fetchall()

    conn.close()

    return render_template(
        "help_parent.html",
        help_list=help_list
    )


@app.route("/add_shift")
def add_shift():

    # 子供だけが使える
    if "user_id" not in session:
        return redirect("/")

    if session["role"] != "child":
        return redirect("/parent_home")

    # Home画面から渡ってきた日付を取得
    selected_date = request.args.get("date")

    conn = sqlite3.connect("app.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # その家族のお手伝い一覧を取得
    cur.execute("""
        SELECT *
        FROM help
        WHERE family_id = ?
        AND is_deleted = 0
        ORDER BY id DESC
    """, (session["family_id"],))

    help_list = cur.fetchall()

    conn.close()

    return render_template(
        "Add_shift.html",
        help_list=help_list,
        selected_date=selected_date
    )

@app.route("/save_shift", methods=["POST"])
def save_shift():

    # ログインしていない場合
    if "user_id" not in session:
        return redirect("/")

    # 子供だけ使える
    if session["role"] != "child":
        return redirect("/parent_home")

    help_id = request.form["help_id"]
    done_date = request.form["done_date"]

    conn = sqlite3.connect("app.db")
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO help_log
        (child_id, help_id, status, done_date)
        VALUES (?, ?, ?, ?)
    """, (
        session["user_id"],
        help_id,
        "pending",
        done_date
    ))

    conn.commit()
    conn.close()

    return redirect("/home")

@app.route("/family_qr")
def family_qr():

    if "user_id" not in session:
        return redirect("/")

    if session["role"] != "parent":
        return redirect("/home")

    family_id = session["family_id"]

    # QRコードに入れるURL
    url = request.host_url + "touroku?family_id=" + str(family_id)

    qr = qrcode.make(url)

    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")

    img = base64.b64encode(buffer.getvalue()).decode()

    return render_template(
        "family_qr.html",
        img=img
    )

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5003,
        debug=True
    )