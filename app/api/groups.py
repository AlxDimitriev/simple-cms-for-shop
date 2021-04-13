from app.api import bp
from flask import jsonify, request, url_for, make_response
from app.api.auth import token_auth
from app.models import Group
from app import db
from app.api.errors import bad_request
from app.utils import delete_photo, permission_required


@bp.route('/groups/<int:id>', methods=['GET'])
def get_group(id):
    return jsonify(Group.query.get_or_404(id).to_dict())


@bp.route('/groups', methods=['GET'])
def get_groups():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = Group.to_collection_dict(Group.query, page, per_page, 'api.get_groups')
    return jsonify(data)


@bp.route('/groups', methods=['POST'])
@token_auth.login_required
@permission_required('manager')
def add_group():
    data = request.get_json() or {}
    if 'name' not in data:
        return bad_request('must include name')
    group = Group()
    group.from_dict(data)
    db.session.add(group)
    db.session.commit()
    response = jsonify(group.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_group', id=group.id)
    return response


@bp.route('/groups/<int:id>', methods=['PUT'])
@token_auth.login_required
@permission_required('manager')
def edit_group(id):
    group = Group.query.get_or_404(id)
    data = request.get_json() or {}
    if 'name' in data and data['name'] != group.name and \
            Group.query.filter_by(name=data['name']).first():
        return bad_request('please use a different name')
    group.from_dict(data)
    db.session.commit()
    return jsonify(group.to_dict())


@bp.route('/groups/<int:id>', methods=['DELETE'])
@permission_required('manager')
def delete_group(id):
    group = Group.query.get_or_404(id)
    if group.photo_id:
        delete_photo(group.photo_id)
    db.session.delete(group)
    db.session.commit()
    return make_response(204)