from app.api import bp
from flask import jsonify, request, url_for, make_response
from app.api.auth import token_auth
from app.models import Item
from app import db
from app.api.errors import bad_request
from app.utils import delete_photo, permission_required


@bp.route('/items/<int:id>', methods=['GET'])
def get_item(id):
    return jsonify(Item.query.get_or_404(id).to_dict())


@bp.route('/items', methods=['POST'])
@token_auth.login_required
@permission_required('manager')
def add_item():
    data = request.get_json() or {}
    if 'title' not in data or 'price' not in data or 'category_id' not in data:
        return bad_request('must include title, price and category_id fields')
    item = Item()
    item.from_dict(data)
    db.session.add(item)
    db.session.commit()
    response = jsonify(item.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_item', id=item.id)
    return response


@bp.route('/items/<int:id>', methods=['PUT'])
@token_auth.login_required
@permission_required('manager')
def edit_item(id):
    item = Item.query.get_or_404(id)
    data = request.get_json() or {}
    if 'title' in data and data['title'] != item.title and \
            Item.query.filter_by(title=data['title']).first():
        return bad_request('please use a different title')
    item.from_dict(data)
    db.session.commit()
    return jsonify(item.to_dict())


@bp.route('/items/<int:id>', methods=['DELETE'])
@permission_required('manager')
def delete_item(id):
    item = Item.query.get_or_404(id)
    if item.photo_id:
        delete_photo(item.photo_id)
    db.session.delete(item)
    db.session.commit()
    return make_response(204)