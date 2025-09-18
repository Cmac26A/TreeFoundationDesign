
# Tree Root Influence Design Tool

This Streamlit app models the influence of tree roots on building foundations using contour plots.

## Features
- Input tree data (location, elevation, species, removal status)
- Load species parameters and depth functions from Excel files
- Generate contour plots showing root influence

## Setup Instructions
1. Clone this repository or download the files.
2. Ensure you have Python 3 installed.
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run the app:
   ```
   streamlit run app.py
   ```

## Files
- `app.py`: Main Streamlit application
- `Tree_data.xlsx`: Tree species parameters
- `Tree_linegraphs.xlsx`: Depth function parameters
- `requirements.txt`: Python dependencies

## Notes
- Designed for engineers to use without coding knowledge.
- Future enhancements may include AI-based tree detection and elevation modeling.
