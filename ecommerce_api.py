from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from flask_marshmallow import Marshmallow
from datetime import datetime
from typing import List
from marshmallow import ValidationError
from sqlalchemy import select

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:K!ng20!2@localhost/ecommerce_api'
app.config['SQLALCHEMY_ECHO'] = True

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(app, model_class=Base)
ma = Marshmallow(app)

order_products = db.Table(
    "Order_Products",
    Base.metadata,
    db.Column('order_id', db.ForeignKey('orders.id')),
    db.Column('product_id', db.ForeignKey('products.id')),
)

# ======================= MODELS =============================

class Customer(Base):
    __tablename__ = 'Customer'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(225), nullable=False)
    email: Mapped[str] = mapped_column(db.String(225))
    address: Mapped[str] = mapped_column(db.String(225))
    orders: Mapped[List["Orders"]] = db.relationship("Orders", back_populates='customer')


class Orders(Base):
    __tablename__ = 'orders'

    id: Mapped[int] = mapped_column(primary_key=True)
    order_date: Mapped[datetime] = mapped_column(db.DateTime, nullable=False)
    customer_id: Mapped[int] = mapped_column(db.ForeignKey('Customer.id'))
    customer: Mapped["Customer"] = db.relationship("Customer", back_populates='orders')
    products: Mapped[List["Products"]] = db.relationship("Products", secondary=order_products, back_populates='orders')


class Products(Base):
    __tablename__ = 'products'

    id: Mapped[int] = mapped_column(primary_key=True)
    product_name: Mapped[str] = mapped_column(db.String(225), nullable=False)
    price: Mapped[float] = mapped_column(db.Float, nullable=False)
    orders: Mapped[List["Orders"]] = db.relationship("Orders", secondary=order_products, back_populates='products')

with app.app_context():
    db.create_all()

# ======================= SCHEMAS =============================

class CustomerSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Customer

class ProductSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Products

class OrderSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Orders
        include_fk = True

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)
order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)

# ======================= ROUTES =============================

@app.route('/')
def home():
    return jsonify({'message': 'Ecommerce API is live! 🚀'})

# ======================= CUSTOMER ROUTES =============================

@app.route("/customers", methods=["POST"])
def add_customer():
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    new_customer = Customer(**customer_data)
    db.session.add(new_customer)
    db.session.commit()

    return jsonify({"Message": "New Customer added successfully", "customer": customer_schema.dump(new_customer)}), 201

@app.route("/customers", methods=["GET"])
def get_customers():
    customers = db.session.execute(select(Customer)).scalars().all()
    return customers_schema.jsonify(customers)

@app.route("/customers/<int:id>", methods=['GET'])
def get_customer(id):
    customer = db.session.get(Customer, id)
    if not customer:
        return jsonify({"Error": "Customer not found"}), 404
    return customer_schema.jsonify(customer)

@app.route('/customers/<int:customer_id>', methods=['PUT'])
def update_customers(customer_id):
    customer = db.session.get(Customer, customer_id)
    if not customer:
        return jsonify({'Error': 'ID not found'}), 404

    for key, value in request.json.items():
        setattr(customer, key, value)

    db.session.commit()
    return customer_schema.jsonify(customer), 200

@app.route('/customers/<int:id>', methods=['DELETE'])
def delete_customers(id):
    customer = db.session.get(Customer, id)
    if not customer:
        return jsonify({'Error': 'ID not found'}), 404
    db.session.delete(customer)
    db.session.commit()
    return jsonify({'Success': 'Customer deleted'}), 200

# ======================= PRODUCT ROUTES =============================

@app.route('/products', methods=['POST'])
def create_product():
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    new_product = Products(**product_data)
    db.session.add(new_product)
    db.session.commit()

    return jsonify({"Message": "New Product added!", "product": product_schema.dump(new_product)}), 201

@app.route("/products", methods=['GET'])
def get_products():
    products = db.session.execute(select(Products)).scalars().all()
    return products_schema.jsonify(products)

@app.route("/products/<int:id>", methods=['GET'])
def get_product(id):
    product = db.session.get(Products, id)
    if not product:
        return jsonify({"Error": "Product not found"}), 404
    return product_schema.jsonify(product)

@app.route('/products/<int:id>', methods=['PUT'])
def update_products(id):
    product = db.session.get(Products, id)
    if not product:
        return jsonify({'Error': 'ID not found'}), 404

    for key, value in request.json.items():
        setattr(product, key, value)

    db.session.commit()
    return product_schema.jsonify(product), 200

@app.route('/products/<int:id>', methods=['DELETE'])
def delete_products(id):
    product = db.session.get(Products, id)
    if not product:
        return jsonify({'Error': 'ID not found'}), 404
    db.session.delete(product)
    db.session.commit()
    return jsonify({'Success': 'Product deleted'}), 200

# ======================= ORDER ROUTES =============================

@app.route('/orders', methods=['POST'])
def add_order():
    try:
        order_data = order_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    customer = db.session.get(Customer, order_data['customer_id'])
    if not customer:
        return jsonify({"message": "Invalid customer id"}), 400

    new_order = Orders(order_date=order_data['order_date'], customer_id=order_data['customer_id'])
    db.session.add(new_order)
    db.session.commit()

    return jsonify({"Message": "New Order Placed!", "order": order_schema.dump(new_order)}), 201

@app.route('/orders/<int:order_id>/add_product/<int:product_id>', methods=['PUT'])
def add_product(order_id, product_id):
    order = db.session.get(Orders, order_id)
    product = db.session.get(Products, product_id)

    if not order or not product:
        return jsonify({"Message": "Invalid order id or product id."}), 400

    if product not in order.products:
        order.products.append(product)
        db.session.commit()
        return jsonify({"Message": "Successfully added item to order."}), 200

    return jsonify({"Message": "Item is already included in this order."}), 400

@app.route('/orders/<int:order_id>/remove_product/<int:product_id>', methods=['DELETE'])
def remove_product_from_order(order_id, product_id):
    order = db.session.get(Orders, order_id)
    product = db.session.get(Products, product_id)

    if not order or not product:
        return jsonify({"Message": "Invalid order id or product id."}), 400

    if product in order.products:
        order.products.remove(product)
        db.session.commit()
        return jsonify({"Message": "Product removed from order."}), 200

    return jsonify({"Message": "Product not found in order."}), 404

@app.route('/orders/user/<int:user_id>', methods=['GET'])
def get_orders_by_user(user_id):
    user = db.session.get(Customer, user_id)
    if not user:
        return jsonify({"Message": "User not found."}), 404

    return orders_schema.jsonify(user.orders)

@app.route('/orders/<int:order_id>/products', methods=['GET'])
def get_products_by_order(order_id):
    order = db.session.get(Orders, order_id)
    if not order:
        return jsonify({"Message": "Order not found."}), 404

    return products_schema.jsonify(order.products)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
