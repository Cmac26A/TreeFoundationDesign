
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# Load tree species and parameter data
TREE_DB = pd.read_excel('Tree_data.xlsx', sheet_name='Sheet1', engine='openpyxl')
PARAM_DB = pd.read_excel('Tree_linegraphs.xlsx', sheet_name='Sheet1', engine='openpyxl')

st.title("Tree Root Influence Contour Model")

st.sidebar.header("Global Parameters")
soil_plasticity = st.sidebar.text_input("Soil Plasticity", "High")
ffl = float(st.sidebar.text_input("Finished Floor Level (FFL)", "13"))
min_depth = float(st.sidebar.text_input("Minimum Depth", "1"))
starting_elevation = ffl - min_depth

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

st.subheader("Current Trees")
st.dataframe(pd.DataFrame(st.session_state.trees))

if st.session_state.trees:
    x_vals = [tree['X'] for tree in st.session_state.trees]
    y_vals = [tree['Y'] for tree in st.session_state.trees]
    min_x, max_x = min(x_vals), max(x_vals)
    min_y, max_y = min(y_vals), max(y_vals)
    padding = 50
    x_coords = np.linspace(min_x - padding, max_x + padding, 200)
    y_coords = np.linspace(min_y - padding, max_y + padding, 200)
    X, Y = np.meshgrid(x_coords, y_coords)

    combined_elevations = np.full(X.shape, starting_elevation)

    def create_cone_function_from_params(params_row, height_to_use, mature_height, soil_plasticity):
        x1 = params_row['x1']
        x2 = params_row['x2']
        y1 = params_row['y1']
        water_demand = params_row['Water Demand']

        min_depths = {
            'High': -1.0,
            'Medium': -0.9,
            'Low': -0.75
        }
        min_depth = min_depths.get(soil_plasticity, -1.0)

        lateral_limits_ratio = {
            'H': 1.25,
            'M': 0.75,
            'L': 0.5
        }
        lateral_limit = lateral_limits_ratio.get(water_demand, 0) * mature_height

        if height_to_use <= 0 or mature_height <= 0:
            return lambda radial_distance: 0.0

        def cone_function(radial_distance):
            if radial_distance < 0:
                return 10000.0
            if radial_distance > lateral_limit:
                return 10000.0

            d_over_h = radial_distance / height_to_use

            if pd.isna(x1):
                if d_over_h <= x2:
                    slope = (1 - y1) / x2
                    depth = slope * d_over_h + y1
                    return -max(depth, -abs(min_depth))
                else:
                    return min_depth
            else:
                if d_over_h < x1:
                    return -2.5
                elif x1 <= d_over_h <= x2:
                    slope = (1 - 2.5) / (x2 - x1)
                    depth = slope * (d_over_h - x1) + 2.5
                    return -max(depth, -abs(min_depth))
                else:
                    return min_depth

        return cone_function

    for tree in st.session_state.trees:
        tree_data = TREE_DB[TREE_DB['Category'] == tree['Tree Name']].iloc[0]
        mature_height = tree_data['Mature Height']
        is_coniferous = tree_data['Coniferous']
        water_demand = tree_data['Water Demand']
        height_to_use = mature_height if tree['Remove'] == 'No' else mature_height

        params_row = PARAM_DB[
            (PARAM_DB['Soil volume potential'] == soil_plasticity) &
            (PARAM_DB['Coniferous'] == is_coniferous) &
            (PARAM_DB['Water Demand'] == water_demand)
        ].iloc[0]

        tree_cone_func = create_cone_function_from_params(params_row, height_to_use, mature_height, soil_plasticity)
        radial_distances = np.sqrt((X - tree['X'])**2 + (Y - tree['Y'])**2)
        current_depths = np.vectorize(tree_cone_func)(radial_distances)
        current_elevations = tree['Z'] + current_depths
        combined_elevations = np.minimum(combined_elevations, current_elevations)


    z_min = combined_elevations.min()
    z_max = combined_elevations.max()
    
    fig = go.Figure(data=
        go.Contour(
            z=combined_elevations,
            x=x_coords,
            y=y_coords,
            colorscale='Viridis',
            contours=dict(
                start=z_min-0.3,       # minimum elevation value
                end=z_max+0.3,         # maximum elevation value
                size=0.3,         # spacing between contour levels
                coloring='heatmap' # use heatmap-style coloring
            ),
            line_smoothing=0.85
        )
    )
    fig.update_layout(title='Combined Tree Root Influence Elevation Map',
                      xaxis_scaleanchor='y', xaxis=dict(title='X'), yaxis=dict(title='Y'))
    st.plotly_chart(fig)
