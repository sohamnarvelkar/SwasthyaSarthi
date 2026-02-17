import json

class ConversationalAgent:
    def __init__(self):
        self.order_data = {}

    def process_order(self, user_input):
        # Sample logic for NLP processing of medicine orders
        # This function should take user input and extract medicine order details
        self.order_data = self.extract_order_details(user_input)
        return self.order_data

    def extract_order_details(self, user_input):
        # Placeholder for extracting order details
        # In a real scenario, NLP techniques will be applied here
        return json.loads(user_input) if self.is_valid_order(user_input) else {}

    def is_valid_order(self, user_input):
        # Validate the user input for order details
        return True  # Placeholder validation