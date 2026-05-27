from database import User, AuditLog, RefreshToken, db
from jwt_manager import JWTManager
from flask import request
from datetime import datetime
import re

class AuthService:
    @staticmethod
    def register(email, username, password):
        errors = AuthService._validate_registration(email, username, password)
        if errors:
            return None, errors
        
        if User.query.filter_by(email=email).first():
            return None, {'email': 'Email já registrado'}
        
        if User.query.filter_by(username=username).first():
            return None, {'username': 'Usuário já existe'}
        
        user = User(email=email, username=username)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        AuthService._log_audit('register', user.id, 'user', 'Novo usuário registrado')
        
        return user, None
    
    @staticmethod
    def login(username, password):
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            AuthService._log_audit('login_failed', None, 'user', f'Falha ao autenticar {username}', 'failed')
            return None, 'Usuário ou senha inválidos'
        
        if not user.is_active:
            AuthService._log_audit('login_blocked', user.id, 'user', 'Usuário inativo', 'failed')
            return None, 'Usuário desativado'
        
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        access_token, refresh_token = JWTManager.generate_tokens(
            user.id, user.username, user.role
        )
        
        AuthService._log_audit('login_success', user.id, 'user', 'Login bem-sucedido')
        
        return {
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }, None
    
    @staticmethod
    def logout(user_id, refresh_token):
        try:
            refresh_db = RefreshToken.query.filter_by(is_revoked=False).first()
            if refresh_db and refresh_db.user_id == user_id:
                refresh_db.is_revoked = True
                db.session.commit()
            
            AuthService._log_audit('logout', user_id, 'user', 'Logout realizado')
            return True, None
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def refresh_token(refresh_token):
        new_access_token = JWTManager.refresh_access_token(refresh_token)
        
        if not new_access_token:
            return None, 'Refresh token inválido ou expirado'
        
        return {'access_token': new_access_token}, None
    
    @staticmethod
    def change_password(user_id, old_password, new_password):
        user = User.query.get(user_id)
        if not user:
            return False, 'Usuário não encontrado'
        
        if not user.check_password(old_password):
            AuthService._log_audit('password_change_failed', user_id, 'user', 'Falha ao alterar senha', 'failed')
            return False, 'Senha atual incorreta'
        
        errors = AuthService._validate_password(new_password)
        if errors:
            return False, errors
        
        user.set_password(new_password)
        db.session.commit()
        
        RefreshToken.query.filter_by(user_id=user_id, is_revoked=False).update({'is_revoked': True})
        db.session.commit()
        
        AuthService._log_audit('password_changed', user_id, 'user', 'Senha alterada com sucesso')
        
        return True, None
    
    @staticmethod
    def get_user(user_id):
        user = User.query.get(user_id)
        if not user:
            return None
        return user.to_dict()
    
    @staticmethod
    def list_users(page=1, per_page=20):
        paginated = User.query.paginate(page=page, per_page=per_page, error_out=False)
        
        return {
            'users': [user.to_dict() for user in paginated.items],
            'total': paginated.total,
            'pages': paginated.pages,
            'current_page': page
        }
    
    @staticmethod
    def update_user_role(user_id, new_role):
        valid_roles = ['user', 'moderator', 'admin']
        if new_role not in valid_roles:
            return False, f'Role inválida. Opções: {valid_roles}'
        
        user = User.query.get(user_id)
        if not user:
            return False, 'Usuário não encontrado'
        
        old_role = user.role
        user.role = new_role
        db.session.commit()
        
        AuthService._log_audit('role_updated', user_id, 'user', f'Role alterado de {old_role} para {new_role}')
        
        return True, None
    
    @staticmethod
    def deactivate_user(user_id):
        user = User.query.get(user_id)
        if not user:
            return False, 'Usuário não encontrado'
        
        user.is_active = False
        RefreshToken.query.filter_by(user_id=user_id, is_revoked=False).update({'is_revoked': True})
        db.session.commit()
        
        AuthService._log_audit('user_deactivated', user_id, 'user', 'Usuário desativado')
        
        return True, None
    
    @staticmethod
    def _validate_registration(email, username, password):
        errors = {}
        
        if not email or not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            errors['email'] = 'Email inválido'
        
        if not username or len(username) < 3 or len(username) > 80:
            errors['username'] = 'Usuário deve ter entre 3 e 80 caracteres'
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            errors['username'] = 'Usuário pode conter apenas letras, números, - e _'
        
        password_errors = AuthService._validate_password(password)
        if password_errors:
            errors.update(password_errors)
        
        return errors
    
    @staticmethod
    def _validate_password(password):
        errors = {}
        
        if len(password) < 8:
            errors['password'] = 'Senha deve ter pelo menos 8 caracteres'
        
        if not re.search(r'[a-z]', password):
            errors['password'] = 'Senha deve conter letras minúsculas'
        
        if not re.search(r'[A-Z]', password):
            errors['password'] = 'Senha deve conter letras maiúsculas'
        
        if not re.search(r'[0-9]', password):
            errors['password'] = 'Senha deve conter números'
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors['password'] = 'Senha deve conter caracteres especiais'
        
        return errors
    
    @staticmethod
    def _log_audit(action, user_id, resource, details, status='success'):
        try:
            ip_address = request.remote_addr or 'unknown'
        except:
            ip_address = 'unknown'
        
        log = AuditLog(
            user_id=user_id,
            action=action,
            resource=resource,
            details=details,
            ip_address=ip_address,
            status=status
        )
        db.session.add(log)
        db.session.commit()
