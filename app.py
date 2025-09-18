
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# Load real datasets
TREE_DB = pd.read_excel('Tree_data.xlsx', sheet_name='Sheet1', engine='openpyxl')
PARAM_DB = pd.read_excel('Tree_linegraphs.xlsx', sheet_name='Sheet1', engine='openpyxl')

# Cone function generator
def create_cone_function(params, mature_height):
    depth_factor = float(params['x2'])
    spread_factor = float(params['y1'])
    max_radius = mature_height * spread_factor
    max_depth = -mature_height * depth_factor
    def cone_func(r):
        return max_depth * (1 - r / max_radius) if r <= max_radius else 0.0
    return cone_func

# Streamlit UI
st.title("Tree Root Influence Contour Model")

# Global parameters
st.sidebar.header("Global Parameters")
soil_plasticity = st.sidebar.text_input("Soil Plasticity", "Medium")
ffl = float(st.sidebar.text_input("Finished Floor Level (FFL)", "13"))
min_depth = float(st.sidebar.text_input("Minimum Depth", "1"))
starting_elevation = ffl - min_depth

# Tree input
st.sidebar.header("Add Tree")
tree_name = st.sidebar.selectbox("Tree Species", TREE_DB['Category'].unique())
x_coord = float(st.sidebar.text_input("X Coordinate", "50"))
y_coord = float(st.sidebar.text_input("Y Coordinate", "50"))
z_coord = float(st.sidebar.text_input("Tree Base Elevation", str(starting_elevation)))
remove_status = st.sidebar.selectbox("Remove Tree?", ['No', 'Yes'])

if 'trees' not in st.session_state:
    st.session_state.trees = []

if st.sidebar.button("Add Tree"):
    st.session_state.trees.append({
        'Tree Name': tree_name,
        'X': x_coord,
        'Y': y_coord,
        'Z': z_coord,
        'Remove': remove_status
    })

# Display tree table
st.subheader("Current Trees")
st.dataframe(pd.DataFrame(st.session_state.trees))

# Create grid
x_coords = np.linspace(0, 100, 200)
y_coords = np.linspace(0, 100, 200)
X, Y = np.meshgrid(x_coords, y_coords)
combined_elevations = np.full(X.shape, starting_elevation)

# Process each tree
for tree in st.session_state.trees:
    tree_data = TREE_DB[TREE_DB['Category'] == tree['Tree Name']].iloc[0]
    mature_height = float(tree_data['Mature Height'])
    is_coniferous = tree_data['Coniferous']
    water_demand = tree_data['Water Demand']

    params = PARAM_DB[
        (PARAM_DB['Soil volume potential'] == 'High') &
        (PARAM_DB['Coniferous'] == is_coniferous) &
        (PARAM_DB['Water Demand'] == water_demand)
    ].iloc[0]

    cone_func = create_cone_function(params, mature_height)
    radial_distances = np.sqrt((X - tree['X'])**2 + (Y - tree['Y'])**2)
    current_depths = np.vectorize(cone_func)(radial_distances)
    current_elevations = tree['Z'] + current_depths
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
