from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, flash, redirect, session, url_for, current_app
from app import db
from models.users import User
from models.items import Item

auth_bp = Blueprint('auth_bp', __name__)

# First Page render when we run the application
@auth_bp.route('/')
def home():
    current_app.logger.info('Home page accessed')
    return render_template('home.html')

# Registration Route
@auth_bp.route('/register', methods=['POST', 'GET'])
def register():
    msg = ""
    if request.method == 'POST':
        data = request.form
        first_name = data.get('first-name')
        last_name = data.get('last-name')
        dob = data.get('dob')
        phone_no = data.get('phone')
        role = data.get('role')
        email = data.get('email')
        password = data.get('password')

        if not all([first_name, last_name, phone_no, email, role, password]):
            msg = "All fields are required"
            current_app.logger.warning('Registration failed: %s', msg)
        elif not User.is_valid_email(email):
            msg = "Invalid email address"
            current_app.logger.warning('Registration failed: %s', msg)
        elif len(password) < 6:
            msg = "Password must be at least 6 characters long" 
            current_app.logger.warning('Password must be at least 6 characters long: %s', msg)   
        elif User.query.filter_by(email=email).first():
            msg = "Email already exists"
            current_app.logger.warning('Registration failed: %s', msg)
        elif User.query.filter_by(phone_no=phone_no).first():
            msg = "Phone number already exists"
            current_app.logger.warning('Registration failed: %s', msg)
        else:
            user = User(
                first_name=first_name,
                last_name=last_name,
                dob=dob,
                phone_no=phone_no,
                email=email,
                password=password
            )
            db.session.add(user)
            db.session.commit()
            msg = "Registration successful"
            flash("Registration successful", 'success')
            current_app.logger.info('User registered successfully: %s', email)
            return redirect(url_for('auth_bp.login'))
    return render_template("register.html", message=msg)

# Route for Login
@auth_bp.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        data = request.form
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            flash("Email and password are required", "error")
            msg = "Email and password are required"
            current_app.logger.warning('Login failed: %s', msg)

        user = User.query.filter_by(email=email).first()
        if not user or not user.verify_password(password):
            flash("Invalid email or password", "error")
            current_app.logger.warning('Login failed: Invalid email or password for email %s', email)
        else:
            session['loggedin'] = True
            session['id'] = user.id
            session['first_name'] = user.first_name
            session['email'] = user.email

            if email == "admin@nucleusteq.com":
                flash("Admin logged in successfully","success")
                current_app.logger.info('Admin logged in: %s', email)
                return redirect(url_for('auth_bp.admin_dashboard', user_id=session.get('id')))
            else:
                flash("Employee logged in successfully","success")
                current_app.logger.info('Employee logged in: %s', email)
                return redirect(url_for('auth_bp.employee_dashboard', user_id=session.get('id')))

    return render_template("login.html")

# Employee home page render when an employee gets logged in
@auth_bp.route('/employee_dashboard', methods=['GET'])
def employee_dashboard():
    if 'loggedin' in session:
        user_name = session['first_name']
        current_app.logger.info('Employee dashboard accessed by user: %s', user_name)
        return render_template('employee_dashboard.html', user_name=user_name)
    flash("You are not logged in", 'error')
    current_app.logger.warning('Unauthorized access attempt to employee dashboard')
    return redirect(url_for('auth_bp.login'))



# Employee assigned items list
@auth_bp.route('/assigned_item', methods=['GET'])
def assigned_item():
    if 'loggedin' in session:
        user_id = session['id']
        user = User.query.filter_by(id=user_id).first()
        if user:
            items = Item.query.filter_by(assigned_to_id=user.id).all()
            current_app.logger.info('Assigned items accessed by user: %s', user.email)
            return render_template('assigned_items.html', items=items, user=user)
        else:
            flash("User not found", "error")
            current_app.logger.warning('User not found: %s', user_id)
            return redirect(url_for('auth_bp.login'))

# Employee profile route
@auth_bp.route('/profile')
def profile():
    if 'loggedin' in session:
        user_id = session['id']
        user = User.query.filter_by(id=user_id).first()
        if user:
            user_details = {
                'id': user.id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'dob': user.dob,
                'email': user.email,
                'mobile': user.phone_no
            }
            current_app.logger.info('Profile accessed by user: %s', user.email)
            return render_template('profile.html', user_id=user_id, user=user_details)
        else:
            flash("User not found", "error")
            current_app.logger.warning('User not found: %s', user_id)
            return redirect(url_for('auth_bp.login'))

    flash("You are not logged in", 'error')
    current_app.logger.warning('Unauthorized access attempt to profile')
    return redirect(url_for('auth_bp.login'))

# Admin Routes
@auth_bp.route('/admin_dashboard', methods=['GET'])
def admin_dashboard():
    if 'loggedin' in session and session['email'] == 'admin@nucleusteq.com':
        user_name = session['first_name']
        current_app.logger.info('Admin dashboard accessed by: %s', user_name)
        return render_template('admin_dashboard.html', user_name=user_name)
    flash('You are not admin', 'error')
    current_app.logger.warning('Unauthorized access attempt to admin dashboard')
    return redirect(url_for('auth_bp.login'))



# Admin profile route
@auth_bp.route('/admin_dashboard/admin_profile')
def admin_profile():
    if 'loggedin' in session and session['email'] == 'admin@nucleusteq.com':
        user_id = session['id']
        user = User.query.filter_by(id=user_id).first()
        if user:
            user_details = {
                'id': user.id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'dob': user.dob,
                'email': user.email,
                'mobile': user.phone_no
            }
            current_app.logger.info('Admin profile accessed by: %s', user.email)
            return render_template('admin_profile.html', user=user_details)

    flash("User not found", "error")
    current_app.logger.warning('Admin user not found: %s', id)
    return redirect(url_for('auth_bp.login'))

# Route to fetch all users and display them
@auth_bp.route('/admin_dashboard/all_users', methods=['GET'])
def all_users():
    if 'loggedin' in session and session['email'] == 'admin@nucleusteq.com':
        users = User.query.all()
        for user in users:
            user.items = Item.query.filter_by(assigned_to_id=user.id).all()
        current_app.logger.info('All users accessed by admin')
        return render_template('all_users.html', users=users)
    flash("You are not logged in", 'error')
    current_app.logger.warning('Unauthorized access attempt to all users')
    return redirect(url_for('auth_bp.login'))

# Route to add a user
@auth_bp.route('/add_user', methods=['POST'])
def add_user():
    if 'loggedin' in session and session['email'] == 'admin@nucleusteq.com':
        data = request.form
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        dob = data.get('dob')
        phone_no = data.get('phone_no')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'user')
        
        if dob==None:
            dob = datetime.now()
        # Additional validations
        if not all([first_name, last_name, phone_no, email, password, dob]):
            flash("All fields are required")
            current_app.logger.warning('Add user failed: Missing fields')
            # return redirect(url_for('auth_bp.all_users'))

        elif not User.is_valid_email(email):
            flash("Invalid email address")
            current_app.logger.warning('Add user failed: Invalid email %s', email)
            # return redirect(url_for('auth_bp.all_users'))

        elif User.query.filter_by(email=email).first():
            flash("Email already exists")
            current_app.logger.warning('Add user failed: Email already exists %s', email)
            return redirect(url_for('auth_bp.all_users'))

        elif User.query.filter_by(phone_no=phone_no).first():
            flash("Phone number already exists")
            current_app.logger.warning('Add user failed: Phone number already exists %s', phone_no)
            return redirect(url_for('auth_bp.all_users'))

        elif len(password) < 6:
            flash("Password must be at least 6 characters long")
            current_app.logger.warning('Add user failed: Password too short')
            return redirect(url_for('auth_bp.all_users'))

        elif len(phone_no) != 10 or not phone_no.isdigit():
            flash("Phone number must be a 10-digit number")
            current_app.logger.warning('Add user failed: Invalid phone number')
            return redirect(url_for('auth_bp.all_users'))
        else:
            try:
                dob = datetime.strptime(dob, '%Y-%m-%d')
                if dob > datetime.now():
                    flash('Date of purchase cannot be in the future', 'error')
                    return redirect(url_for('auth_bp.all_items'))
            except ValueError:
                flash("Invalid date format for Date of Birth")
                current_app.logger.warning('Add user failed: Invalid date format for DOB')
                return redirect(url_for('auth_bp.all_users'))

            user = User(
                first_name=first_name,
                last_name=last_name,
                dob=dob,
                phone_no=phone_no,
                email=email,
                password=password,
                role=role
            )
            user.password = password

            db.session.add(user)
            db.session.commit()

            flash("Employee added successfully")
            current_app.logger.info('User added successfully: %s', email)
            return redirect(url_for('auth_bp.all_users'))

    flash("You are not logged in", 'error')
    current_app.logger.warning('Unauthorized access attempt to add user')
    return redirect(url_for('auth_bp.login'))


# Route to delete a user
@auth_bp.route('/delete_user', methods=['DELETE'])
def delete_user():
    if 'loggedin' in session and session['email'] == 'admin@nucleusteq.com':
        data = request.get_json()
        user_id = data.get('id')
        user = User.query.get(user_id)

        if user:
            db.session.delete(user)
            db.session.commit()
            current_app.logger.info('User deleted successfully: %s', user.email)
            return jsonify({'success': True})
        else:
            current_app.logger.warning('Delete user failed: User not found ')
            return jsonify({'success': False, 'error': 'User not found'}), 404
    flash("You are not logged in", 'error')
    current_app.logger.warning('Unauthorized access attempt to delete user')
    return redirect(url_for('auth_bp.login'))

# Routes for items
# Route to fetch the details of items
@auth_bp.route('/admin_dashboard/all_items', methods=['GET'])
def all_items():
    if 'loggedin' in session:
        items = Item.query.all()
        employees = User.query.all()
        current_app.logger.info('All items accessed')
        return render_template('items.html', items=items, employees=employees)
    flash("You are not logged in", 'error')
    current_app.logger.warning('Unauthorized access attempt to all items')
    return redirect(url_for('auth_bp.login'))


# Route to add an item
@auth_bp.route('/admin_dashboard/add_item', methods=['POST'])
def add_item():
    if 'loggedin' in session:
        data = request.form
        name = data.get('name')
        serial_number = data.get('serial_number')
        bill_number = data.get('bill_number')
        date_of_purchase = data.get('date_of_purchase')
        warranty = data.get('warranty')
        assigned_to_id = data.get('assigned_to_id')
        
        # Check if date_of_purchase is not in the future
        try:
            purchase_date = datetime.strptime(date_of_purchase, '%Y-%m-%d')
            if purchase_date > datetime.now():
                flash('Date of purchase cannot be in the future', 'error')
                return redirect(url_for('auth_bp.all_items'))
        except ValueError:
            flash('Invalid date format', 'error')
            return redirect(url_for('auth_bp.all_items'))
        
        # Check if serial_number and bill_number are unique
        if Item.query.filter_by(serial_number=serial_number).first():
            flash('Serial number already exists', 'error')
            return redirect(url_for('auth_bp.all_items'))
        
        if Item.query.filter_by(bill_number=bill_number).first():
            flash('Bill number already exists', 'error')
            return redirect(url_for('auth_bp.all_items'))
        
        new_item = Item(
            name=name,
            serial_number=serial_number,
            bill_number=bill_number,
            date_of_purchase=date_of_purchase,
            warranty=warranty,
            assigned_to_id=assigned_to_id
        )
        db.session.add(new_item)
        db.session.commit()
        flash('Item Added Successfully', 'success')
        current_app.logger.info('Item added successfully: %s', name)
        return redirect(url_for('auth_bp.all_items'))
    flash("You are not logged in", 'error')
    current_app.logger.warning('Unauthorized access attempt to add item')
    return redirect(url_for('auth_bp.login'))

# Route to assign an item to user
@auth_bp.route('/admin_dashboard/assign_item', methods=['POST'])
def assign_item():
    if 'loggedin' in session:
        data = request.form
        item_id = data.get('item_id')
        assigned_to_id = data.get('assigned_to')
        item = Item.query.get(item_id)

        if item:
            if assigned_to_id:
                existing_item = Item.query.filter_by(assigned_to_id=assigned_to_id, name=item.name).first()
                if existing_item:
                    flash(f'User already has an item named {item.name}', 'error')
                    current_app.logger.warning('Assign item failed: User %s already has item %s', assigned_to_id, item.name)
                    return redirect(url_for('auth_bp.all_items'))

                item.assigned_to_id = assigned_to_id
                db.session.commit()
                flash('Item assigned successfully', 'success')
                current_app.logger.info('Item assigned successfully: %s to user %s', item.
                name, assigned_to_id)
        else:
            flash('Item not found', 'error')
            current_app.logger.warning('Assign item failed: Item not found %s', item_id)

        return redirect(url_for('auth_bp.all_items'))
    flash("You are not logged in", 'error') 
    current_app.logger.warning('Unauthorized access attempt to assign item')
    return redirect(url_for('auth_bp.login'))

@auth_bp.route('/admin_dashboard/unassign_item/<int:item_id>', methods=['POST', 'GET'])
def unassign_item(item_id):
    if 'loggedin' in session:
        item = Item.query.get(item_id)
        if item:
            item.assigned_to_id = None
            db.session.commit()
            flash('Item Unassigned successfully', 'success')
            current_app.logger.info('Item unassigned successfully: %s', item_id)
        else:
            flash('Item Not Found', 'error')
        return redirect(url_for('auth_bp.all_items'))
    flash("You are not logged in", 'error')
    current_app.logger.warning('Unauthorized access attempt to unassign item')
    return redirect(url_for('auth_bp.login'))

# Route to delete an item
@auth_bp.route('/delete_item', methods=['DELETE'])
def delete_item():
    if 'loggedin' in session:
        data = request.get_json()
        item_id = data.get('id')
        item = Item.query.get(item_id)
        if item:
            db.session.delete(item)
            db.session.commit()
            flash('Item Deleted Successfully', 'success')
            current_app.logger.info('Item deleted successfully: %s', item.name)
        else:
            flash('Item not found', 'error')
            current_app.logger.warning('Delete item failed: Item not found %s', item_id)
        return redirect(url_for('auth_bp.all_items'))
    flash("You are not logged in", 'error')
    current_app.logger.warning('Unauthorized access attempt to delete item')
    return redirect(url_for('auth_bp.login'))

# Route to update an item
@auth_bp.route('/edit_item', methods=['POST'])
def edit_item():
    if 'loggedin' in session:
        data = request.form
        item_id = data.get('item_id')
        item = Item.query.get(item_id)
        if item:
            item.name = data.get('name')
            item.serial_number = data.get('serial_number')
            item.bill_number = data.get('bill_number')
            item.date_of_purchase = data.get('date_of_purchase')
            item.warranty = data.get('warranty')
            db.session.commit()
            flash("Item updated successfully", "success")
            current_app.logger.info('Item updated successfully: %s', item.name)
        else:
            flash("Item not found", "error")
            current_app.logger.warning('Update item failed: Item not found %s', item_id)
        return redirect(url_for('auth_bp.all_items'))
    flash("You are not logged in", 'error')
    current_app.logger.warning('Unauthorized access attempt to update item')
    return redirect(url_for('auth_bp.login'))

# Log out route
@auth_bp.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('full_name', None)
    session.pop('email', None)
    session.pop('role', None)
    flash("You have been logged out.", "success")
    current_app.logger.info('User logged out')
    return redirect(url_for('auth_bp.login'))
