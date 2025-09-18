
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# Load real datasets
TREE_DB = pd.read_excel('Tree_data.xlsx', sheet_name='Sheet1', engine='openpyxl')
PARAM_DB = pd.read_excel('Tree_linegraphs.xlsx', sheet_name='Sheet1', engine='openpyxl')

# Cone function generator
def create_cone_function(params, mature_height):
    try:
        depth_factor = float(params['x2'])
        spread_factor = float(params['y1'])
    except (KeyError, ValueError):
        depth_factor = 1.0
        spread_factor = 1.0
    max_radius = mature_height * spread_factor
    max_depth = -mature_height * depth_factor
    def cone_func(r):
        if r > max_radius:
            return 0.0
        return max_depth * (1 - r / max_radius)
    return cone_func

# Streamlit UI
st.title("Tree Root Influence Contour Model")

# Global parameters
st.sidebar.header("Global Parameters")
soil_plasticity = st.sidebar.text_input("Soil Plasticity", "Medium")
ffl = st.sidebar.text_input("Finished Floor Level (FFL)", "13")
min_depth = st.sidebar.text_input("Minimum Depth", "1")

try:
    ffl_val = float(ffl)
    min_depth_val = float(min_depth)
    starting_elevation = ffl_val - min_depth_val
except ValueError:
    st.error("Please enter valid numeric values for FFL and Minimum Depth.")
    st.stop()

# Tree input
st.sidebar.header("Add Tree")
tree_name = st.sidebar.selectbox("Tree Species", TREE_DB['Category'].dropna().unique())
x_coord = st.sidebar.text_input("X Coordinate", "50")
y_coord = st.sidebar.text_input("Y Coordinate", "50")
z_coord = st.sidebar.text_input("Tree Base Elevation", str(starting_elevation))
remove_status = st.sidebar.selectbox("Remove Tree?", ['No', 'Yes'])

if 'trees' not in st.session_state:
    st.session_state.trees = []

if st.sidebar.button("Add Tree"):
    try:
        x_val = float(x_coord)
        y_val = float(y_coord)
        z_val = float(z_coord)
        st.session_state.trees.append({
            'Tree Name': str(tree_name),
            'X': x_val,
            'Y': y_val,
            'Z': z_val,
            'Remove': remove_status
        })
    except ValueError:
        st.error("Please enter valid numeric values for coordinates.")

# Display tree table
st.subheader("Current Trees")
if st.session_state.trees:
    try:
        tree_df = pd.DataFrame(st.session_state.trees)
        st.dataframe(tree_df)
    except Exception as e:
        st.warning(f"Error displaying tree table: {e}")
else:
    st.write("No trees added yet.")

# Create grid
x_coords = np.linspace(0, 100, 200)
y_coords = np.linspace(0, 100, 200)
X, Y = np.meshgrid(x_coords, y_coords)
combined_elevations = np.full(X.shape, starting_elevation)

# Process each tree
for tree in st.session_state.trees:
    try:
        tree_data = TREE_DB[TREE_DB['Category'] == tree['Tree Name']]
        if tree_data.empty:
            st.warning(f"Tree species '{tree['Tree Name']}' not found in database. Skipping.")
            continue
        tree_data = tree_data.iloc[0]
        mature_height = float(tree_data['Mature Height'])
        is_coniferous = tree_data['Coniferous']
        water_demand = tree_data['Water Demand']

        params_match = PARAM_DB[
            (PARAM_DB['Soil volume potential'] == 'High') &
            (PARAM_DB['Coniferous'] == is_coniferous) &
            (PARAM_DB['Water Demand'] == water_demand)
        ]
        if params_match.empty:
            st.warning(f"No matching parameters for tree '{tree['Tree Name']}'. Using default values.")
            params = {'x2': 1.0, 'y1': 1.0}
        else:
            params = params_match.iloc[0]

        cone_func = create_cone_function(params, mature_height)
        radial_distances = np.sqrt((X - tree['X'])**2 + (Y - tree['Y'])**2)
        current_depths = np.vectorize(cone_func)(radial_distances)
        current_elevations = tree['Z'] + current_depths
        combined_elevations = np.minimum(combined_elevations, current_elevations)
    except Exception as e:
        st.warning(f"Error processing tree '{tree['Tree Name']}': {e}")

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
