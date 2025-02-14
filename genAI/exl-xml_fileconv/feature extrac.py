import pandas as pd
import json

# Load labeled data
labeled_data = json.load(open('labeled_data.json'))

# Prepare features for training
features = []
labels = []

for item in labeled_data:
    # Example features: row, column, and a textual feature
    feature = {
        'row': item['row'],
        'col': item['col'],
        'text_feature': 'Pin' if item['label'] == 'Pin' else ('Connector' if item['label'] == 'Connector' else 'Connection')
    }
    features.append(feature)
    labels.append(item['label'])

# Convert to pandas DataFrame for model input
features_df = pd.DataFrame(features)
labels_df = pd.Series(labels)

print(features_df.head())
