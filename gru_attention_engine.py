import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.preprocessing import MinMaxScaler

torch.manual_seed(42)
np.random.seed(42)

class SoftAttention(nn.Module):
    def __init__(self, hidden_dim):
        super(SoftAttention, self).__init__()
        self.W_a = nn.Linear(hidden_dim, hidden_dim, bias=True)
        self.v_a = nn.Linear(hidden_dim, 1, bias=False)

    def forward(self, gru_outputs):
        scores = torch.tanh(self.W_a(gru_outputs))
        scores = self.v_a(scores)
        attention_weights = F.softmax(scores, dim=1)
        context_vector = torch.sum(attention_weights * gru_outputs, dim=1)
        return context_vector, attention_weights

class AttentionGRUModel(nn.Module):
    def __init__(self, input_dim, hidden_dim=128, output_dim=1, dropout=0.2):
        super(AttentionGRUModel, self).__init__()
        self.gru = nn.GRU(input_size=input_dim, hidden_size=hidden_dim, batch_first=True)
        self.attention = SoftAttention(hidden_dim)
        self.fc1 = nn.Linear(hidden_dim, 64)
        self.fc2 = nn.Linear(64, 32)
        self.out = nn.Linear(32, output_dim)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        gru_out, _ = self.gru(x)
        context, attn_weights = self.attention(gru_out)
        x = F.relu(self.fc1(context))
        x = self.dropout(x)
        x = F.relu(self.fc2(x))
        x = self.dropout(x)
        predictions = self.out(x)
        return predictions, attn_weights

def run_gru_inference(price_series, sentiment_series, lookback=60):
    raw_data = np.column_stack([price_series, sentiment_series])
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(raw_data)

    if len(scaled_data) < lookback:
        lookback = len(scaled_data) - 1

    input_seq = scaled_data[-lookback:].reshape(1, lookback, raw_data.shape[1])
    tensor_input = torch.FloatTensor(input_seq)

    model = AttentionGRUModel(input_dim=raw_data.shape[1])
    model.eval()
    
    with torch.no_grad():
        pred_scaled, attn_weights = model(tensor_input)
    
    dummy_matrix = np.zeros((1, raw_data.shape[1]))
    dummy_matrix[0, 0] = pred_scaled.item()
    predicted_spot_price = scaler.inverse_transform(dummy_matrix)[0, 0]
    
    weights = attn_weights.squeeze().numpy()
    weighted_sentiment = np.sum(weights * sentiment_series[-lookback:])

    return float(predicted_spot_price), float(weighted_sentiment)

if __name__ == "__main__":
    prices = np.linspace(9820.0, 10500.0, 100) + np.random.randn(100) * 10
    sentiments = np.random.uniform(-0.8, 0.2, 100)
    spot, si = run_gru_inference(prices, sentiments)
    print(f"✓ Inference Engine Operational | Predicted Spot: ${spot:.2f} | Weighted SI: {si:.3f}")
