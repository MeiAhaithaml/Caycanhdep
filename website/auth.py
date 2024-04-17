from flask import Blueprint, render_template, redirect, flash
from .forms import LoginForm, SignUpForm,PasswordChangeForm
from .models import Customer
from .models import db
from flask_login import login_user, login_required, logout_user

auth = Blueprint('auth', __name__)


@auth.route('/sign-up', methods=['GET', 'POST'])
def login():
    form = SignUpForm()
    if form.validate_on_submit():
        email = form.email.data
        username = form.username.data
        password1 = form.password1.data
        password2 = form.password2.data

        if password1 == password2:
            new_customer = Customer()
            new_customer.email = email
            new_customer.username = username
            new_customer.password = password2

            try:
                db.session.add(new_customer)
                db.session.commit()
                flash('Account Createf Successfully,You can now Login')
                return redirect('/login')
            except Exception as e:
                print(e)
                flash('Account Noot Created!!,Email already ')
            form.email.data = ''
            form.username.data = ''
            form.password1.data = ''
            form.password2.data = ''

    return render_template('signup.html', form=form)


@auth.route('/login', methods=['GET', 'POST'])
def sign_up():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        customer = Customer.query.filter_by(email=email).first()
        if customer:
            if customer.verify_password(password=password):
                login_user(customer)
                return redirect('/')
            else:
                flash('Incorrect Email or Password')
        else:
            flash('Vui long dang ky tai khoan')

    return render_template('login.html', form=form)

@auth.route('/logout',methods=['GET','POST'])
def log_out():
    logout_user()
    return redirect('/')

@auth.route('/profile/<int:customer_id>')
@login_required
def profile(customer_id):
    customer = Customer.query.get(customer_id)
    print('Customer ID:',customer_id)
    return render_template('profile.html',customer=customer)
@auth.route('/change-password/<int:customer_id>',methods=['GET','POST'])
@login_required
def change_password(customer_id):
    form = PasswordChangeForm()
    customer =Customer.query.get(customer_id)
    if form.validate_on_submit():
        current_password =form.current_password.data
        new_password =form.new_password.data
        confirm_new_password = form.confirm_new_password.data

        if customer.verify_password(current_password):
            if new_password == confirm_new_password:
                customer.password = confirm_new_password
                db.session.commit()
                flash(" Thay doi mat khau thanh cong")
                return  redirect(f'/profile/{customer.id}')
            else:
                flash('Mat khau khong khop')
        else:
            flash('Current Password is Incorrect')
    return render_template('change_password.html',form=form)
