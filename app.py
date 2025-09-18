
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

@st.cache_data
def load_tree_species_data():
    df = pd.read_excel("Tree_data.xlsx", engine="openpyxl")
    df['Coniferous'] = df['Coniferous'].map({'T': True, 'F': False})
    return df

@st.cache_data
def load_depth_function_data():
    df = pd.read_excel("Tree_linegraphs.xlsx", engine="openpyxl")
    df['Coniferous'] = df['Coniferous'].map({'T': True, 'F': False})
    return df

def get_depth_params(species_name, species_df, depth_df, soil_type):
    tree = species_df[species_df['Category'] == species_name].iloc[0]
    coniferous = tree['Coniferous']
    water_demand = tree['Water Demand']
    match = depth_df[(depth_df['Coniferous'] == coniferous) &
                     (depth_df['Water Demand'] == water_demand) &
                     (depth_df['Soil volume potential'] == soil_type)]
    if not match.empty:
        params = match.iloc[0]
        return params['x2'], params['x1'], params['y1']
    else:
        return None, None, None

def compute_depth(r, x2, x1, y1):
    return x2 * r**2 + x1 * r + y1

def model_influence(trees, species_df, depth_df, soil_type, grid_size=100, spacing=1.0):
    x_vals = np.linspace(0, grid_size * spacing, grid_size)
    y_vals = np.linspace(0, grid_size * spacing, grid_size)
    X, Y = np.meshgrid(x_vals, y_vals)
    Z = np.full_like(X, np.nan)

    for tree in trees:
        x, y, z, species, removal = tree['x'], tree['y'], tree['z'], tree['species'], tree['removal']
        if removal:
            continue
        x2, x1, y1 = get_depth_params(species, species_df, depth_df, soil_type)
        if None in (x2, x1, y1):
            continue
        R = np.sqrt((X - x)**2 + (Y - y)**2)
        depth = compute_depth(R, x2, x1, y1)
        absolute_depth = z - depth
        if np.isnan(Z).all():
            Z = absolute_depth
        else:
            Z = np.minimum(Z, absolute_depth)

    return X, Y, Z

if 'trees' not in st.session_state:
    st.session_state.trees = []

species_df = load_tree_species_data()
depth_df = load_depth_function_data()
species_list = species_df['Category'].tolist()

st.title("Tree Root Influence Design Tool")
st.write("Input tree data to model root influence on foundations.")

soil_type = st.selectbox("Select Soil Plasticity", ["High", "Medium", "Low"])

with st.form("tree_input_form"):
    x = st.number_input("X Coordinate", value=0.0)
    y = st.number_input("Y Coordinate", value=0.0)
    z = st.number_input("Z Elevation", value=0.0)
    species = st.selectbox("Tree Species", species_list)
    removal = st.checkbox("Tree will be removed")
    submitted = st.form_submit_button("Add Tree")

    if submitted:
        st.session_state.trees.append({
            'x': x,
            'y': y,
            'z': z,
            'species': species,
            'removal': removal
        })
        st.success(f"Tree '{species}' added at ({x}, {y}, {z})")

if st.session_state.trees:
    st.subheader("Added Trees")
    st.dataframe(pd.DataFrame(st.session_state.trees))

    X, Y, Z = model_influence(st.session_state.trees, species_df, depth_df, soil_type)
    fig, ax = plt.subplots()
    contour = ax.contourf(X, Y, Z, levels=20, cmap='viridis')
    plt.colorbar(contour, ax=ax)
    ax.set_title("Contour Plot of Tree Root Influence")
    st.pyplot(fig)
else:
    st.info("No trees added yet.")
