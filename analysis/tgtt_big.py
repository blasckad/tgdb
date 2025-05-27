# analysis/tgtt_big.py
import math, torch, torch.nn as nn
F_DIM = 4          # размер вектора mooc_action_features

class TemporalEncoding(nn.Module):
    def __init__(self, d_model): super().__init__(); self.d = d_model
    def forward(self, t):
        div = torch.exp(torch.arange(0, self.d, 2, device=t.device) *
                        -(math.log(10000.0)/self.d))
        pos = t.unsqueeze(-1).float()
        pe  = torch.zeros((*pos.shape[:-1], self.d), device=t.device)
        pe[...,0::2] = torch.sin(pos*div); pe[...,1::2] = torch.cos(pos*div)
        return pe

class EventEmbedding(nn.Module):
    def __init__(self, node_dim, d_model, feature_dim=F_DIM):
        super().__init__()
        self.p_node = nn.Linear(node_dim, d_model)
        self.p_time = nn.Linear(d_model, d_model)
        self.p_feat = nn.Linear(feature_dim, d_model)
        self.out    = nn.Linear(d_model*4, d_model)
    def forward(self, h_u,h_v,t_enc,f_vec):
        z = torch.cat([self.p_node(h_u),
                       self.p_node(h_v),
                       self.p_time(t_enc),
                       self.p_feat(f_vec)], dim=-1)
        return self.out(z)

class TGTT(nn.Module):
    """Гибкий Temporal Graph Transformer"""
    def __init__(self, node_dim=128, d_model=128, n_heads=8, n_layers=3,
                 dropout=0.2):
        super().__init__()
        self.tenc = TemporalEncoding(d_model)
        self.eemb = EventEmbedding(node_dim, d_model)
        enc_layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=n_heads, batch_first=True,
            dim_feedforward=d_model*4, dropout=dropout, norm_first=True)
        self.encoder = nn.TransformerEncoder(enc_layer, n_layers)
        self.gru  = nn.GRU(d_model, d_model, batch_first=True)
        self.head = nn.Linear(d_model, 1)

    def forward(self, h_dict, batch_seq):          # kортежи (u,v,t,f,label)
        B,S = len(batch_seq), len(batch_seq[0])
        dev = next(self.parameters()).device
        h_u = torch.stack([torch.stack([h_dict[u] for (u,_,_,_,_) in seq])
                           for seq in batch_seq]).to(dev)
        h_v = torch.stack([torch.stack([h_dict[v] for (_,v,_,_,_) in seq])
                           for seq in batch_seq]).to(dev)
        ts  = torch.tensor([[t for *_,t,_,_ in seq] for seq in batch_seq], device=dev)
        f_vec = torch.stack([torch.stack([f for *_,f,_ in seq]) for seq in batch_seq]).to(dev)

        e = self.eemb(h_u, h_v, self.tenc(ts), f_vec)
        mask = torch.triu(torch.ones(S,S,device=dev),1).bool()
        z = self.encoder(e, mask=mask)

        new_h = {}
        for b, seq in enumerate(batch_seq):
            for i,(u,v,_,_,_) in enumerate(seq):
                step = z[b:b+1, i:i+1]
                for n in (u, v):
                    prev = h_dict[n].unsqueeze(0).unsqueeze(0).to(dev)
                    upd, _ = self.gru(step, prev)
                    new_h[n] = upd.squeeze(0).squeeze(0)
        return new_h, self.head(z).squeeze(-1)
