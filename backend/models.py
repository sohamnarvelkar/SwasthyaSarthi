class Medicine:
    def __init__(self, name, price, quantity):
        self.name = name
        self.price = price
        self.quantity = quantity

class Order:
    def __init__(self, order_id, customer, medicine_list):
        self.order_id = order_id
        self.customer = customer
        self.medicine_list = medicine_list

class Customer:
    def __init__(self, customer_id, name, contact):
        self.customer_id = customer_id
        self.name = name
        self.contact = contact

class AgentTrace:
    def __init__(self, agent_id, order_id, trace_info):
        self.agent_id = agent_id
        self.order_id = order_id
        self.trace_info = trace_info
