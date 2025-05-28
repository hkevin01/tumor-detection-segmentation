import sys
import os
import subprocess

# Set a valid matplotlib backend if running outside Jupyter
if "MPLBACKEND" in os.environ and os.environ["MPLBACKEND"] == "module://matplotlib_inline.backend_inline":
    os.environ["MPLBACKEND"] = "Agg"

def install_and_import(package):
    try:
        __import__(package)
    except ImportError:
        venv = os.environ.get("VIRTUAL_ENV")
        if not venv:
            print(f"Module '{package}' not found.")
            print("You are not in a virtual environment (venv).")
            print("Please activate your venv and install dependencies with:")
            print("    source venv/bin/activate")
            print("    pip install -r requirements.txt")
            sys.exit(1)
        else:
            print(f"Module '{package}' not found in your virtual environment. Attempting to install...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                __import__(package)
            except Exception as e:
                print(f"Automatic installation failed: {e}")
                print("Run the following command in your terminal:")
                print("    pip install -r requirements.txt")
                sys.exit(1)

for pkg in ["torch", "monai", "numpy", "matplotlib", "pandas", "scikit-learn", "scipy", "tqdm"]:
    try:
        install_and_import(pkg)
    except Exception as e:
        print(f"Automatic installation failed: {e}")
        print("If you see 'No module named' errors for 'scikit-learn', try installing with:")
        print("    pip install scikit-learn")
        print("Or install all requirements with:")
        print("    pip install -r requirements.txt")
        sys.exit(1)

try:
    import torch
    from monai.networks.nets import UNet
    from monai.transforms import Compose, LoadImage, EnsureChannelFirst, Resize, ScaleIntensity, ToTensor
    from monai.data import DataLoader, Dataset
    from monai.losses import DiceLoss
    from monai.metrics import DiceMetric
except ImportError as e:
    print(f"Import failed: {e}")
    print("Please ensure all dependencies are installed in your virtual environment.")
    sys.exit(1)
import os
import json

# Load configuration
with open("../config.json") as f:
    config = json.load(f)

# Set device
device = torch.device(config["device"] if torch.cuda.is_available() else "cpu")

# Define transformations
train_transforms = Compose([
    LoadImage(image_only=True),
    EnsureChannelFirst(),
    Resize(config["image_size"]),
    ScaleIntensity(),
    ToTensor()
])

# Define dataset and dataloaders
train_dataset = Dataset(data=[], transform=train_transforms)  # Replace `data=[]` with your dataset
train_loader = DataLoader(train_dataset, batch_size=config["batch_size"], shuffle=True, num_workers=config["num_workers"])

# Define model, loss, and optimizer
model = UNet(
    dimensions=3,
    in_channels=1,
    out_channels=2,
    channels=(16, 32, 64, 128, 256),
    strides=(2, 2, 2, 2),
    num_res_units=2,
).to(device)

loss_function = DiceLoss(to_onehot_y=True, softmax=True)
optimizer = torch.optim.Adam(model.parameters(), lr=config["learning_rate"])

# Training loop
for epoch in range(config["epochs"]):
    model.train()
    epoch_loss = 0
    for batch in train_loader:
        inputs, labels = batch["image"].to(device), batch["label"].to(device)
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = loss_function(outputs, labels)
        loss.backward()
        optimizer.step()
        epoch_loss += loss.item()
    print(f"Epoch {epoch + 1}/{config['epochs']}, Loss: {epoch_loss / len(train_loader)}")