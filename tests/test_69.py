def test_issue69(db):
    db.query("CREATE table if not exists users (id text)")
    db.query("SELECT * FROM users WHERE id = :user", user="Te'ArnaLambert")
