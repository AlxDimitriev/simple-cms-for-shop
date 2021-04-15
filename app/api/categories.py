from app.api import bp
from flask import jsonify, request, url_for, make_response
from app.api.auth import token_auth
from app.models import Category
from app import db
from app.api.errors import bad_request
from app.utils import delete_photo, permission_required


@bp.route('/categories/<int:id>', methods=['GET'])
def get_category(id):
    return jsonify(Category.query.get_or_404(id).to_dict())


@bp.route('/categories', methods=['GET'])
def get_categories():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = Category.to_collection_dict(Category.query, page, per_page, 'api.get_categories')
    return jsonify(data)


@bp.route('/categories', methods=['POST'])
@token_auth.login_required
@permission_required('manager')
def add_category():
    data = request.get_json() or {}
    if 'name' not in data:
        return bad_request('must include name')
    category = Category()
    category.from_dict(data)
    db.session.add(category)
    db.session.commit()
    response = jsonify(category.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_category', id=category.id)
    return response


@bp.route('/categories/<int:id>', methods=['PUT'])
@token_auth.login_required
@permission_required('manager')
def edit_category(id):
    category = Category.query.get_or_404(id)
    data = request.get_json() or {}
    if 'name' in data and data['name'] != category.name and \
            Category.query.filter_by(name=data['name']).first():
        return bad_request('please use a different name')
    category.from_dict(data)
    db.session.commit()
    return jsonify(category.to_dict())


@bp.route('/categories/<int:id>', methods=['DELETE'])
@permission_required('manager')
def delete_category(id):
    category = Category.query.get_or_404(id)
    if category.photo_id:
        delete_photo(category.photo_id)
    db.session.delete(category)
    db.session.commit()
    return make_response(204)