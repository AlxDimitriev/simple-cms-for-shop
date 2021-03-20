from app.main.forms import EditItemForm, EditGroupForm, EditUserRightsForm
from flask import render_template, flash, redirect, url_for, request, session, current_app
from flask_login import current_user, login_required
from app.models import User, Item, Group
from app import db
from app.main import bp
from app.utils import upload_photo, edit_rights_required, admin_rights_required, delete_photo


@bp.route('/')
@bp.route('/index')
def index():
    return render_template('index.html', title='Home')


@bp.route('/add_item', methods=['GET', 'POST'])
@login_required
@edit_rights_required
def add_item():
    form = EditItemForm()
    if form.validate_on_submit():
        item = Item(title=form.title.data,
                    description=form.description.data,
                    price=form.price.data,
                    group_id=form.group_id.data,
                    photo_id=upload_photo(form.image.data) if form.image.data else None)
        db.session.add(item)
        db.session.commit()
        flash('Item have been created.')
        if 'editing_group' in session:
            return redirect(session['editing_group'])
    return render_template('add_item.html', title='Add item', form=form)


@bp.route('/edit_item/<item_id>', methods=['GET', 'POST'])
@login_required
@edit_rights_required
def edit_item(item_id):
    if 'editing_item' in session:
        del session['editing_item']
    item = Item.query.filter_by(id=item_id).first_or_404()
    form = EditItemForm()
    session['editing_item'] = url_for('main.edit_item', item_id=item_id)
    if form.validate_on_submit():  # Updating
        item.title = form.title.data
        item.description = form.description.data
        item.price = form.price.data
        item.group_id = form.group_id.data
        if item.photo_id:
            delete_photo(item.photo_id)
            item.photo_id = None
        if form.image.data:
            item.photo_id = upload_photo(form.image.data)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.edit_item', item_id=item.id))
    elif request.method == 'GET':  # Rendering
        form.title.data = item.title
        form.description.data = item.description
        form.price.data = item.price
        form.group_id.data = item.group_id
    return render_template('edit_item.html', title='Edit Item',
                           form=form, item=item)


@bp.route('/delete_item/<item_id>', methods=['GET', 'POST'])
@login_required
@edit_rights_required
def delete_item(item_id):
    item = Item.query.filter_by(id=item_id).first_or_404()
    group_id = item.group_id
    if item.photo_id:
        delete_photo(item.photo_id)
    db.session.delete(item)
    db.session.commit()
    flash('Item have been deleted.')
    return redirect(url_for('main.edit_group', group_id=group_id))


@bp.route('/item/<item_id>', methods=['GET'])
def show_item(item_id):
    item = Item.query.filter_by(id=item_id).first_or_404()
    return render_template('show_item.html', item=item)


@bp.route('/add_group', methods=['GET', 'POST'])
@login_required
@edit_rights_required
def add_group():
    form = EditGroupForm()
    if form.validate_on_submit():
        group = Group(name=form.name.data,
                      description=form.description.data,
                      photo_id=upload_photo(form.image.data) if form.image.data else None)
        db.session.add(group)
        db.session.commit()
        flash('Group have been created.')
        if 'editing_groups' in session:
            return redirect(session['editing_groups'])
    return render_template('add_group.html', title='Add group', form=form)


@bp.route('/edit_group/<group_id>', methods=['GET', 'POST'])
@login_required
@edit_rights_required
def edit_group(group_id):
    if 'editing_group' in session:
        del session['editing_group']
    group = Group.query.filter_by(id=group_id).first_or_404()
    form = EditGroupForm()
    page = request.args.get('page', 1, type=int)
    items = group.get_items().paginate(
        page, current_app.config['ITEMS_PER_PAGE'], True)
    next_url = url_for('edit_group', group_id=group_id, page=items.next_num) \
        if items.has_next else None
    prev_url = url_for('edit_group', group_id=group_id, page=items.prev_num) \
        if items.has_prev else None
    session['editing_group'] = url_for('main.edit_group', group_id=group_id)
    if form.validate_on_submit():  # Updating
        group.name = form.name.data
        group.description = form.description.data
        if group.photo_id:
            delete_photo(group.photo_id)
            group.photo_id = None
        if form.image.data:
            group.photo_id = upload_photo(form.image.data)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.edit_group', group_id=group.id))
    elif request.method == 'GET':  # Rendering
        form.name.data = group.name
        form.description.data = group.description
    return render_template('edit_group.html', title='Edit Group', form=form,
                           group=group, items=items.items, next_url=next_url,
                           prev_url=prev_url)


@bp.route('/delete_group/<group_id>', methods=['GET', 'POST'])
@login_required
@edit_rights_required
def delete_group(group_id):
    group = Group.query.filter_by(id=group_id).first_or_404()
    if group.photo_id:
        delete_photo(group.photo_id)
    db.session.delete(group)
    db.session.commit()
    flash('Group have been deleted.')
    return redirect(url_for('main.show_groups'))


@bp.route('/group/<group_id>', methods=['GET', 'POST'])
def show_group(group_id):
    group = Group.query.filter_by(id=group_id).first_or_404()
    page = request.args.get('page', 1, type=int)
    items = group.get_items().paginate(
        page, current_app.config['ITEMS_PER_PAGE'], True)
    next_url = url_for('main.show_group', group_id=group_id, page=items.next_num) \
        if items.has_next else None
    prev_url = url_for('main.show_group', group_id=group_id, page=items.prev_num) \
        if items.has_prev else None
    return render_template('show_group.html', group=group,
                           items=items.items, next_url=next_url, prev_url=prev_url)


@bp.route('/catalog', methods=['GET'])
def show_groups():
    if 'editing_groups' in session:
        del session['editing_groups']
    page = request.args.get('page', 1, type=int)
    groups = Group.query.paginate(
        page, current_app.config['ITEMS_PER_PAGE'], True)
    next_url = url_for('show_groups', page=groups.next_num) \
        if groups.has_next else None
    prev_url = url_for('show_groups', page=groups.prev_num) \
        if groups.has_prev else None
    session['editing_groups'] = url_for('main.show_groups')
    return render_template('show_groups.html', groups=groups.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/admin_panel', methods=['GET', 'POST'])
@login_required
@admin_rights_required
def admin_panel():
    page = request.args.get('page', 1, type=int)
    users = User.query.filter(User.id != current_user.id).paginate(
        page, current_app.config['USERS_PER_PAGE'], False)
    next_url = url_for('main.admin_panel', page=users.next_num) \
        if users.has_next else None
    prev_url = url_for('main.admin_panel', page=users.prev_num) \
        if users.has_prev else None
    return render_template('admin_panel.html', title='Admin Panel',
                           users=users.items, next_url=next_url,
                           prev_url=prev_url)


@bp.route('/admin_panel/<user_id>', methods=['GET', 'POST'])
@login_required
@admin_rights_required
def manage_user_rights(user_id):
    user = User.query.filter_by(id=user_id).first_or_404()
    form = EditUserRightsForm()
    if form.validate_on_submit():
        user.level = form.level.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.admin_panel'))
    elif request.method == 'GET':
        form.level.data = user.level
    return render_template('manage_user_rights.html', title='Manage User Rights',
                           form=form, user=user)


@bp.route('/delete_group_photos/<photo_id>', methods=['GET', 'POST'])
@login_required
@edit_rights_required
def delete_group_photos(photo_id):
    delete_photo(photo_id)
    flash('Photo have been deleted.')
    group = Group.query.filter_by(photo_id=photo_id).first()
    group.photo_id = None
    db.session.commit()
    return redirect(session['editing_group'])


@bp.route('/delete_item_photos/<photo_id>', methods=['GET', 'POST'])
@login_required
@edit_rights_required
def delete_item_photos(photo_id):
    delete_photo(photo_id)
    flash('Photo have been deleted.')
    item = Item.query.filter_by(photo_id=photo_id).first()
    item.photo_id = None
    db.session.commit()
    return redirect(session['editing_item'])
