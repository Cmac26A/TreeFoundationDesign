
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# Define tree database
TREE_DB = pd.DataFrame({
    'Category': ['Oak', 'Pine', 'Maple'],
    'Mature Height': [20, 25, 18],
    'Coniferous': [False, True, False],
    'Water Demand': ['Medium', 'High', 'Low']
})

PARAM_DB = pd.DataFrame({
    'Soil volume potential': ['High', 'High', 'High'],
    'Coniferous': [False, True, False],
    'Water Demand': ['Medium', 'High', 'Low'],
    'Depth Factor': [1.0, 1.2, 0.8],
    'Spread Factor': [1.5, 2.0, 1.2]
})

# Cone function generator
def create_cone_function(params, height_to_use, mature_height):
    depth_factor = params['Depth Factor']
    spread_factor = params['Spread Factor']
    max_radius = mature_height * spread_factor
    max_depth = -height_to_use * depth_factor

    def cone_func(r):
        if r > max_radius:
            return 0.0
        return max_depth * (1 - r / max_radius)

    return cone_func

# Streamlit UI
st.title("Tree Root Influence Contour Model")

st.sidebar.header("Add Tree")
tree_name = st.sidebar.selectbox("Tree Species", TREE_DB['Category'].unique())
x_coord = st.sidebar.slider("X Coordinate", 0, 100, 50)
y_coord = st.sidebar.slider("Y Coordinate", 0, 100, 50)
current_height = st.sidebar.slider("Current Height (m)", 1, 30, 10)
remove_status = st.sidebar.selectbox("Remove Tree?", ['No', 'Yes'])
tree_base_height = st.sidebar.slider("Tree Base Elevation", -10.0, 10.0, 0.0)

if 'trees' not in st.session_state:
    st.session_state.trees = []

if st.sidebar.button("Add Tree"):
    st.session_state.trees.append({
        'Tree Name': tree_name,
        'X': x_coord,
        'Y': y_coord,
        'Current Height': current_height,
        'Remove': remove_status,
        'Tree base height': tree_base_height
    })

st.subheader("Current Trees")
st.write(pd.DataFrame(st.session_state.trees))

# Create grid
x_coords = np.linspace(0, 100, 200)
y_coords = np.linspace(0, 100, 200)
X, Y = np.meshgrid(x_coords, y_coords)
combined_elevations = np.full(X.shape, 9999.0)

# Process each tree
for tree in st.session_state.trees:
    tree_data = TREE_DB[TREE_DB['Category'] == tree['Tree Name']].iloc[0]
    mature_height = tree_data['Mature Height']
    is_coniferous = tree_data['Coniferous']
    water_demand = tree_data['Water Demand']

    height_to_use = tree['Current Height'] if tree['Remove'] == 'Yes' else mature_height

    params = PARAM_DB[
        (PARAM_DB['Soil volume potential'] == 'High') &
        (PARAM_DB['Coniferous'] == is_coniferous) &
        (PARAM_DB['Water Demand'] == water_demand)
    ].iloc[0]

    cone_func = create_cone_function(params, height_to_use, mature_height)
    radial_distances = np.sqrt((X - tree['X'])**2 + (Y - tree['Y'])**2)
    current_depths = np.vectorize(cone_func)(radial_distances)
    current_elevations = tree['Tree base height'] + current_depths
    combined_elevations = np.minimum(combined_elevations, current_elevations)

# Plot
fig = go.Figure(data=
    go.Contour(
        z=combined_elevations,
        x=x_coords,
        y=y_coords,
        colorscale='Viridis',
        contours_coloring='heatmap',
        line_smoothing=0.85
    )
)
fig.update_layout(title='Combined Tree Root Influence Elevation Map')

st.plotly_chart(fig)
