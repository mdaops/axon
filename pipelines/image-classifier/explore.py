from torchvision import datasets
from pathlib import Path 

data_dir = Path("data")
dataset = datasets.FashionMNIST(root=data_dir, train=True, download=True)

print(f"dataset size: {len(dataset)} images")
print(f"image shape: {dataset[0][0].size}")
print(f"labels: {dataset.classes}")

samples_dir = Path("data/samples")
samples_dir.mkdir(exist_ok=True)

for i in range(10):
    image, idx = dataset[i]
    label_name = dataset.classes[idx]
    print(label_name)
    image.save(samples_dir / f"{i:02d}_{label_name}.png")

print(f"saved 10 samples to {samples_dir}")
