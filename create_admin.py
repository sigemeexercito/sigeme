from app import app, db, Usuario

with app.app_context():
    if not Usuario.query.filter_by(username="admin").first():
        u = Usuario(username="admin")
        u.set_password("1234")
        db.session.add(u)
        db.session.commit()
        print("Usuário admin criado com sucesso!")
    else:
        print("Usuário admin já existe.")

