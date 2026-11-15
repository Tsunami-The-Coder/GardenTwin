import torch
import time

print("PyTorch:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())

torch.set_num_threads(4)

print("\nImporting NVIDIA FourCastNet...")
from earth2studio.models.px import FCN

print("Loading public pretrained checkpoint...")
start = time.time()

package = FCN.load_default_package()
model = FCN.load_model(package)

model = model.to("cpu")
model.eval()

print("\nEARTH-2 MODEL LOAD SUCCESS")
print("Model:", model)
print("Parameters:", sum(p.numel() for p in model.parameters()))
print("Device: CPU")
print("Load time:", round(time.time() - start, 2), "seconds")
