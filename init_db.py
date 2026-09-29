from app import app, db, Usuario, Unidade, Especialidade, Militar

with app.app_context():
    db.drop_all()
    db.create_all()

    # cria utilizador admin inicial
    if not Usuario.query.filter_by(username="admin").first():
        u = Usuario(username="admin")
        u.set_password("1234")
        db.session.add(u)
        db.session.commit()
        print("Base de dados criada e utilizador admin inserido.")
    else:
        print("Utilizador admin já existe.")
