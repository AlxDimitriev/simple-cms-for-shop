from app.main.forms import EditItemForm, EditCategoryForm, EditUserRightsForm, SearchForm
from flask import render_template, flash, redirect, url_for, request, session, current_app, g
from flask_login import current_user, login_required
from app.models import User, Item, Category
from app import db
from app.main import bp
from app.utils import upload_photo, delete_photo, permission_required


@bp.before_app_request
def before_request():
    g.search_form = SearchForm()


@bp.route('/')
@bp.route('/index')
def index():
    return render_template('index.html', title='Home')


@bp.route('/add_item', methods=['GET', 'POST'])
@login_required
@permission_required('manager')
def add_item():
    form = EditItemForm()
    if form.validate_on_submit():
        item = Item(
            title=form.title.data,
            description=form.description.data,
            price=form.price.data,
            category_id=form.category_id.data,
            photo_id=upload_photo(form.image.data) if form.image.data else None
        )
        db.session.add(item)
        db.session.commit()
        flash('Item have been created.')
        if 'editing_category' in session:
            return redirect(session['editing_category'])
    return render_template('add_item.html', title='Add item', form=form)


@bp.route('/edit_item/<item_id>', methods=['GET', 'POST'])
@login_required
@permission_required('manager')
def edit_item(item_id):
    if 'editing_item' in session:
        del session['editing_item']
    item = Item.query.filter_by(id=item_id).first_or_404()
    categories = Category.query.all()
    form = EditItemForm()
    form.categories.choices = [(category.id, category.name) for category in categories]
    session['editing_item'] = url_for('main.edit_item', item_id=item_id)
    if form.validate_on_submit():  # Updating
        item.title = form.title.data
        item.description = form.description.data
        item.price = form.price.data
        item.category_id = form.categories.data
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
        form.categories.data = item.category_id
    return render_template('edit_item.html', title='Edit Item',
                           form=form, item=item)


@bp.route('/delete_item/<item_id>', methods=['GET', 'POST'])
@login_required
@permission_required('manager')
def delete_item(item_id):
    item = Item.query.filter_by(id=item_id).first_or_404()
    category_id = item.category_id
    if item.photo_id:
        delete_photo(item.photo_id)
    db.session.delete(item)
    db.session.commit()
    flash('Item have been deleted.')
    return redirect(url_for('main.edit_group', category_id=category_id))


@bp.route('/item/<item_id>', methods=['GET'])
def show_item(item_id):
    item = Item.query.filter_by(id=item_id).first_or_404()
    return render_template('show_item.html', item=item)


@bp.route('/add_category', methods=['GET', 'POST'])
@login_required
@permission_required('manager')
def add_category():
    form = EditCategoryForm()
    if form.validate_on_submit():
        category = Category(
            name=form.name.data,
            description=form.description.data,
            photo_id=upload_photo(form.image.data) if form.image.data else None
        )
        db.session.add(category)
        db.session.commit()
        flash('Category have been created.')
        if 'editing_categories' in session:
            return redirect(session['editing_categories'])
    return render_template('add_category.html', title='Add category', form=form)


@bp.route('/edit_category/<category_id>', methods=['GET', 'POST'])
@login_required
@permission_required('manager')
def edit_category(category_id):
    if 'editing_category' in session:
        del session['editing_category']
    category = Category.query.filter_by(id=category_id).first_or_404()
    form = EditCategoryForm()
    page = request.args.get('page', 1, type=int)
    items = category.get_items().paginate(
        page, current_app.config['ITEMS_PER_PAGE'], True)
    next_url = url_for('edit_category', category_id=category_id, page=items.next_num) \
        if items.has_next else None
    prev_url = url_for('edit_category', category_id=category_id, page=items.prev_num) \
        if items.has_prev else None
    session['editing_category'] = url_for('main.edit_category', category_id=category_id)
    if form.validate_on_submit():  # Updating
        category.name = form.name.data
        category.description = form.description.data
        if category.photo_id:
            delete_photo(category.photo_id)
            category.photo_id = None
        if form.image.data:
            category.photo_id = upload_photo(form.image.data)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.edit_category', category_id=category.id))
    elif request.method == 'GET':  # Rendering
        form.name.data = category.name
        form.description.data = category.description
    return render_template('edit_category.html', title='Edit Category', form=form,
                           category=category, items=items.items, next_url=next_url,
                           prev_url=prev_url)


@bp.route('/delete_category/<category_id>', methods=['GET', 'POST'])
@login_required
@permission_required('manager')
def delete_category(category_id):
    category = Category.query.filter_by(id=category_id).first_or_404()
    if category.photo_id:
        delete_photo(category.photo_id)
    db.session.delete(category)
    db.session.commit()
    flash('Category have been deleted.')
    return redirect(url_for('main.show_categories'))


@bp.route('/category/<category_id>', methods=['GET', 'POST'])
def show_category(category_id):
    category = Category.query.filter_by(id=category_id).first_or_404()
    page = request.args.get('page', 1, type=int)
    items = category.get_items().paginate(
        page, current_app.config['ITEMS_PER_PAGE'], True)
    next_url = url_for('main.show_category', category_id=category_id, page=items.next_num) \
        if items.has_next else None
    prev_url = url_for('main.show_category', category_id=category_id, page=items.prev_num) \
        if items.has_prev else None
    return render_template('show_category.html', category=category,
                           items=items.items, next_url=next_url, prev_url=prev_url)


@bp.route('/catalog', methods=['GET'])
def show_categories():
    if 'editing_categories' in session:
        del session['editing_categories']
    page = request.args.get('page', 1, type=int)
    categories = Category.query.paginate(
        page, current_app.config['ITEMS_PER_PAGE'], True)
    next_url = url_for('show_categories', page=categories.next_num) \
        if categories.has_next else None
    prev_url = url_for('show_categories', page=categories.prev_num) \
        if categories.has_prev else None
    session['editing_categories'] = url_for('main.show_categories')
    return render_template('show_categories.html', categories=categories.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/admin_panel', methods=['GET', 'POST'])
@login_required
@permission_required('admin')
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
@permission_required('admin')
def manage_user_rights(user_id):
    user = User.query.filter_by(id=user_id).first_or_404()
    form = EditUserRightsForm(obj=user)
    form.permissions.choices = [('customer','Customer'), ('manager', 'Manager'), ('admin', 'Admin')]
    if request.method == 'POST':
        user.permission = form.permissions.data
        db.session.commit()
        flash('Your changes have been saved.')
    elif request.method == 'GET':
        form.permissions.data = user.permission
    return render_template('manage_user_rights.html', title='Manage User Rights',
                           form=form, user=user)


@bp.route('/delete_category_photos/<photo_id>', methods=['GET', 'POST'])
@login_required
@permission_required('manager')
def delete_category_photos(photo_id):
    delete_photo(photo_id)
    flash('Photo have been deleted.')
    category = Category.query.filter_by(photo_id=photo_id).first()
    category.photo_id = None
    db.session.commit()
    return redirect(session['editing_category'])


@bp.route('/delete_item_photos/<photo_id>', methods=['GET', 'POST'])
@login_required
@permission_required('manager')
def delete_item_photos(photo_id):
    delete_photo(photo_id)
    flash('Photo have been deleted.')
    item = Item.query.filter_by(photo_id=photo_id).first()
    item.photo_id = None
    db.session.commit()
    return redirect(session['editing_item'])


@bp.route('/search')
def search():
    if not g.search_form.validate():
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    items, total = Item.search(g.search_form.q.data, page,
                               current_app.config['ITEMS_PER_PAGE'])
    next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1) \
        if total > page * current_app.config['ITEMS_PER_PAGE'] else None
    prev_url = url_for('main.search', q=g.search_form.q.data, page=page - 1) \
        if page > 1 else None
    return render_template('search.html', title='Search', items=items,
                           next_url=next_url, prev_url=prev_url)