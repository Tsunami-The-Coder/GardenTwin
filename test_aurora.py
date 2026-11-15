
import torch
from aurora import AuroraSmallPretrained

print("Device:", "cuda" if torch.cuda.is_available() else "cpu")
print("Loading Aurora Small pretrained model...")

model = AuroraSmallPretrained()
model.load_checkpoint()
model.eval()

device = "cuda" if torch.cuda.is_available() else "cpu"
model = model.to(device)

print("SUCCESS: Aurora checkpoint loaded.")
print("Model:", type(model).__name__)
print("Device:", device)

if torch.cuda.is_available():
    print(
        "GPU memory allocated:",
        round(torch.cuda.memory_allocated() / 1024**3, 2),
        "GB"
    )
