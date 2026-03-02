# 🎭 Deepfake Analyzer (CNN + GNN)

A Deepfake Detection Web Application built using a hybrid CNN + Graph
Neural Network architecture.

This project performs face-based deepfake classification by combining:

-   🧠 ResNet18 (CNN branch)
-   🔗 Hierarchical Graph Convolutional Network (GNN branch)
-   🎥 Face extraction using MTCNN
-   🌐 Streamlit Web Interface

------------------------------------------------------------------------

## 🚀 Features

-   Upload a video (.mp4, .avi, .mov)
-   Automatic face extraction (MTCNN)
-   Patch-based graph construction from facial regions
-   CNN + GNN fusion model (FuNetA)
-   Binary classification: **Real vs Deepfake**
-   Clean Streamlit UI

------------------------------------------------------------------------

## 🧠 Model Architecture

### CNN Branch

-   Pretrained ResNet18 (feature extractor)
-   Fully connected layer → 600-dimensional embedding

### GNN Branch

-   Patch extraction (32x32 patches)
-   k-NN graph construction using cosine similarity
-   Multi-layer GCN with residual connections
-   Global max pooling

### Fusion Strategy

Additive fusion:

CNN(features) + GNN(features)

Final classification layer:

Linear(600 → 2)

Output: - Class 0 → Real - Class 1 → Deepfake

------------------------------------------------------------------------

## 📂 Project Structure

    Deepfake-Analyzer/
    │
    ├── app.py
    ├── model_definitions.py
    ├── my_models.py
    ├── requirements.txt
    └── README.md

Model weights are hosted separately (see below).

------------------------------------------------------------------------

## 📦 Installation

### ✅ Recommended Python Version

Python **3.10**

### 1️⃣ Create Virtual Environment

python -m venv venv

Activate:

Windows: venv`\Scripts`{=tex}`\activate`{=tex}

Mac/Linux: source venv/bin/activate

### 2️⃣ Install Dependencies

pip install -r requirements.txt

------------------------------------------------------------------------

## 🧾 Model Weights

The pretrained model file:

funet_a\_full.pth

Due to GitHub file size limits, download it from the **Releases**
section of this repository.

After downloading, place it inside:

Deepfake-Analyzer/

------------------------------------------------------------------------

## ▶️ Run the App

From inside the Deepfake-Analyzer folder:

streamlit run app.py

The app will open in your browser.

------------------------------------------------------------------------

## 🛠 Tech Stack

-   Python 3.10
-   PyTorch
-   Torchvision
-   Torch Geometric
-   Streamlit
-   OpenCV
-   MTCNN
