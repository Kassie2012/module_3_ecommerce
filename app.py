from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from flask_marshmallow import Marshmallow
from datetime import date
from typing import List
from marshmallow import ValidationError, fields
from sqlalchemy import select, delete

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://<root>:<K!ng20!2>@localhost/ecommerce_api'

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(app, model_class=Base)
ma = Marshmallow(app)

#======================= MODELS =============================

class Customer(Base):
    __tablename__ = 'Customer'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(225), nullable=False)
    email: Mapped[str] = mapped_column(db.String(225))
    address: Mapped[str] = mapped_column(db.String(225))
    orders: Mapped[List["Orders"]] = db.relationship(back_populates='customer')

order_products = db.Table(
    "Order_Products",
    Base.metadata,
    db.Column('order_id', db.ForeignKey('orders.id')),
    db.Column('product_id', db.ForeignKey('products.id')),
)

class Orders(Base):
    __tablename__ = 'orders'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    order_date: Mapped[date] = mapped_column(db.Date, nullable = False)
    customer_id: Mapped[int] = mapped_column(db.ForeignKey('Customer.id'))
    customer: Mapped['Customer'] = db.relationship(back_populates='orders')
    products: Mapped[List['Products']] = db.relationship(secondary=order_products, back_populates='orders')


class Products(Base):
    __tablename__ = 'products'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    product_name: Mapped[str] = mapped_column(db.String(225), nullable = False)
    price: Mapped[float] = mapped_column(db.Float, nullable = False)
    orders: Mapped[List['Orders']] = db.relationship(secondary=order_products, back_populates='products')
    
with app.app_context():
    db.create_all()
    

#================================= SSCHEMAS =====================================

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

#=================================== ROUTES ===================================

@app.route("/customers", methods=["POST"])
def add_customer():
    
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    new_customer = Customer(name=customer_data['name'], email=customer_data['email'], address=customer_data['address'])
    db.session.add(new_customer)
    db.session.commit()
    
    return jsonify({"Message": "New Customer was added to the DB successfully",
                    "customer": customer_schema.dump(new_customer)}), 201
    
@app.route("/customers", methods=["GET"])
def get_customers():
    
    query = select(Customer)
    result = db.session.execute(query).scalars()
    customers = result.all()
    return customers_schema.jsonify(customers)

@app.route("/customers/<int:id>", methods=['GET'])
def get_customer(id):
    
    query = select(Customer).where(Customer.id == id)
    result = db.session.execute(query).scalars().first() 

    if result is None:
        return jsonify({"Error": "Customer not found"}), 404
    
    return customer_schema.jsonify(result)

##need to do a put and delete route for customers

#=================================== PRODUCTS ===================================

@app.route('/products', methods=['POST'])
def create_product():
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    new_product = Products(product_name=product_data['product_name'], price=product_data['price'])
    db.session.add(new_product)
    db.session.commit()

    return jsonify({"Messages": "New Product added!",
                    "product": product_schema.dump(new_product)}), 201

@app.route("/products", methods=['GET'])
def get_products():
    query = select(Products)
    result = db.session.execute(query).scalars() 
    products = result.all() 
    return products_schema.jsonify(products)
if __name__ == '__main__':
    app.run(debug=True, port=5001)