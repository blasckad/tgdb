# train_tgtt_v3.py
# ──────────────────────────────────────────────────────────────────────────
#  Temporal Graph Transformer v3 + action-features
#  • сплит по user_id
#  • окно WINDOW последних действий
#  • раздельные mailbox-ы для train / val
#  • Focal BCE (γ=2) с глобальным pos_weight
#  • dropout-0.2, AdamW, weight-decay
# ──────────────────────────────────────────────────────────────────────────
import random, torch, torch.nn as nn
from collections import deque
from datetime import datetime
from torchmetrics.classification import BinaryAccuracy, BinaryAUROC

from data_storage.read import EDGE_DIR_TREE, sliding_user_windows   # ← см. read.py
from analysis.tgtt_big import TGTT                 # вместо v3

# ===============  гиперпараметры  ========================================
H              = 128        # базовая размерность скрытых векторов
WINDOW         = 100        # длина последовательности событий на пользователя
BATCH_USERS    = 64        # пользователей в одном batch  ⇒ (B,S)
TRAIN_FRAC     = 0.8
EPOCHS         = 25
LR             = 5e-5
WEIGHT_DECAY   = 5e-5
GRAD_CLIP      = 1.0
GAMMA_FOCAL    = 2.0       # γ в Focal BCE
SEED           = 42
MODEL_PATH     = f"tgtt_userv3_{datetime.now():%Y%m%d_%H%M}.pt"
# ==========================================================================

rng = random.Random(SEED)
torch.manual_seed(SEED)

device = torch.device("cuda:0")
assert torch.cuda.is_available(), "CUDA not detected – install torch-cu* and driver"

# ────────── 1. Получаем список всех пользователей в индексе ───────────────
all_users = {name for (name, direction) in EDGE_DIR_TREE if direction == "out"}
all_users = list(all_users)
rng.shuffle(all_users)

split = int(len(all_users) * TRAIN_FRAC)
train_users = set(all_users[:split])
val_users   = set(all_users[split:])

print(f"Users: total={len(all_users)} | train={len(train_users)} | val={len(val_users)}")

# ────────── 2. Формируем окна событий через read.sliding_user_windows ─────
train_windows = list(sliding_user_windows(train_users, WINDOW))
val_windows   = list(sliding_user_windows(val_users,   WINDOW))

print(f"Windows: train={len(train_windows)}  val={len(val_windows)}")

# ────────── 3. Подсчитываем pos_weight по всему набору ────────────────────
n_pos = sum(lbl for seq in train_windows for *_, lbl in seq) + \
        sum(lbl for seq in val_windows   for *_, lbl in seq)
n_all = (len(train_windows) + len(val_windows)) * WINDOW
pos_ratio  = n_pos / n_all
pos_weight = torch.tensor([(1 - pos_ratio) / pos_ratio], device=device)
print(f"Positive ratio={pos_ratio:.4%}  =>  pos_weight={pos_weight.item():.2f}")

# ────────── 4. Инициализация модели и инструментов ────────────────────────
model = TGTT(node_dim=H, dropout=0.2).to(device)
optim = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)

acc_tr, auc_tr = BinaryAccuracy().to(device), BinaryAUROC().to(device)
acc_val, auc_val = BinaryAccuracy().to(device), BinaryAUROC().to(device)

# Focal-BCE   (γ=2, α = pos_weight / (1+pos_weight))
alpha = pos_weight / (1 + pos_weight)
def focal_bce_logits(logit, y):
    bce = nn.functional.binary_cross_entropy_with_logits(
        logit, y, pos_weight=pos_weight, reduction="none")
    p_t = torch.exp(-bce)           # σ(z)  если y=1; 1-σ(z) если y=0
    focal = (alpha * y + (1 - alpha) * (1 - y)) * (1 - p_t) ** GAMMA_FOCAL * bce
    return focal.mean()

# ────────── 5. Mail-box (раздельно train / val) ───────────────────────────
mail_train, mail_val = {}, {}                   # node → deque(maxlen=WINDOW)
def get_state(buf, node):
    if node not in buf:
        buf[node] = deque(maxlen=WINDOW)
        buf[node].append(torch.zeros(H, device=device))
    return buf[node][-1]

def update_state(buf, node, vec):
    if node not in buf:  # ← добавьте эту строку
        buf[node] = deque(maxlen=WINDOW)
    buf[node].append(vec.detach())

# ────────── 6. Batch-итератор по пользователям ────────────────────────────
def batch_iter(win_list, batch_users=BATCH_USERS):
    rng.shuffle(win_list)
    for i in range(0, len(win_list), batch_users):
        yield win_list[i:i+batch_users]

# ────────── 7. Цикл обучения ───────────────────────────────────────────────
best_val_auc, patience = 0.0, 0

for epoch in range(1, EPOCHS + 1):

    # ================= TRAIN ===================
    model.train()
    acc_tr.reset(); auc_tr.reset(); loss_sum_tr = 0

    for windows in batch_iter(train_windows):
        # h_dict: текущие состояния участников
        h_dict = {n: get_state(mail_train, n)
                  for seq in windows for (u, v, *_ ) in seq for n in (u, v)}

        # дата-тензоры
        labels = torch.tensor([[lbl for *_, lbl in seq] for seq in windows],
                              dtype=torch.float32, device=device)
        upd, logits = model(h_dict, windows)[:2]
        loss = focal_bce_logits(logits, labels)

        optim.zero_grad(); loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), GRAD_CLIP)
        optim.step()

        # обновление mail-box
        for n, vec in upd.items(): update_state(mail_train, n, vec)
        loss_sum_tr += loss.item() * labels.numel()

        prob = logits.sigmoid()
        acc_tr.update(prob, labels); auc_tr.update(prob, labels)

    # ================= VALID ===================
    model.eval()
    acc_val.reset(); auc_val.reset(); loss_sum_val = 0

    with torch.no_grad():
        for windows in batch_iter(val_windows):
            h_dict = {n: get_state(mail_val, n)
                      for seq in windows for (u, v, *_ ) in seq for n in (u, v)}
            labels = torch.tensor([[lbl for *_, lbl in seq] for seq in windows],
                                  dtype=torch.float32, device=device)
            _, logits = model(h_dict, windows)[:2]
            loss_val = focal_bce_logits(logits, labels)

            # обновляем mail_val, но НЕ переносим в след. эпоху (холодный старт)
            for n, vec in upd.items(): update_state(mail_val, n, vec)

            loss_sum_val += loss_val.item() * labels.numel()
            prob = logits.sigmoid()
            acc_val.update(prob, labels); auc_val.update(prob, labels)

    denom_tr  = len(train_windows) * WINDOW
    denom_val = len(val_windows)   * WINDOW
    val_auc   = auc_val.compute().item()
    print(f"epoch {epoch:02}/{EPOCHS} | "
          f"train loss {loss_sum_tr/denom_tr:.4f} acc {acc_tr.compute():.3f} auc {auc_tr.compute():.3f} | "
          f"val loss {loss_sum_val/denom_val:.4f} acc {acc_val.compute():.3f} auc {val_auc:.3f}")

    # ---------- early stopping ----------
    if val_auc > best_val_auc:
        best_val_auc = val_auc
        torch.save(model.state_dict(), MODEL_PATH)
        patience = 0
    else:
        patience += 1
        if patience >= 3:
            print("Early-stop: no improvement 3 epochs")
            break

print(f"✅  лучшая модель сохранена в {MODEL_PATH}  |  best val-AUC = {best_val_auc:.3f}")
