import math, torch, torch.nn as nn
H = 64          # базовая скрытая размерность
F_DIM = 4       # размер вектора features

class TemporalEncoding(nn.Module):
    def __init__(self, dim=H): super().__init__(); self.dim=dim
    def forward(self, t):                          # (B,S)
        div = torch.exp(torch.arange(0,self.dim,2,device=t.device) *
                        -(math.log(10000.0)/self.dim))
        pos = t.unsqueeze(-1).float()
        pe  = torch.zeros((*pos.shape[:-1], self.dim), device=t.device)
        pe[...,0::2]=torch.sin(pos*div); pe[...,1::2]=torch.cos(pos*div)
        return pe                                  # (B,S,H)

class EventEmbedding(nn.Module):
    def __init__(self, node_dim, feature_dim=F_DIM):
        super().__init__()
        self.p_node = nn.Linear(node_dim, H)
        self.p_time = nn.Linear(H, H)
        self.p_feat = nn.Linear(feature_dim, H)
        self.out    = nn.Linear(H*4, H)
    def forward(self, h_u, h_v, t_enc, f_vec):
        z = torch.cat([self.p_node(h_u),
                       self.p_node(h_v),
                       self.p_time(t_enc),
                       self.p_feat(f_vec)], dim=-1)
        return self.out(z)                         # (B,S,H)

class TGTTv3(nn.Module):
    def __init__(self, node_dim=H, n_heads=4, n_layers=2, dropout=0.2):
        super().__init__()
        self.tenc = TemporalEncoding(H)
        self.eemb = EventEmbedding(node_dim)
        enc = nn.TransformerEncoderLayer(
            d_model=H, nhead=n_heads, batch_first=True, dropout=dropout)
        self.encoder = nn.TransformerEncoder(enc, n_layers)
        self.gru  = nn.GRU(H, H, batch_first=True)
        self.head = nn.Linear(H, 1)
    def forward(self, h_dict, batch_seq):          # seq = (u,v,t,f,label)
        B,S = len(batch_seq), len(batch_seq[0])
        dev = next(self.parameters()).device
        h_u = torch.stack([torch.stack([h_dict[u] for (u,_,_,_,_) in seq])
                           for seq in batch_seq]).to(dev)
        h_v = torch.stack([torch.stack([h_dict[v] for (_,v,_,_,_) in seq])
                           for seq in batch_seq]).to(dev)
        ts  = torch.tensor([[t for *_,t,_,_ in seq] for seq in batch_seq],
                           device=dev)
        f_vec = torch.stack([torch.stack([f for *_,f,_ in seq])
                             for seq in batch_seq]).to(dev)
        e = self.eemb(h_u, h_v, self.tenc(ts), f_vec)
        mask = torch.triu(torch.ones(S,S,device=dev),1).bool()
        z = self.encoder(e, mask=mask)             # (B,S,H)
        new_h = {}
        for b, seq in enumerate(batch_seq):
            for i,(u,v,_,_,_) in enumerate(seq):
                step = z[b:b+1,i:i+1]
                for n in (u,v):
                    prev = h_dict[n].unsqueeze(0).unsqueeze(0).to(dev)
                    upd,_ = self.gru(step, prev)
                    new_h[n] = upd.squeeze(0).squeeze(0)
        return new_h, self.head(z).squeeze(-1)     # logits (B,S)
