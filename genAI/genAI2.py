import os
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QTextEdit, QPushButton, QLabel, QWidget
from transformers import pipeline
from sentence_transformers import SentenceTransformer, util
import torch
from pathlib import Path
import sys

# Step 1: Data Preprocessing (Load and Combine Excel Files)
def load_data(path_to_excel_files):
    data = []
    for file in Path(path_to_excel_files).glob("*.xlsx"):
        df = pd.read_excel(file)
        data.append(df)
    combined_data = pd.concat(data, ignore_index=True)
    return combined_data

# Function to dynamically get the path to the train folder (whether from .exe or source)
def get_train_data_path():
    # Determine the path to the 'train' folder based on the environment (whether running from .exe or source code)
    if getattr(sys, 'frozen', False):
        # If running from the packaged .exe, get the folder containing the .exe
        base_path = os.path.dirname(sys.executable)
    else:
        # If running from the source code, use the current working directory
        base_path = os.path.abspath(".")
    
    # Return the path to the 'train' folder
    return os.path.join(base_path, "train")

# Step 2: Pretrained AI Model (Load a Simple QA Model)
qa_pipeline = pipeline("question-answering", model="distilbert-base-uncased-distilled-squad")

# Step 3: Initialize Sentence Transformers for Embedding-based Search
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# Step 4: AI Query Function - Handle Question and Answer Logic
def generate_answer(query, combined_data):
    # Simple QA using pre-trained QA model
    try:
        answer = qa_pipeline(question=query, context=combined_data.to_string())
        return answer['answer']
    except Exception as e:
        return "Sorry, I couldn't find an answer to that."

# Optional: Use Semantic Search (Sentence Embedding-based Retrieval)
def semantic_search(query, combined_data, top_k=1):
    # Embedding the query and the combined data for semantic search
    query_embedding = embedding_model.encode([query], convert_to_tensor=True)
    data_embeddings = embedding_model.encode(combined_data.columns.tolist(), convert_to_tensor=True)

    # Cosine similarity between the query and data columns
    similarities = util.pytorch_cos_sim(query_embedding, data_embeddings)[0]
    top_results = torch.topk(similarities, k=top_k)

    top_answers = [combined_data.columns[i] for i in top_results[1]]
    return "Most relevant column: " + ", ".join(top_answers)

# Step 5: GUI Setup Using PyQt
class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.data = load_data(get_train_data_path())  # Use the dynamic path for the 'train' folder

    def initUI(self):
        self.setWindowTitle("Offline Generative AI GUI")
        layout = QVBoxLayout()

        self.question_input = QTextEdit()
        layout.addWidget(QLabel("Enter your question:"))
        layout.addWidget(self.question_input)

        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self.on_submit)
        layout.addWidget(self.submit_button)

        self.answer_display = QLabel("Answer will appear here.")
        layout.addWidget(self.answer_display)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def on_submit(self):
        question = self.question_input.toPlainText()
        if question.strip() == "":
            self.answer_display.setText("Please enter a question.")
            return

        # Query the AI Model
        answer = generate_answer(question, self.data)
        # You can also add semantic search here if needed
        # answer = semantic_search(question, self.data)

        self.answer_display.setText(answer)

# Step 6: Run the GUI
def run_app():
    app = QApplication([])
    window = MyApp()
    window.show()
    app.exec_()

# Main execution
if __name__ == "__main__":
    run_app()
