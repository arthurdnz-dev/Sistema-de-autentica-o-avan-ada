import os
import sys
from app import create_app
from database import db, User

def init_database():
    env = os.getenv('FLASK_ENV', 'development')
    app = create_app(env)
    
    with app.app_context():
        db.create_all()
        print("Banco de dados inicializado")
        
        admin = User.query.filter_by(role='admin').first()
        if admin:
            print(f"Admin já existe: {admin.username}")
            return
        
        print("\ncriando usuário administrador...")
        email = input("Email do admin: ").strip()
        username = input("Usuário do admin: ").strip()
        password = input("Senha do admin: ")
        
        if not email or not username or not password:
            print("Dados incompletos")
            return
        
        if '@' not in email or '.' not in email:
            print("Email inválido")
            return
        
        if User.query.filter_by(email=email).first():
            print(f"Email {email} já registrado")
            return
        
        if User.query.filter_by(username=username).first():
            print(f"Usuário {username} já existe")
            return
        
        try:
            admin_user = User(
                email=email,
                username=username,
                role='admin',
                is_active=True
            )
            admin_user.set_password(password)
            
            db.session.add(admin_user)
            db.session.commit()
            
            print(f"\nAdmin criado com sucesso!")
            print(f"  Email: {email}")
            print(f"  Usuário: {username}")
            print(f"  Role: admin")
            
        except ValueError as e:
            print(f"Erro ao criar admin: {str(e)}")
            db.session.rollback()


if __name__ == '__main__':
    init_database()
