
import streamlit as st
from scipy.interpolate import RegularGridInterpolator
import numpy as np
import pandas as pd
import plotly.graph_objects as go

import streamlit as st

# Initialize session state
    
    
    
if 'section_lines' not in st.session_state:
        st.session_state.section_lines = []
if 'click_points' not in st.session_state:
        st.session_state.click_points = []



# Page config
st.set_page_config(page_title="GGP - Foundations Near Trees", page_icon="🌳", layout="wide")

# Custom sidebar style
st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            background-color: #d4f4dd;
        }
    </style>
""", unsafe_allow_html=True)

# Sidebar logo
st.sidebar.image("Logo.jpeg", width='stretch')

# Main page banner
st.image("Banner.jpeg", width='stretch')





# Load tree species and parameter data
TREE_DB = pd.read_excel('Tree_data.xlsx', sheet_name='Sheet1', engine='openpyxl')
PARAM_DB = pd.read_excel('Tree_linegraphs.xlsx', sheet_name='Sheet1', engine='openpyxl')

st.title("GGP Consult: Tree influence on Foundation Design Model")

st.markdown("""
Created by C.J. McAteer


### How to use
Welcome to the Tree influence on Foundation Design. Here's how to use the app:

1. **Set Global Parameters**:
   - Enter the Finished Floor Level (FFL), Minimum Foundation Depth, and Soil Plasticity Index in the sidebar.

2. **Add Trees**:
   - Select a tree species from the dropdown.
   - Enter the mature height and X, Y, Z coordinates.
   - Click **Add Tree** to include it in the model.

3. **View Tree Data**:
   - The table below shows all trees you've added.

4. **Interpret the Contour Plot**:
   - The plot shows the cumulative root influence zones.
   - Colors represent depth influence, with discrete contour intervals.

5. **Reset**
   - Press c and enter to clear cache, press r to rerun.
   - To force an update (e.g. to see sections on plot), enter any number in the Re-run button in the sidebar.
   
""")




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

st.sidebar.header("Re-run figure to update sections")
section = float(st.sidebar.text_input("Type any number and enter to update section lines", "0"))

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

fig = go.Figure()

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
            colorscale='Greens_r',
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
                      xaxis_scaleanchor='y', xaxis=dict(title='X'), yaxis=dict(title='Y'),height=1000)





    

    
    # Add section lines to plot
    for i, line in enumerate(st.session_state.section_lines):
        x1, y1 = line['start']
        x2, y2 = line['end']
        label = line['label']
        color = line['color']
        fig.add_trace(go.Scatter(
            x=[x1, x2],
            y=[y1, y2],
            mode='lines+text',
            line=dict(color=color, width=3),
            text=[label, ''],
            textposition='top left',
            name=label
        ))
    
    # Display plot
    st.subheader("Click two points to define a section line")
st.plotly_chart(fig, width='stretch', key='main_contour')

if 'section_lines' not in st.session_state:
        st.session_state.section_lines = []
if 'click_points' not in st.session_state:
        st.session_state.click_points = []


    
    # Allow user to input any coordinates
x_click = st.number_input("X coordinate of click", value=0.0)
y_click = st.number_input("Y coordinate of click", value=0.0)
if st.button("Add Click Point"):
    st.session_state.click_points.append((x_click, y_click))
    fig.update_layout(title='Combined Tree Root Influence Elevation Map',
                      xaxis_scaleanchor='y', xaxis=dict(title='X'), yaxis=dict(title='Y'),height=1000)
        
# Show table of click points
if st.session_state.click_points:
    st.subheader("Click Points")
    click_df = pd.DataFrame(st.session_state.click_points, columns=['X', 'Y'])
    st.dataframe(click_df)
    
    # Create section line if two points are clicked

if len(st.session_state.click_points) >= 2:
    start = st.session_state.click_points.pop(0)
    end = st.session_state.click_points.pop(0)
    label = "A-A'"
    color = 'red'
    st.session_state.section_lines = [{
        'label': label,
        'start': start,
        'end': end,
        'color': color
    }]

    
    # Generate section plots
if st.session_state.trees and st.session_state.section_lines:
    # safe to run interpolation and plotting
    
    interp_func = RegularGridInterpolator(
        (y_coords, x_coords),
        combined_elevations,
        bounds_error=False,
        fill_value=np.nan
    )
    
    for line in st.session_state.section_lines:
        x1, y1 = line['start']
        x2, y2 = line['end']
        num_points = 200
        x_line = np.linspace(x1, x2, num_points)
        y_line = np.linspace(y1, y2, num_points)
        points = np.array([y_line, x_line]).T
        elevations = interp_func(points)
        distances = np.sqrt((x_line - x1)**2 + (y_line - y1)**2)
        
        section_fig = go.Figure()
        section_fig.add_trace(go.Scatter(
            x=distances,
            y=elevations,
            mode='lines',
            name=line['label'],
            line=dict(color=line['color'])
        ))
        section_fig.update_layout(
            title=f"Section View: {line['label']}",
            xaxis_title='Distance Along Line (m)',
            yaxis_title='Elevation (m)',
            yaxis_scaleanchor='x',
            height=600
        )

st.plotly_chart(section_fig, width='stretch', key='section_0')
            
    

       
