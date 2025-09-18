
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# Simulated tree data (replace with actual data loading if needed)
tree_df = pd.DataFrame({
    'Category': ['Oak', 'Pine', 'Maple', 'Birch', 'Elm'],
    'Mature Height': [20, 25, 18, 15, 22],
    'Coniferous': [False, True, False, False, False],
    'Water Demand': ['Medium', 'High', 'Low', 'Medium', 'High']
})

tree_graph_df = pd.DataFrame({
    'Soil volume potential': ['High'] * 5,
    'Coniferous': [False, True, False, False, False],
    'Water Demand': ['Medium', 'High', 'Low', 'Medium', 'High'],
    'Depth Factor': [1.0, 1.2, 0.8, 0.9, 1.1],
    'Spread Factor': [1.5, 2.0, 1.2, 1.3, 1.6]
})

# UI inputs
st.title("Tree Root Influence Contour Plot")

selected_species = st.selectbox("Select Tree Species", tree_df['Category'].unique())
height = st.number_input("Tree Height (m)", min_value=0.0, step=0.1)
X_coord = st.number_input("Tree X Coordinate", value=50.0)
Y_coord = st.number_input("Tree Y Coordinate", value=50.0)
FFL = st.number_input("Finished Floor Level (FFL) (m)", value=13.0)
min_depth = st.number_input("Minimum Depth (m)", value=1.0)

if st.button("Generate Contour Plot"):
    initial_elevation = FFL - min_depth

    # Create grid
    x_coords = np.linspace(X_coord - 30, X_coord + 30, 200)
    y_coords = np.linspace(Y_coord - 30, Y_coord + 30, 200)
    X, Y = np.meshgrid(x_coords, y_coords)
    combined_elevations = np.full(X.shape, initial_elevation)

    # Get tree parameters
    tree_info = tree_df[tree_df['Category'] == selected_species].iloc[0]
    mature_height = tree_info['Mature Height']
    is_coniferous = tree_info['Coniferous']
    water_demand = tree_info['Water Demand']

    params_row = tree_graph_df[
        (tree_graph_df['Soil volume potential'] == 'High') &
        (tree_graph_df['Coniferous'] == is_coniferous) &
        (tree_graph_df['Water Demand'] == water_demand)
    ]
    if params_row.empty:
        st.error("No parameters found for selected tree.")
    else:
        params = params_row.iloc[0]
        depth_factor = params['Depth Factor']
        spread_factor = params['Spread Factor']
        max_radius = mature_height * spread_factor
        max_depth = -height * depth_factor

        def cone_func(r):
            if r > max_radius:
                return 0.0
            return max_depth * (1 - r / max_radius)

        radial_distances = np.sqrt((X - X_coord)**2 + (Y - Y_coord)**2)
        current_tree_depths = np.vectorize(cone_func)(radial_distances)
        current_tree_elevations = FFL + current_tree_depths
        combined_elevations = np.minimum(combined_elevations, current_tree_elevations)

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
        fig.update_layout(title='Tree Root Influence Elevation Map')
        st.plotly_chart(fig)
