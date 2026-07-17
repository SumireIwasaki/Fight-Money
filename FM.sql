--ユーザー＋家族--
CREATE TABLE users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    role TEXT CHECK(role IN ('parent','child')) NOT NULL,
    password TEXT NOT NULL,
    family_id INTEGER
);

--お金--
CREATE TABLE money(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    users_id INTEGER NOT NULL,
    amount INTEGER NOT NULL,
    type TEXT CHECK(type IN ('reward','spend','adjust')) NOT NULL,
    help_id INTEGER,
    memo TEXT,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

--お手伝い（お手伝い名、１回あたりの報酬）--
CREATE TABLE help(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    family_id INTEGER,
    title TEXT NOT NULL,
    reward INTEGER
);

--お手伝いログ--
CREATE TABLE help_log(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    child_id INTEGER,
    help_id INTEGER,
    status TEXT CHECK(status IN ('pending','approved')),
    done_date DATE,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


--欲しいもの--
CREATE TABLE goals(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    users_id INTEGER,
    title TEXT NOT NULL,
    amount INTEGER
);