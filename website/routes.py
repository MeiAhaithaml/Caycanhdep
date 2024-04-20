from flask import Blueprint, render_template, flash, request, redirect, jsonify,send_from_directory
from intasend import APIService
from datetime import datetime
from .models import Product,Cart,db,Order,Favorite
from  flask_login import login_required,current_user

routes = Blueprint('routes',__name__)
API_PUBLISHABLE_KEY ='ISPubKey_test_40e07e2d-32e8-429c-a515-7e09afa2773e'
API_TOKEN = 'ISSecretKey_test_acd2bae2-7794-4629-a163-d2805327f46f'
@routes.route('/')
def home():
    items = Product.query.filter_by(flash_sale=True).all()
    items_sorted = sorted(items, key=lambda x: x.date_added, reverse=True)
    latest_items = items_sorted[:9]
    return render_template('home.html', items=latest_items, cart=Cart.query.filter_by(customer_link=current_user.id).all()
                           if current_user.is_authenticated else [])

@routes.route('/media/<path:filename>',methods=['GET','POST'])
def get_image(filename):
    return send_from_directory('../media', filename)

@routes.route('/<int:item_id>',methods=['GET'])
def product_detail(item_id):
    product = Product.query.get(item_id)
    return render_template('product_details.html', product=product)
@routes.route('/<tag>',methods=['GET'])
def products_by_tag(tag):
    items = Product.query.filter_by(tag=tag).all()
    return render_template('tag/tag.html', items=items)
@routes.route('add-to-cart/<int:item_id>',methods=['GET','POST'])
@login_required
def add_to_cart(item_id):
    item_to_add = Product.query.get(item_id)
    item_exists = Cart.query.filter_by(product_link=item_id, customer_link=current_user.id).first()
    if item_exists:
        try:
            item_exists.quantity = item_exists.quantity + 1
            db.session.commit()
            flash(f' Quantity of {item_exists.product.product_name} has been updated')
            return redirect(request.referrer)
        except Exception as e:
            print('Quantity not Updated', e)
            flash(f'Quantity of {item_exists.product.product_name} not updated')
            return redirect(request.referrer)

    new_cart_item = Cart()
    new_cart_item.quantity = 1
    new_cart_item.product_link = item_to_add.id
    new_cart_item.customer_link = current_user.id

    try:
        db.session.add(new_cart_item)
        db.session.commit()
        flash(f'{new_cart_item.product.product_name} added to cart')
    except Exception as e:
        print('Item not added to cart', e)
        flash(f'{new_cart_item.product.product_name} has not been added to cart')

    return redirect(request.referrer)

@routes.route('/cart',methods=['GET','POST'])
@login_required
def show_cart():
    cart = Cart.query.filter_by(customer_link=current_user.id).all()
    amount = 0
    for item in cart:
        amount += item.product.current_price * item.quantity

    return render_template('cart.html', cart=cart, amount=amount, total=amount+20000)

@routes.route('/pluscart',methods=['GET','POST'])
@login_required
def plus_cart():
    if request.method == 'GET':
        cart_id = request.args.get('cart_id')
        cart_item = Cart.query.get(cart_id)
        cart_item.quantity = cart_item.quantity + 1
        db.session.commit()

        cart = Cart.query.filter_by(customer_link=current_user.id).all()

        amount = 0

        for item in cart:
            amount += item.product.current_price * item.quantity

        data = {
            'quantity': cart_item.quantity,
            'amount': amount,
            'total': amount + 20000
        }

        return jsonify(data)


@routes.route('/minuscart', methods=['GET', 'POST'])
@login_required
def minus_cart():
    if request.method == 'GET':
        cart_id = request.args.get('cart_id')
        cart_item = Cart.query.get(cart_id)
        if cart_item.quantity > 1:
            cart_item.quantity = cart_item.quantity - 1
            db.session.commit()

        cart = Cart.query.filter_by(customer_link=current_user.id).all()

        amount = 0

        for item in cart:
            amount += item.product.current_price * item.quantity

        data = {
            'quantity': cart_item.quantity,
            'amount': amount,
            'total': amount +20000
        }

        return jsonify(data)


@routes.route('removecart',methods=['GET','POST'])
@login_required
def remove_cart():
    if request.method == 'GET':
        cart_id = request.args.get('cart_id')
        cart_item = Cart.query.get(cart_id)
        db.session.delete(cart_item)
        db.session.commit()

        cart = Cart.query.filter_by(customer_link=current_user.id).all()

        amount = 0

        for item in cart:
            amount += item.product.current_price * item.quantity

        data = {
            'quantity': cart_item.quantity,
            'amount': amount,
            'total': amount + 20000
        }

        return jsonify(data)

@routes.route('/place-order',methods=['GET','POST'])
@login_required
def place_order():
    customer_cart = Cart.query.filter_by(customer_link=current_user.id)
    if customer_cart:
        try:
            total = 0
            for item in customer_cart:
                total += item.product.current_price * item.quantity

            service = APIService(token=API_TOKEN, publishable_key=API_PUBLISHABLE_KEY, test=True)
            create_order_response = service.collect.mpesa_stk_push(phone_number=2540332477829, email=current_user.email,
                                                                   amount=total + 20000, narrative='Purchase of goods')

            for item in customer_cart:
                new_order = Order()
                new_order.quantity = item.quantity
                new_order.price = item.product.current_price
                new_order.status = create_order_response['invoice']['state'].capitalize()
                new_order.payment_id = create_order_response['id']

                new_order.product_link = item.product_link
                new_order.customer_link = item.customer_link

                db.session.add(new_order)

                product = Product.query.get(item.product_link)

                product.in_stock -= item.quantity

                db.session.delete(item)

                db.session.commit()

            flash('Order Placed Successfully')

            return redirect('/orders')
        except Exception as e:
            print(e)
            flash('Order not placed')
            return redirect('/')
    else:
        flash('Your cart is Empty')
        return redirect('/')

@routes.route('/orders',methods=['GET','POST'])
@login_required
def order():
    orders = Order.query.filter_by(customer_link=current_user.id).all()
    return render_template('orders.html', orders=orders)

@routes.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        search_query = request.form.get('search')
        items = Product.query.filter(Product.product_name.ilike(f'%{search_query}%')).all()
        return render_template('search.html', items=items, cart=Cart.query.filter_by(customer_link=current_user.id).all()
                           if current_user.is_authenticated else [])

    return render_template('search.html')



@routes.route('/add-to-favorite/<int:item_id>', methods=['GET', 'POST'])
@login_required
def add_to_favorite(item_id):
    favorite_item = Favorite.query.filter_by(product_link=item_id, customer_link=current_user.id).first()
    if favorite_item:
        flash('Product already exists in favorites!')
        return redirect('/')
    else:
        new_favorite_item = Favorite(customer_link=current_user.id, product_link=item_id)
        try:
            db.session.add(new_favorite_item)
            db.session.commit()
            flash('Product added to favorites successfully!')
        except Exception as e:
            print(e)
            flash('Error adding product to favorites!')
    return redirect(request.referrer)



@routes.route('/favorites')
@login_required
def show_favorites():
    favorite_items = Favorite.query.filter_by(customer_link=current_user.id).all()
    favorites = []
    for favorite in favorite_items:
        product = Product.query.get(favorite.product_link)
        if product:
            favorites.append(product)
    return render_template('favorites.html', favorites=favorites)


@routes.route('/remove-from-favorite/<int:item_id>', methods=['GET', 'POST'])
@login_required
def remove_from_favorite(item_id):
    favorite_item = Favorite.query.filter_by(product_link=item_id, customer_link=current_user.id).first()
    if favorite_item:
        try:
            db.session.delete(favorite_item)
            db.session.commit()
            flash('Product removed from favorites successfully!')
        except Exception as e:
            print(e)
            flash('Error removing product from favorites!')
    else:
        flash('Product not found in favorites!')
    return redirect(request.referrer)

@routes.route('/about_us')
def about_us():
    return render_template('about_us.html')

@routes.route('/contact_us')
def contact_us():
    return render_template('contact_us.html')