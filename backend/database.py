import pandas as pd

class ExcelStorage:
    def __init__(self):
        self.data = {}

    def load_from_excel(self, file_path):
        # Load Excel file into memory
        df = pd.read_excel(file_path)
        self.data = df.to_dict(orient='records')

    def save_to_excel(self, file_path):
        # Save the current in-memory data to an Excel file
        df = pd.DataFrame(self.data)
        df.to_excel(file_path, index=False)

    def get_data(self):
        # Retrieve the in-memory data
        return self.data

    def clear_data(self):
        # Clear the in-memory data
        self.data = {}