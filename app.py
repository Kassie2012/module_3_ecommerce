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

def check_database_connection():
    try:
        connection = db.engine.connect()
        print("Successfully connected to the database.")
        connection.close() 
    except Exception as e:
        print(f"Error connecting to the database: {e}")


#======================= MODELS =============================

class Customer(Base):
    __tablename__ = 'Customer'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(225), nullable=False)
    email: Mapped[str] = mapped_column(db.String(225))
    address: Mapped[str] = mapped_column(db.String(225))
    orders: Mapped[List["Orders"]] = db.relationship("orders", back_populates='customer')

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
    products: Mapped[List['Products']] = db.relationship("products", secondary=order_products, back_populates='orders')


class Products(Base):
    __tablename__ = 'products'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    product_name: Mapped[str] = mapped_column(db.String(225), nullable = False)
    price: Mapped[float] = mapped_column(db.Float, nullable = False)
    orders: Mapped[List['Orders']] = db.relationship("orders", secondary=order_products, back_populates='products')
    
with app.app_context():
    Base.metadata.create_all(db.engine)
    

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

@app.route("/customers", methods=["POST"]) # Create a new customer
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
    
@app.route("/customers", methods=["GET"]) # Get all customers
def get_customers():
    
    query = select(Customer)
    result = db.session.execute(query).scalars()
    customers = result.all()
    return customers_schema.jsonify(customers)

@app.route("/customers/<int:id>", methods=['GET']) # Get a single customer by ID
def get_customer(id):
    
    query = select(Customer).where(Customer.id == id)
    result = db.session.execute(query).scalars().first() 

    if result is None:
        return jsonify({"Error": "Customer not found"}), 404
    
    return customer_schema.jsonify(result)

##check put and delete for errors

@app.route('/customers/<int:customer_id>', methods=['PUT']) ##did i do it? lol Updates a customer
def update_customers(id):
    try:
        new_customer = customer_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    quary = select(Customer).where(Customer.id == id)
    update_customers = db.session.execute(quary).scalars().first()

    if not update_customers:
        return jsonify({'Error': 'ID not found'})

    for field, attribute in new_customer.items():
        setattr(update_customers, field, attribute)
        

    db.session.commit()
    return customer_schema.dumps(update_customers), 200

@app.route('/customers/<int:id>', methods=['DELETE']) # Deletes a customer
def delete_customers(id):
    delete_customers = db.session.get(Customer, id)
    if delete_customers is None:
        return jsonify({'Error': 'ID not found'}), 404
    db.session.delete(delete_customers)
    db.session.commit()
    return jsonify({'Success': 'Customer deleted'}), 200

#=================================== PRODUCTS ===================================

@app.route('/products', methods=['POST']) # Create a new product
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

@app.route("/products", methods=['GET']) # Get all products
def get_products():
    query = select(Products)
    result = db.session.execute(query).scalars() 
    products = result.all() 
    return products_schema.jsonify(products)

@app.route("/products/<int:id>", methods=['GET']) # Get a single product by ID
def get_product(id):
    
    query = select(Products).where(Products.id == id)
    result = db.session.execute(query).scalars().first() 

    if result is None:
        return jsonify({"Error": "Customer not found"}), 404
    
    return product_schema.jsonify(result)

##need to do a put and delete route for products

@app.route('/products/<int:customer_id>', methods=['PUT']) #Updates a customer
def update_products(id):
    try:
        new_product = product_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    quary = select(Products).where(Products.id == id)
    update_products = db.session.execute(quary).scalars().first()

    if not update_products:
        return jsonify({'Error': 'ID not found'})

    for field, attribute in new_product.items():
        setattr(update_products, field, attribute)

    db.session.commit()
    return product_schema(update_products), 200

@app.route('/products/<int:id>', methods=['DELETE']) # Deletes a product
def delete_products(id):
    delete_products = db.session.get(Products, id)
    if delete_products is None:
        return jsonify({'Error': 'ID not found'}), 404
    db.session.delete(delete_products)
    db.session.commit()
    return jsonify({'Success': 'Product deleted'}), 200

#=================================== ORDERS ===================================

#CREATE an ORDER
@app.route('/orders', methods=['POST'])
def add_order():
    try:
        order_data = order_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    customer = db.session.get(Customer, order_data['customer_id'])
    
    if customer:
        new_order = Orders(order_date=order_data['order_date'], customer_id = order_data['customer_id'])

        db.session.add(new_order)
        db.session.commit()

        return jsonify({"Message": "New Order Placed!",
                        "order": order_schema.dump(new_order)}), 201
    else:
        return jsonify({"message": "Invalid customer id"}), 400

#ADD ITEM TO ORDER
@app.route('/orders/<int:order_id>/add_product/<int:product_id>', methods=['PUT'])
def add_product(order_id, product_id):
    order = db.session.get(Orders, order_id)
    product = db.session.get(Products, product_id)

    if order and product: 
        if product not in order.products: 
            order.products.append(product) 
            db.session.commit() 
            return jsonify({"Message": "Successfully added item to order."}), 200
        else:
            return jsonify({"Message": "Item is already included in this order."}), 400
    else:
        return jsonify({"Message": "Invalid order id or product id."}), 400


if __name__ == '__main__':
    app.run(debug=True, port=5001)