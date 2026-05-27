import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from database import RefreshToken, db
import bcrypt

class JWTManager:
    @staticmethod
    def generate_tokens(user_id, username, role):
        now = datetime.utcnow()
        access_payload = {
            'user_id': user_id,
            'username': username,
            'role': role,
            'type': 'access',
            'iat': now,
            'exp': now + current_app.config['JWT_EXPIRATION']
        }
        
        refresh_payload = {
            'user_id': user_id,
            'type': 'refresh',
            'iat': now,
            'exp': now + current_app.config['JWT_REFRESH_EXPIRATION']
        }
        
        access_token = jwt.encode(
            access_payload,
            current_app.config['JWT_SECRET'],
            algorithm=current_app.config['JWT_ALGORITHM']
        )
        
        refresh_token = jwt.encode(
            refresh_payload,
            current_app.config['JWT_SECRET'],
            algorithm=current_app.config['JWT_ALGORITHM']
        )
        
        token_hash = bcrypt.hashpw(
            refresh_token.encode('utf-8'),
            bcrypt.gensalt(rounds=10)
        ).decode('utf-8')
        
        refresh_db = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=now + current_app.config['JWT_REFRESH_EXPIRATION']
        )
        db.session.add(refresh_db)
        db.session.commit()
        
        return access_token, refresh_token
    
    @staticmethod
    def verify_token(token, token_type='access'):
        try:
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET'],
                algorithms=[current_app.config['JWT_ALGORITHM']]
            )
            
            if payload.get('type') != token_type:
                return None
            
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    @staticmethod
    def refresh_access_token(refresh_token):
        payload = JWTManager.verify_token(refresh_token, 'refresh')
        if not payload:
            return None
        
        user_id = payload.get('user_id')
                refresh_db = RefreshToken.query.filter_by(is_revoked=False).first()
        if not refresh_db or not refresh_db.is_valid():
            return None
        
        if not bcrypt.checkpw(
            refresh_token.encode('utf-8'),
            refresh_db.token_hash.encode('utf-8')
        ):
            return None
        
        from database import User
        user = User.query.get(user_id)
        if not user or not user.is_active:
            return None
        
        now = datetime.utcnow()
        access_payload = {
            'user_id': user.id,
            'username': user.username,
            'role': user.role,
            'type': 'access',
            'iat': now,
            'exp': now + current_app.config['JWT_EXPIRATION']
        }
        
        access_token = jwt.encode(
            access_payload,
            current_app.config['JWT_SECRET'],
            algorithm=current_app.config['JWT_ALGORITHM']
        )
        
        return access_token


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'error': 'Token inválido'}), 401
        
        if not token:
            return jsonify({'error': 'Token ausente'}), 401
        
        payload = JWTManager.verify_token(token, 'access')
        if not payload:
            return jsonify({'error': 'Token expirado ou inválido'}), 401
        
        return f(payload, *args, **kwargs)
    
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(payload, *args, **kwargs):
        if payload.get('role') != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403
        
        return f(payload, *args, **kwargs)
    
    return decorated


def role_required(required_role):
    def decorator(f):
        @wraps(f)
        def decorated(payload, *args, **kwargs):
            from database import User
            user = User.query.get(payload.get('user_id'))
            
            if not user or not user.has_permission(required_role):
                return jsonify({'error': 'Permissão insuficiente'}), 403
            
            return f(payload, *args, **kwargs)
        
        return decorated
    
    return decorator
