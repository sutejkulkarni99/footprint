import sys
import pandas as pd
import torch
import optuna
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QFileDialog, QLabel, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt
from transformers import TableTransformerForObjectDetection, TrainingArguments, Trainer, TableTransformerTokenizer
from datasets import Dataset, load_metric
from sklearn.model_selection import KFold

class ConnectorTrainer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cable Connector Trainer")
        self.setGeometry(100, 100, 1200, 800)
        
        # Data storage
        self.df_combined = pd.DataFrame()
        self.model = None
        self.tokenizer = TableTransformerTokenizer.from_pretrained('microsoft/table-transformer-detection')
        
        # Initialize GUI
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # File selection controls
        file_controls_layout = QHBoxLayout()
        self.load_files_button = QPushButton("Load Excel Files")
        self.load_files_button.clicked.connect(self.load_files)
        file_controls_layout.addWidget(self.load_files_button)
        
        self.train_button = QPushButton("Train Model")
        self.train_button.clicked.connect(self.train_model)
        file_controls_layout.addWidget(self.train_button)
        
        self.predict_button = QPushButton("Predict Connections")
        self.predict_button.clicked.connect(self.predict_connections)
        file_controls_layout.addWidget(self.predict_button)
        
        layout.addLayout(file_controls_layout)
        
        # Table widget to show combined data
        self.table = QTableWidget()
        layout.addWidget(self.table)
        
        # Status bar
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
    
    def load_files(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Open Excel Files", "", "Excel Files (*.xlsx)")
        if file_paths:
            self.df_combined = pd.DataFrame()
            for file in file_paths:
                df = pd.read_excel(file)
                self.df_combined = pd.concat([self.df_combined, df], ignore_index=True)
            self.draw_spreadsheet()
            self.status_label.setText(f"Loaded {len(file_paths)} files")
    
    def draw_spreadsheet(self):
        if self.df_combined.empty:
            return
        
        self.table.setRowCount(len(self.df_combined))
        self.table.setColumnCount(len(self.df_combined.columns))
        self.table.setHorizontalHeaderLabels(self.df_combined.columns)
        
        for row_idx in range(len(self.df_combined)):
            for col_idx in range(len(self.df_combined.columns)):
                cell_value = str(self.df_combined.iat[row_idx, col_idx])
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(cell_value))
        
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
    
    def train_model(self):
        if self.df_combined.empty:
            QMessageBox.warning(self, "No Data", "Please load the Excel files first!")
            return
        
        dataset = Dataset.from_pandas(self.df_combined)
        metric = load_metric("accuracy")

        def compute_metrics(p):
            return metric.compute(predictions=p.predictions, references=p.label_ids)

        def model_init():
            return TableTransformerForObjectDetection.from_pretrained('microsoft/table-transformer-detection')

        def objective(trial):
            training_args = TrainingArguments(
                output_dir='./results',
                num_train_epochs=trial.suggest_int('num_train_epochs', 2, 10),
                per_device_train_batch_size=trial.suggest_categorical('per_device_train_batch_size', [2, 4, 8]),
                per_device_eval_batch_size=trial.suggest_categorical('per_device_eval_batch_size', [2, 4, 8]),
                warmup_steps=trial.suggest_int('warmup_steps', 100, 500),
                weight_decay=trial.suggest_float('weight_decay', 0.01, 0.1),
                logging_dir='./logs',
            )

            kf = KFold(n_splits=5)
            accuracy_scores = []

            for train_index, val_index in kf.split(dataset):
                train_dataset = dataset.select(train_index)
                val_dataset = dataset.select(val_index)
                
                trainer = Trainer(
                    model_init=model_init,
                    args=training_args,
                    train_dataset=train_dataset,
                    eval_dataset=val_dataset,
                    compute_metrics=compute_metrics,
                )
                
                trainer.train()
                eval_result = trainer.evaluate()
                accuracy_scores.append(eval_result['eval_accuracy'])
            
            return sum(accuracy_scores) / len(accuracy_scores)

        study = optuna.create_study(direction='maximize')
        study.optimize(objective, n_trials=20)

        best_hyperparameters = study.best_params
        self.status_label.setText(f"Best hyperparameters: {best_hyperparameters}")

        training_args = TrainingArguments(
            output_dir='./results',
            num_train_epochs=best_hyperparameters['num_train_epochs'],
            per_device_train_batch_size=best_hyperparameters['per_device_train_batch_size'],
            per_device_eval_batch_size=best_hyperparameters['per_device_eval_batch_size'],
            warmup_steps=best_hyperparameters['warmup_steps'],
            weight_decay=best_hyperparameters['weight_decay'],
            logging_dir='./logs',
        )

        trainer = Trainer(
            model=model_init(),
            args=training_args,
            train_dataset=dataset,
            eval_dataset=dataset,
            compute_metrics=compute_metrics,
        )

        trainer.train()
        self.model = trainer.model
        self.model.save_pretrained('./fine_tuned_model')
        self.status_label.setText("Model training complete and saved.")
    
    def predict_connections(self):
        if not self.model:
            self.model = TableTransformerForObjectDetection.from_pretrained('./fine_tuned_model')
        
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Excel File", "", "Excel Files (*.xlsx)")
        if file_path:
            df = pd.read_excel(file_path)
            inputs = self.tokenizer(df.to_csv(index=False), return_tensors="pt")
            outputs = self.model(**inputs)
            predictions = outputs.logits.argmax(-1).tolist()
            pred_df = pd.DataFrame(predictions, columns=['Source', 'Destination'])
            save_path, _ = QFileDialog.getSaveFileName(self, "Save Predictions", "", "Excel Files (*.xlsx)")
            if save_path:
                pred_df.to_excel(save_path, index=False)
                self.status_label.setText(f"Predictions saved to {save_path}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ConnectorTrainer()
    window.show()
    sys.exit(app.exec())