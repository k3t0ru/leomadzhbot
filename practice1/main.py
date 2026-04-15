import os
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Customer, Product, Order, OrderItem
from service import StoreService
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/store_db")

# Wait for DB to be ready
def get_engine():
    retries = 5
    while retries > 0:
        try:
            engine = create_engine(DATABASE_URL)
            engine.connect()
            return engine
        except Exception as e:
            print(f"Waiting for database... {e}")
            time.sleep(5)
            retries -= 1
    raise Exception("Could not connect to database")

def init_db(engine):
    Base.metadata.drop_all(engine) # Clear database for fresh run
    Base.metadata.create_all(engine)
    print("Database tables created.")

def seed_data(session):
    # Seed initial customer
    customer = Customer(first_name="Ivan", last_name="Ivanov", email="ivan@example.com")
    session.add(customer)
    
    # Seed initial products
    product1 = Product(product_name="Laptop", price=1200.0)
    product2 = Product(product_name="Mouse", price=25.0)
    product3 = Product(product_name="Keyboard", price=45.0)
    session.add_all([product1, product2, product3])
    
    session.commit()
    print("Initial data seeded.")
    return customer.customer_id, [p.product_id for p in [product1, product2, product3]]

def main():
    engine = get_engine()
    init_db(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Initial Seed
        customer_id, product_ids = seed_data(session)

        print("\n--- Running Scenarios ---")

        # Scenario 3: Add new product
        print("Scenario 3: Adding a new product...")
        new_product = StoreService.add_product(session, "Monitor", 300.0)
        session.commit()
        print(f"Product added: {new_product.product_name} with ID {new_product.product_id}")

        # Scenario 2: Update customer email
        print("\nScenario 2: Updating customer email...")
        updated_customer = StoreService.update_customer_email(session, customer_id, "ivan_new@example.com")
        session.commit()
        print(f"Customer {updated_customer.first_name} email updated to: {updated_customer.email}")

        # Scenario 1: Place an order
        print("\nScenario 1: Placing an order...")
        items = [(product_ids[0], 1), (product_ids[1], 2)] # 1 Laptop, 2 Mice
        order = StoreService.place_order(session, customer_id, items)
        session.commit()
        print(f"Order #{order.order_id} placed for customer {customer_id}.")
        print(f"Total Amount: ${order.total_amount}")
        
        # Verify order items
        order_items = session.query(OrderItem).filter(OrderItem.order_id == order.order_id).all()
        for item in order_items:
            product = session.query(Product).filter(Product.product_id == item.product_id).first()
            print(f" - Item: {product.product_name}, Qty: {item.quantity}, Subtotal: ${item.subtotal}")

        print("\nAll scenarios completed successfully!")

    except Exception as e:
        print(f"Error occurred: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    main()
