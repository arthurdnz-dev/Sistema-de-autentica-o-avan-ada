import requests
import json
from typing import Dict, Any

BASE_URL = 'http://localhost:5000/api'

class AuthAPITester:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.access_token = None
        self.refresh_token = None
        self.user_id = None
    
    def _print_response(self, title: str, status_code: int, data: Any):
        print(f"\n{'='*60}")
        print(f"{title} (Status: {status_code})")
        print(f"{'='*60}")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    
    def register(self, email: str, username: str, password: str):
        url = f'{self.base_url}/auth/register'
        payload = {
            'email': email,
            'username': username,
            'password': password
        }
        
        response = requests.post(url, json=payload)
        data = response.json()
        
        self._print_response('Registro', response.status_code, data)
        
        if response.status_code == 201:
            self.user_id = data['user']['id']
            return True
        return False
    
    def login(self, username: str, password: str):
        url = f'{self.base_url}/auth/login'
        payload = {
            'username': username,
            'password': password
        }
        
        response = requests.post(url, json=payload)
        data = response.json()
        
        self._print_response('Login', response.status_code, data)
        
        if response.status_code == 200:
            self.access_token = data['access_token']
            self.refresh_token = data['refresh_token']
            self.user_id = data['user']['id']
            return True
        return False
    
    def get_profile(self):
        url = f'{self.base_url}/user/profile'
        headers = {'Authorization': f'Bearer {self.access_token}'}
        
        response = requests.get(url, headers=headers)
        data = response.json()
        
        self._print_response('Perfil do Usuário', response.status_code, data)
        
        return response.status_code == 200
    
    def change_password(self, old_password: str, new_password: str):
        url = f'{self.base_url}/user/change-password'
        headers = {'Authorization': f'Bearer {self.access_token}'}
        payload = {
            'old_password': old_password,
            'new_password': new_password
        }
        
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        
        self._print_response('Alteração de Senha', response.status_code, data)
        
        return response.status_code == 200
    
    def refresh_access(self):
        url = f'{self.base_url}/auth/refresh'
        payload = {'refresh_token': self.refresh_token}
        
        response = requests.post(url, json=payload)
        data = response.json()
        
        self._print_response('Refresh Token', response.status_code, data)
        
        if response.status_code == 200:
            self.access_token = data['access_token']
            return True
        return False
    
    def logout(self):
        url = f'{self.base_url}/user/logout'
        headers = {'Authorization': f'Bearer {self.access_token}'}
        payload = {'refresh_token': self.refresh_token}
        
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        
        self._print_response('Logout', response.status_code, data)
        
        return response.status_code == 200
    
    def list_users(self):
        url = f'{self.base_url}/admin/users'
        headers = {'Authorization': f'Bearer {self.access_token}'}
        
        response = requests.get(url, headers=headers)
        data = response.json()
        
        self._print_response('Listar Usuários', response.status_code, data)
        
        return response.status_code == 200
    
    def update_user_role(self, user_id: int, role: str):
        url = f'{self.base_url}/admin/users/{user_id}/role'
        headers = {'Authorization': f'Bearer {self.access_token}'}
        payload = {'role': role}
        
        response = requests.put(url, json=payload, headers=headers)
        data = response.json()
        
        self._print_response(f'Atualizar Role para {role}', response.status_code, data)
        
        return response.status_code == 200
    
    def test_invalid_token(self):
        url = f'{self.base_url}/user/profile'
        headers = {'Authorization': 'Bearer invalid_token_here'}
        
        response = requests.get(url, headers=headers)
        data = response.json()
        
        self._print_response('Token Inválido (Esperado falhar)', response.status_code, data)
        
        return response.status_code == 401
    
    def health_check(self):
        url = 'http://localhost:5000/health'
        
        response = requests.get(url)
        data = response.json()
        
        self._print_response('Health Check', response.status_code, data)
        return response.status_code == 200


def run_tests():
    print("\n" + "="*60)
    print("TESTE DA API DE AUTENTICAÇÃO")
    print("="*60)
    
    tester = AuthAPITester()
    
    try:
        tester.health_check()
    except requests.exceptions.ConnectionError:
        print("\nERRO: Servidor não está rodando em http://localhost:5000")
        print("Inicie com: python app.py")
        return
    
    print("\nIniciando testes...\n")
    
        print("Testando Registro")
    tester.register(
        email='teste@example.com',
        username='usuario_teste',
        password='SenhaForte123!@#'
    )
    
    print("\nTestando Login")
    tester.login(username='usuario_teste', password='SenhaForte123!@#')
    
    print("\nTestando Obtenção de Perfil")
    tester.get_profile()
    
    print("\nTestando Refresh de Token")
    tester.refresh_access()
    
    print("\nTestando Alteração de Senha")
    tester.change_password(
        old_password='SenhaForte123!@#',
        new_password='NovaSenha456!@#$'
    )
    
    print("\nTestando Login com Nova Senha")
    tester.login(username='usuario_teste', password='NovaSenha456!@#$')
    
    print("\nTestando Token Inválido (deve falhar)")
    tester.test_invalid_token()
  
    print("\nTestando Logout")
    tester.logout()
    
    print("\n" + "="*60)
    print("TESTES CONCLUÍDOS")
    print("="*60 + "\n")

if __name__ == '__main__':
    run_tests()