from flask import Blueprint, request, jsonify, current_app
from auth_service import AuthService
from jwt_manager import token_required, admin_required, role_required

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')
user_bp = Blueprint('user', __name__, url_prefix='/api/user')

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Dados não fornecidos'}), 400
    
    email = data.get('email', '').strip()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    user, errors = AuthService.register(email, username, password)
    
    if errors:
        return jsonify({'errors': errors}), 400
    
    return jsonify({
        'message': 'Usuário registrado com sucesso',
        'user': user.to_dict()
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Dados não fornecidos'}), 400
    
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'error': 'Usuário e senha são obrigatórios'}), 400
    
    result, error = AuthService.login(username, password)
    
    if error:
        return jsonify({'error': error}), 401
    
    return jsonify(result), 200


@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Dados não fornecidos'}), 400
    
    refresh_token = data.get('refresh_token')
    
    if not refresh_token:
        return jsonify({'error': 'Refresh token não fornecido'}), 400
    
    result, error = AuthService.refresh_token(refresh_token)
    
    if error:
        return jsonify({'error': error}), 401
    
    return jsonify(result), 200

@user_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(payload):
    user = AuthService.get_user(payload.get('user_id'))
    
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    return jsonify({'user': user}), 200

@user_bp.route('/logout', methods=['POST'])
@token_required
def logout(payload):
    data = request.get_json() or {}
    refresh_token = data.get('refresh_token')
    
    success, error = AuthService.logout(payload.get('user_id'), refresh_token)
    
    if not success:
        return jsonify({'error': error}), 400
    
    return jsonify({'message': 'Logout realizado com sucesso'}), 200


@user_bp.route('/change-password', methods=['POST'])
@token_required
def change_password(payload):
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Dados não fornecidos'}), 400
    
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')
    
    if not old_password or not new_password:
        return jsonify({'error': 'Senhas são obrigatórias'}), 400
    
    success, error = AuthService.change_password(
        payload.get('user_id'),
        old_password,
        new_password
    )
    
    if not success:
        return jsonify({'error': error}), 400
    
    return jsonify({'message': 'Senha alterada com sucesso'}), 200

@admin_bp.route('/users', methods=['GET'])
@token_required
@admin_required
def list_users(payload):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    if per_page > 100:
        per_page = 100
    
    result = AuthService.list_users(page, per_page)
    return jsonify(result), 200


@admin_bp.route('/users/<int:user_id>/role', methods=['PUT'])
@token_required
@admin_required
def update_user_role(payload, user_id):
    if payload.get('user_id') == user_id:
        return jsonify({'error': 'Não é possível alterar seu próprio role'}), 400
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Dados não fornecidos'}), 400
    
    new_role = data.get('role', '').strip()
    
    if not new_role:
        return jsonify({'error': 'Role é obrigatório'}), 400
    
    success, error = AuthService.update_user_role(user_id, new_role)
    
    if not success:
        return jsonify({'error': error}), 400
    
    return jsonify({'message': 'Role atualizado com sucesso'}), 200


@admin_bp.route('/users/<int:user_id>/deactivate', methods=['POST'])
@token_required
@admin_required
def deactivate_user(payload, user_id):
    if payload.get('user_id') == user_id:
        return jsonify({'error': 'Não é possível desativar sua própria conta'}), 400
    
    success, error = AuthService.deactivate_user(user_id)
    
    if not success:
        return jsonify({'error': error}), 400
    
    return jsonify({'message': 'Usuário desativado com sucesso'}), 200

@admin_bp.route('/protected-resource', methods=['GET'])
@token_required
@role_required('moderator')
def protected_resource(payload):
    return jsonify({
        'message': 'Acesso concedido',
        'user': payload.get('username'),
        'role': payload.get('role')
    }), 200

@auth_bp.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Requisição inválida'}), 400

@auth_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({'error': 'Não autorizado'}), 401

@auth_bp.errorhandler(403)
def forbidden(error):
    return jsonify({'error': 'Acesso negado'}), 403

@auth_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Recurso não encontrado'}), 404

@auth_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Erro interno do servidor'}), 500
