from datetime import datetime, timedelta
import logging
import unittest
from app import create_app, db
from models.users import User
from models.items import Item

class AuthTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Check if user already exists
        existing_user = User.query.filter_by(phone_no='1234567890').first()
        if existing_user:
            db.session.delete(existing_user)
            db.session.commit()

        # Create all tables
        db.create_all()

        # Configure a separate logger for the tests
        self.test_log_file = 'test_log.log'
        self.logger = logging.getLogger('test_logger')
        self.logger.setLevel(logging.INFO)
        file_handler = logging.FileHandler(self.test_log_file)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # Inject the logger into the app's current_app
        self.app.logger = self.logger

        # Add a test user and admin user
        self.user = User(
            first_name='Test',
            last_name='User',
            dob='1990-01-01',
            phone_no='1234567890',
            email='test@nucleusteq.com',
            password='password',
            role='user'
        )
        self.admin = User(
            first_name='Admin',
            last_name='User',
            dob='1980-01-01',
            phone_no='0987654321',
            email='admin@nucleusteq.com',
            password='adminpassword',
            role='admin'
        )
        

        # Create a test item
        self.item = Item(name='Laptop', serial_number='SN12345679', bill_number='BN12345679', date_of_purchase=datetime.strptime('2023-01-01', '%Y-%m-%d'), warranty='2 years', assigned_to_id=self.admin.id)
       
        db.session.add(self.user)
        db.session.add(self.admin)
        db.session.add(self.item)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

         # Clean up the logger
        handlers = self.logger.handlers[:]
        for handler in handlers:
            handler.close()
            self.logger.removeHandler(handler)

    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Home', response.data)

    def test_register_user(self):
        response = self.client.post('/register', data={
            'first-name': 'New',
            'last-name': 'User',
            'dob': '1992-02-02',
            'phone': '1111111111',
            'email': 'newuser@nucleusteq.com',
            'password': 'password123',
            'role': 'user'
        })
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertEqual(response.location,'/login')

    def test_register_missing_fields(self):
        data = {'first-name': 'John'}  # Missing other required fields
        response = self.client.post('/register', data=data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'All fields are required', response.data)

    def test_register_invalid_email(self):
        data = {
            'first-name': 'John',
            'last-name': 'Doe',
            'dob': '1990-01-01',
            'phone': '1234567895',
            'email': 'john@nucleus.com',  # Invalid email format
            'password': 'password',
            'role': 'user'
        }
        response = self.client.post('/register', data=data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid email address', response.data)  
   

    def test_register_existing_email(self):
        # Create a user with the same email as in the test data
        existing_user = User(
            first_name='John',
            last_name='Doe',
            dob='1990-01-01',
            phone_no='1234567521',
            email='john@nucleusteq.com',
            password='password'
        )
        db.session.add(existing_user)
        db.session.commit()

        data = {
            'first-name': 'Jahn',
            'last-name': 'Doe',
            'dob': '1990-01-01',
            'phone': '1234567890',
            'email': 'john@nucleusteq.com',  # Existing email
            'password': 'password',
            'role': 'user'
        }
        response = self.client.post('/register', data=data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Email already exists", response.data)  

    def test_register_short_password(self):
        data = {
            'first-name': 'Jony',
            'last-name': 'Deo',
            'dob': '1990-01-01',
            'phone': '1234598745',
            'email': 'jony@nucleusteq.com',
            'password': 'pass',  # Short password
            'role': 'user'
        }
        response = self.client.post('/register', data=data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Password must be at least 6 characters long", response.data)                     

#tests for login
    def test_login_user(self):
        response = self.client.post('/login', data={
            'email': 'test@nucleusteq.com',
            'password': 'password'
        })
        self.assertEqual(response.status_code, 302)  # Redirect to dashboard

    def test_login_failure_missing_credentials(self):
        data = {'email': '', 'password': ''}
        response = self.client.post('/login', data=data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Email and password are required', response.data)
    

    def test_login_failure_invalid_credentials(self):
        data = {'email': 'john@example.com', 'password': 'wrongpassword'}
        response = self.client.post('/login', data=data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid email or password', response.data)

    def test_login_admin(self):
        response = self.client.post('/login', data={
            'email': 'admin@nucleusteq.com',
            'password': 'adminpassword'
        })
        self.assertEqual(response.status_code, 302)  # Redirect to admin dashboard
        self.assertEqual(response.location,'/admin_dashboard?user_id=2')
        # self.assertEqual("Admin logged in successfully",response.data)

    def test_login_employee(self):
        response = self.client.post('/login', data={
            'email': 'test@nucleusteq.com',
            'password': 'password'
        })
        self.assertEqual(response.status_code, 302)  # Redirect to employee dashboard
        self.assertEqual(response.location,'/employee_dashboard?user_id=1')
        # self.assertEqual("Admin logged in successfully",response.data)    


    def test_employee_dashboard(self):
        with self.client.session_transaction() as sess:
            sess['loggedin'] = True
            sess['first_name'] = self.user.first_name 
            sess['id'] = self.user.id
            sess['email'] = self.user.email
        response = self.client.get('/employee_dashboard')
        self.assertEqual(response.status_code, 200)

        

    def test_employee_dashboard_unauthorized_access(self):
        response = self.client.get('/employee_dashboard', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'You are not logged in', response.data)
        self.assertNotIn(b'Employee Dashboard', response.data)


    def test_profile_logged_in(self):
        with self.client.session_transaction() as sess:
            sess['loggedin'] = True
            sess['id'] = self.user.id

        response = self.client.get('/profile')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Profile', response.data)
        self.assertIn(b'Test', response.data)
        self.assertIn(b'User', response.data)
        self.assertIn(b'1990-01-01', response.data)
        self.assertIn(b'test@nucleusteq.com', response.data)
        self.assertIn(b'1234567890', response.data)   

    def test_profile_user_not_found(self):
        with self.client.session_transaction() as sess:
            sess['loggedin'] = True
            sess['id'] = 999  # User ID not in database

        response = self.client.get('/profile', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'User not found', response.data)

    def test_profile_not_logged_in(self):
        response = self.client.get('/profile', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'You are not logged in', response.data)             
     
## test for admin routes
    def test_admin_dashboard(self):
        with self.client.session_transaction() as sess:
            sess['first_name'] = self.admin.first_name 
            sess['loggedin'] = True
            sess['id'] = self.admin.id
            sess['email'] = self.admin.email
        response = self.client.get('/admin_dashboard')
        self.assertEqual(response.status_code, 200)



    def test_admin_dashboard_non_admin_access(self):
        with self.client.session_transaction() as sess:
            sess['loggedin'] = True
            sess['email'] = 'john@nucleusteq.com'  # Non-admin user
            sess['first_name'] = 'John'
        response = self.client.get('/admin_dashboard', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'You are not admin', response.data)
        self.assertNotIn(b'Admin Dashboard', response.data)   


    def test_admin_dashboard_unauthorized_access(self):
        response = self.client.get('/admin_dashboard', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        # self.assertIn(b'You are not logged in', response.data)
        self.assertNotIn(b'Admin Dashboard', response.data) 

# admin profile test
    def test_admin_profile_logged_in(self):
        with self.client.session_transaction() as sess:
            sess['loggedin'] = True
            sess['id'] = self.admin.id
            sess['email'] = self.admin.email

        response = self.client.get('/admin_dashboard/admin_profile')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Profile', response.data)
        self.assertIn(b'Admin', response.data)
        self.assertIn(b'User', response.data)
        self.assertIn(b'1980-01-01', response.data)
        self.assertIn(b'admin@nucleusteq.com', response.data)
        
        

    def test_admin_profile_not_found(self):
        with self.client.session_transaction() as sess:
            sess['loggedin'] = True
            sess['id'] = 999  # Admin ID not in database
            sess['email'] = 'admin@nucleusteq.com'

        response = self.client.get('/admin_dashboard/admin_profile', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'User not found', response.data)

    def test_admin_profile_not_logged_in(self):
        response = self.client.get('/admin_dashboard/admin_profile', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'User not found', response.data)                    

# tests for all_user route
    def test_all_users_logged_in(self):
        with self.client.session_transaction() as sess:
            sess['loggedin'] = True
            sess['id'] = self.admin.id
            sess['email'] = self.admin.email

        response = self.client.get('/admin_dashboard/all_users')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'All Users', response.data)
        self.assertIn(b'Admin', response.data)
        self.assertIn(b'User', response.data)
   

    def test_all_users_not_logged_in(self):
        response = self.client.get('/admin_dashboard/all_users', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'You are not logged in', response.data)


#add user
    def test_successful_user_addition(self):
        # Simulate admin login
        with self.client.session_transaction() as session:
            session['loggedin'] = True
            session['email'] = 'admin@nucleusteq.com'

        # Provide valid user data
        user_data = {
            'first_name': 'test2',
            'last_name': 'user',
            'dob': '1990-01-01',
            'phone_no': '9981474746',
            'email': 'john@nucleusteq.com',
            'password': 'password123'
        }

        # Send POST request to add user
        response = self.client.post('/add_user', data=user_data, follow_redirects=True)

        # Check if user is added successfully
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Employee added successfully', response.data)
 

    def test_add_user_not_logged_in(self):
        response = self.client.post('/add_user', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'You are not logged in', response.data)

    def test_add_user_incomplete_data(self):
        with self.client.session_transaction() as sess:
            sess['loggedin'] = True
            sess['email'] = self.admin.email

        data = {
            'first_name': 'Test',
            'last_name': 'User',
            'phone_no': '9876543210',
            'email': 'test@example.com',
            'password': 'test_password',
        }
        response = self.client.post('/add_user', data=data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        

#delete user
    def test_successful_user_deletion(self):
        with self.client.session_transaction() as sess:
            sess['loggedin'] = True
            sess['email'] = self.admin.email

        # Create a user to delete
        user = User(first_name='test3', last_name='user',phone_no = "9981365266", email='test3@nucleusteq.com', password='password123')
        db.session.add(user)
        db.session.commit()

        # Delete the user
        response = self.client.delete('/delete_user', json={'id': user.id}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
           

     
        

    def test_unauthorized_access(self):
        # Attempt to delete a user without being logged in as admin
        response = self.client.delete('/delete_user', json={'id': 1}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)  # Redirect to login
        self.assertIn(b'You are not logged in', response.data)

#add item
    def test_successful_item_addition(self):
        with self.client.session_transaction() as sess:
            sess['loggedin'] = True
            sess['email'] = self.admin.email
        response = self.client.post('/admin_dashboard/add_item', data={
            'name': 'Laptop',
            'serial_number': 'SN12345678',
            'bill_number': 'BN12345678',
            'date_of_purchase': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
            'warranty': '2 years',
            'assigned_to_id': self.admin.id
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Item Added Successfully', response.data)

    def test_unauthorized_access(self):
        response = self.client.post('/admin_dashboard/add_item', data={
            'name': 'Laptop',
            'serial_number': 'SN12345678',
            'bill_number': 'BN12345678',
            'date_of_purchase': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
            'warranty': '2 years',
            'assigned_to_id': self.admin.id
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'You are not logged in', response.data)

    def test_invalid_date_format(self):
        with self.client.session_transaction() as sess:
            sess['loggedin'] = True
            sess['email'] = self.admin.email
        response = self.client.post('/admin_dashboard/add_item', data={
            'name': 'Laptop',
            'serial_number': 'SN12345678',
            'bill_number': 'BN12345678',
            'date_of_purchase': 'invalid-date',
            'warranty': '2 years',
            'assigned_to_id': self.admin.id
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid date format', response.data)

    def test_future_date_of_purchase(self):
        with self.client.session_transaction() as sess:
            sess['loggedin'] = True
            sess['email'] = self.admin.email
        response = self.client.post('/admin_dashboard/add_item', data={
            'name': 'Laptop',
            'serial_number': 'SN12345678',
            'bill_number': 'BN12345678',
            'date_of_purchase': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            'warranty': '2 years',
            'assigned_to_id': self.admin.id
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Date of purchase cannot be in the future', response.data)

    def test_duplicate_serial_number(self):
        with self.client.session_transaction() as sess:
            sess['loggedin'] = True
            sess['email'] = self.admin.email
        item = Item(name='Laptop', serial_number='SN12345678', bill_number='BN12345678', date_of_purchase=(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'), warranty='2 years', assigned_to_id=self.admin.id)
        db.session.add(item)
        db.session.commit()

        response = self.client.post('/admin_dashboard/add_item', data={
            'name': 'Monitor',
            'serial_number': 'SN12345678',
            'bill_number': 'BN87654321',
            'date_of_purchase': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
            'warranty': '1 year',
            'assigned_to_id': self.admin.id
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Serial number already exists', response.data)

    def test_duplicate_bill_number(self):
        with self.client.session_transaction() as sess:
            sess['loggedin'] = True
            sess['email'] = self.admin.email
        item = Item(name='Laptop', serial_number='SN12345678', bill_number='BN12345678', date_of_purchase=(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'), warranty='2 years', assigned_to_id=self.admin.id)
        db.session.add(item)
        db.session.commit()

        response = self.client.post('/admin_dashboard/add_item', data={
            'name': 'Monitor',
            'serial_number': 'SN87654321',
            'bill_number': 'BN12345678',
            'date_of_purchase': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
            'warranty': '1 year',
            'assigned_to_id': self.admin.id
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Bill number already exists', response.data)

    
# all item route
    def test_successful_access_all_items(self):
        with self.client.session_transaction() as sess:
            sess['loggedin'] = True
            sess['email'] = self.admin.email
        response = self.client.get('/admin_dashboard/all_items')
        self.assertEqual(response.status_code, 200)

        

    def test_unauthorized_access_all_items(self):
        response = self.client.get('/admin_dashboard/all_items', follow_redirects=True)
        self.assertEqual(response.status_code, 200)  # because of redirect
        self.assertIn(b'You are not logged in', response.data)
        self.assertIn(b'Login', response.data)
        



#assign item to user
    def test_assign_item(self):
        # Create a test item
        item = Item(
            name='Test Item',
            serial_number='SN123',
            bill_number='BN123',
            date_of_purchase='2023-01-01',
            warranty='2 years',
            assigned_to_id=self.user.id
        )
        db.session.add(item)
        db.session.commit()

        with self.client.session_transaction() as sess:
            sess['loggedin'] = True
            sess['id'] = self.admin.id
            sess['email'] = self.admin.email
        
        response = self.client.post('/admin_dashboard/assign_item', data={
            'item_id': item.id,
            'assigned_to': self.user.id
        })
        self.assertEqual(response.status_code, 302)  # Redirect to items
        self.assertEqual(Item.query.filter_by(assigned_to_id=self.user.id).count(), 1)


#unassign item 
    def test_successful_item_unassignment(self):
        with self.client.session_transaction() as sess:
            sess['loggedin'] = True
            sess['email'] = self.admin.email
        response = self.client.post(f'/admin_dashboard/unassign_item/{self.item.id}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Item Unassigned successfully', response.data)

        # Check if the item is unassigned
        item = Item.query.get(self.item.id)
        self.assertIsNone(item.assigned_to_id)

# delete an item
    def test_delete_item(self):
        # Create a test item
        item = Item(
            name='Test Item',
            serial_number='SN123',
            bill_number='BN123',
            date_of_purchase='2023-01-01',
            warranty='2 years'
        )
        db.session.add(item)
        db.session.commit()

        with self.client.session_transaction() as sess:
            sess['loggedin'] = True
            sess['id'] = self.admin.id
            sess['email'] = self.admin.email
        
        response = self.client.delete('/delete_item', json={'id': item.id})
        self.assertEqual(response.status_code, 302)  # Redirect to items
        self.assertEqual(Item.query.filter_by(id=item.id).count(), 0)

if __name__ == '__main__':
    unittest.main()
