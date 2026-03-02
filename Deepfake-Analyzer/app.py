import streamlit as st      #Creates the web app interface.
import numpy as np      #Handles numerical operations (like turning images into arrays)
import cv2      #Processes video frames and images.
import os
import tempfile      #this module provides generic, low- and high-level interfaces for creating temporary files and directories.
import torch
import torch.nn as nn
import torch.nn.functional as F
from model_definitions import FuNetA
from my_models import extract_faces_from_video, image_to_graph
import os

# Set Streamlit page config
st.set_page_config(page_title="Deepfake analyser", layout="wide")

# 💅 Custom CSS
st.markdown("""
    <style>
    body { background-color: #fff0f5; }
    body, .stTextInput, .stFileUploader label, .stMarkdown, .stText {
        color: #880e4f;
    }
    .main {
        background-color: #fff0f5;
        padding: 0;
    }
    .pink-card {
        background-color: #ffe6f0;
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(216, 27, 96, 0.2);
        border: 1px solid #f8bbd0;
        color: #880e4f;
    }
    .taskbar {
        background-color: #ffe6f0;
        padding: 15px 30px;
        border-radius: 0 0 12px 12px;
        color: #880e4f;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-family: 'Segoe UI', sans-serif;
        border-bottom: 2px solid #f8bbd0;
    }
    .taskbar a {
        color: #880e4f;
        margin: 0 10px;
        font-size: 18px;
        text-decoration: none;
        font-weight: 600;
        position: relative;
        transition: color 0.2s ease-in-out;
    }
    .taskbar a:not(:last-child)::after {
        content: "|";
        color: #d81b60;
        margin-left: 15px;
        margin-right: 10px;
        font-weight: 400;
    }
    .taskbar a:hover {
        text-decoration: underline;
        color: #d81b60;
    }
    </style>
""", unsafe_allow_html=True)

# Load model and detector
#Loads your trained CNN model for deepfake detection.
# Define the same architecture
model = FuNetA()
model.load_state_dict(torch.load("funet_a_full.pth", map_location="cpu"))
model.eval()
model_path = "funet_a_full.pth"

if not os.path.exists(model_path):
    st.error("Model file not found. Download it from the Releases section and place it inside the Deepfake-Analyzer folder.")
    st.stop()

model.load_state_dict(torch.load(model_path, map_location="cpu"))


# 💻 Taskbar
st.markdown("""
    <div class="taskbar">
        <div><strong style='font-size: 20px;'>💖 Deepfake Analyzer</strong></div>
        <div>
            <a href="#upload">Upload</a>
            <a href="#results">Results</a>
            <a href="#about">About</a>
        </div>
    </div>
""", unsafe_allow_html=True)

# 🎯 Title
st.markdown("<h1 style='color:#880e4f;'>Deepfake Detector</h1>", unsafe_allow_html=True)
st.write("Upload a video to get started.")

# 📦 Upload + Results cards. page is split into 2 sections
col1, spacer, col2 = st.columns([2, 0.5, 2])

with col1:
    st.markdown("""
        <div class="pink-card">
            <h3 style='color:#880e4f;'>Upload</h3>
            <p style='color:#880e4f; font-weight:bold;'>Upload a video file</p>
        </div>
    """, unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Video Upload Label", label_visibility="collapsed", type=["mp4", "avi", "mov"]) #Lets the user upload a video file

with col2:
    st.markdown("""
        <div class="pink-card">
            <h3 style='color:#880e4f;'>Results</h3>
            <p style='color:#880e4f; font-weight:bold;'>Results will appear here</p>
        </div>
    """, unsafe_allow_html=True)




# 🎥 Process uploaded video
if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
        temp_video.write(uploaded_file.read())
        temp_path = temp_video.name

    with st.spinner("Analyzing video..."):
        faces = extract_faces_from_video(temp_path, max_faces=10)

        if not faces:
            st.error("No faces detected. Try a clearer video.")
        else:
             # Convert faces to numpy array and normalize
            faces_np = np.array(faces) / 255.0  # shape: (num_faces, H, W, C)

            # Convert to torch tensor and permute to (N, C, H, W)
            input_tensor = torch.tensor(faces_np, dtype=torch.float32).permute(0, 3, 1, 2)

            # Run inference
            model.eval()
            all_probs = []

    with torch.no_grad():
        for face in faces_np:
            # Convert face to tensor (NCHW)
            face_tensor = torch.tensor(face, dtype=torch.float32).unsqueeze(0).permute(0, 3, 1, 2)

            # Build graph
            graph = image_to_graph(face_tensor.squeeze(0))
            if graph is None:
                print("⚠️ Skipping face because image_to_graph returned None")
                continue  # skip this face, don’t feed None into the model

            # Forward pass
            output = model(face_tensor, graph)

            # Get deepfake probability
            prob = torch.softmax(output, dim=1)[:, 1]
            all_probs.append(prob.item())

    # Handle case: all graphs failed
    if len(all_probs) == 0:
        st.error("No valid faces/graphs could be processed. Try a clearer video.")
    else:
        avg_prob = np.mean(all_probs)
        if avg_prob > 0.5:
            st.error(f"⚠️ This video is likely a DEEPFAKE ({avg_prob:.2f} confidence)")
        else:
            st.success(f"✅ This video is likely REAL ({1 - avg_prob:.2f} confidence)")

        os.remove(temp_path)

# 🧾 About section
st.markdown("<hr style='border:1px solid #bbb;'>", unsafe_allow_html=True)
st.markdown("<h3 style='color:#880e4f;'>About This Project</h3>", unsafe_allow_html=True)
st.write("A deepfake detection project by Team Aegis using face-based CNN+GNN classification with MTCNN .")