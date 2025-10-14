"""
Deep Transformer Model with MC Dropout

Temporal Fusion Transformer-inspired model for crypto prediction.
Uses MC Dropout for epistemic uncertainty estimation.
"""
import torch
import torch.nn as nn


class SeqTransformer(nn.Module):
    """
    Sequence Transformer with uncertainty estimation.
    
    Architecture:
        - Linear projection
        - Transformer Encoder
        - Multiple prediction heads:
            - Classification (p_up)
            - Regression (expected return μ)
            - Uncertainty (σ via MC Dropout)
    """
    
    def __init__(
        self,
        in_dim: int,
        d_model: int = 128,
        nhead: int = 4,
        nlayers: int = 3,
        dropout: float = 0.1,
    ):
        super().__init__()
        
        self.in_dim = in_dim
        self.d_model = d_model
        
        # Input projection
        self.input_proj = nn.Linear(in_dim, d_model)
        
        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dropout=dropout,
            batch_first=True,
            dim_feedforward=d_model * 4,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=nlayers)
        
        # Prediction heads
        self.head_cls = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_model // 2, 1),  # logit for p_up
        )
        
        self.head_mu = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_model // 2, 1),  # expected return
        )
        
        self.head_sigma = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_model // 2, 1),  # log std (uncertainty)
        )
    
    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Forward pass.
        
        Args:
            x: (batch, seq_len, in_dim)
        
        Returns:
            (logit, mu, sigma)
        """
        # Project input
        h = self.input_proj(x)  # (B, T, d_model)
        
        # Transformer encoding
        h = self.transformer(h)  # (B, T, d_model)
        
        # Use last timestep
        h_last = h[:, -1, :]  # (B, d_model)
        
        # Prediction heads
        logit = self.head_cls(h_last).squeeze(-1)  # (B,)
        mu = self.head_mu(h_last).squeeze(-1)  # (B,)
        
        # Sigma via softplus (ensure positive)
        log_sigma = self.head_sigma(h_last).squeeze(-1)
        sigma = torch.nn.functional.softplus(log_sigma) + 1e-6  # (B,)
        
        return logit, mu, sigma


def mc_predict(
    model: SeqTransformer,
    x: torch.Tensor,
    n_samples: int = 20,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Monte Carlo Dropout prediction for uncertainty estimation.
    
    Args:
        model: Trained model
        x: Input (batch, seq_len, in_dim)
        n_samples: Number of MC samples
    
    Returns:
        (p_up, mu, sigma) - averaged predictions with uncertainty
    """
    model.train()  # Enable dropout
    
    probs = []
    mus = []
    sigmas = []
    
    with torch.no_grad():
        for _ in range(n_samples):
            logit, mu, sigma = model(x)
            probs.append(torch.sigmoid(logit))
            mus.append(mu)
            sigmas.append(sigma)
    
    # Average predictions
    p_up = torch.stack(probs).mean(0)
    mu_avg = torch.stack(mus).mean(0)
    
    # Uncertainty: variance of predictions + model sigma
    epistemic_uncertainty = torch.stack(probs).std(0)
    aleatoric_uncertainty = torch.stack(sigmas).mean(0)
    total_uncertainty = torch.sqrt(epistemic_uncertainty**2 + aleatoric_uncertainty**2)
    
    return p_up, mu_avg, total_uncertainty


def create_model(in_dim: int, **kwargs) -> SeqTransformer:
    """Factory function to create model with default params."""
    return SeqTransformer(
        in_dim=in_dim,
        d_model=kwargs.get("d_model", 128),
        nhead=kwargs.get("nhead", 4),
        nlayers=kwargs.get("nlayers", 3),
        dropout=kwargs.get("dropout", 0.1),
    )

