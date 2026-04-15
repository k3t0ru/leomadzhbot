from sqlalchemy.orm import Session
from models import Customer, Product, Order, OrderItem
from typing import List, Tuple

class StoreService:
    @staticmethod
    def place_order(session: Session, customer_id: int, items: List[Tuple[int, int]]):
        """
        Scenario 1: Places an order within a transaction.
        'items' is a list of (product_id, quantity) tuples.
        """
        try:
            # 1. Create a new order entry
            new_order = Order(customer_id=customer_id, total_amount=0.0)
            session.add(new_order)
            session.flush()  # To get the order_id

            total_amount = 0.0
            for product_id, quantity in items:
                # Get product to find price
                product = session.query(Product).filter(Product.product_id == product_id).first()
                if not product:
                    raise ValueError(f"Product with ID {product_id} not found")
                
                subtotal = product.price * quantity
                total_amount += subtotal

                # 2. Add order items
                order_item = OrderItem(
                    order_id=new_order.order_id,
                    product_id=product_id,
                    quantity=quantity,
                    subtotal=subtotal
                )
                session.add(order_item)

            # 3. Update total amount in Orders table
            new_order.total_amount = total_amount
            
            # Commit happens outside if we want to chain operations or inside if it's standalone.
            # Usually, session.commit() is called by the caller or using a context manager.
            return new_order
        except Exception as e:
            session.rollback()
            raise e

    @staticmethod
    def update_customer_email(session: Session, customer_id: int, new_email: str):
        """
        Scenario 2: Updates customer email within a transaction.
        """
        try:
            customer = session.query(Customer).filter(Customer.customer_id == customer_id).first()
            if not customer:
                raise ValueError(f"Customer with ID {customer_id} not found")
            
            customer.email = new_email
            return customer
        except Exception as e:
            session.rollback()
            raise e

    @staticmethod
    def add_product(session: Session, product_name: str, price: float):
        """
        Scenario 3: Adds a new product within a transaction.
        """
        try:
            new_product = Product(product_name=product_name, price=price)
            session.add(new_product)
            return new_product
        except Exception as e:
            session.rollback()
            raise e
