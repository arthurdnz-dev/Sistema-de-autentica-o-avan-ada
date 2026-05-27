
import os
import shutil

ENV_EXAMPLE_CONTENT = """FLASK_ENV=development
FLASK_DEBUG=True
PORT=5000

SECRET_KEY=sua-chave-secreta-muito-segura-aqui
JWT_SECRET=sua-jwt-secret-chave-muito-segura-aqui

DATABASE_URL=sqlite:///app.db
"""

def setup():
    print("=" * 60)
    print("CONFIGURAÇÃO DO SISTEMA DE AUTENTICAÇÃO")
    print("=" * 60)
    
    if not os.path.exists('.env.example'):
        with open('.env.example', 'w') as f:
            f.write(ENV_EXAMPLE_CONTENT)
        print("Arquivo .env.example criado")
    
    if os.path.exists('.env'):
        resposta = input("\n.env já existe. Deseja sobrescrever? (s/n): ").strip().lower()
        if resposta != 's':
            print("Arquivo .env mantido")
        else:
            shutil.copy('.env.example', '.env')
            print("Arquivo .env copiado de .env.example")
    else:
        shutil.copy('.env.example', '.env')
        print("Arquivo .env criado")
    
    if not os.path.exists('instance'):
        os.makedirs('instance')
        print("Pasta instance criada")
    
    print("\n" + "=" * 60)
    print("PRÓXIMOS PASSOS:")
    print("=" * 60)
    print("1. python init_db.py    (criar usuário admin)")
    print("2. python app.py        (iniciar servidor)")
    print("3. python test_api.py   (testar endpoints)")
    print("=" * 60 + "\n")


if __name__ == '__main__':
    setup()

if __name__ == '__main__':
    setup()