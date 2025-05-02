import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def preprocess_data(data, category_col, nutrient_cols, top_n=10):
    """
    Preprocesses nutrient data for radar chart visualization by scaling values and aggregating by category.

    Parameters:
        data (pd.DataFrame): The input DataFrame containing nutrient and category data.
        category_col (str): The column name representing food categories.
        nutrient_cols (list): A list of column names representing nutritional attributes.
        top_n (int): The number of top categories (by frequency) to include.

    Returns:
        pd.DataFrame: A DataFrame with average scaled nutrient values per top category.
    """
    results = []
    top_categories = data[category_col].value_counts().nlargest(top_n).index

    # Step 1: Compute global 5th and 95th percentiles for each nutrient
    global_low = {col: data[col].quantile(0.05) for col in nutrient_cols}
    global_high = {col: data[col].quantile(0.95) for col in nutrient_cols}

    # Step 2: Clip and scale globally
    clipped_scaled_data = pd.DataFrame()
    for col in nutrient_cols:
        low = global_low[col]
        high = global_high[col]
        clipped_col = data[col].clip(low, high)
        scaled_col = (clipped_col - low) / (high - low)
        clipped_scaled_data[col] = scaled_col

    # Step 3: Add category column back
    clipped_scaled_data[category_col] = data[category_col]

    # Step 4: Filter to top N categories and group by category
    filtered_data = clipped_scaled_data[clipped_scaled_data[category_col].isin(top_categories)]
    return filtered_data.groupby(category_col)[nutrient_cols].mean().reset_index()


def get_category_colors(categories):
    """
    Assigns a distinct color to each category from a predefined color palette.

    Parameters:
        categories (list): List of category names.

    Returns:
        dict: A mapping of category names to their assigned color hex codes.
    """
    color_palette = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
    ]
    return {category: color_palette[i % len(color_palette)] 
            for i, category in enumerate(categories)}


def create_radar_chart_with_dropdown(categories, values, title):
    """
    Creates an interactive radar chart with a dropdown menu to view individual category plots.

    Parameters:
        categories (list): List of category names to include in the dropdown.
        values (pd.DataFrame): DataFrame with rows for categories and columns for nutrient values.
        title (str): Title of the radar chart.

    Returns:
        go.Figure: A Plotly figure object with interactive dropdown-enabled radar chart.
    """
    fig = go.Figure()
    color_map = get_category_colors(categories)  
    
    
    for i, category in enumerate(categories):
        fig.add_trace(go.Scatterpolar(
            r=values.iloc[i].tolist(),
            theta=values.columns,
            fill='toself',
            name=category,
            line=dict(color=color_map[category]),  
            visible=True
        ))
    
    
    dropdown_options = []
    for i, category in enumerate(categories):
        dropdown_options.append(
            dict(
                args=[{"visible": [j == i for j in range(len(categories))],
                      "title": f"{title} - {category}"}],
                label=category,
                method="update"
            )
        )
    
    
    fig.update_layout(
        updatemenus=[dict(
            buttons=dropdown_options,
            direction="down",
            showactive=True,
            x=0.1,
            xanchor="left",
            y=1.15,
            yanchor="top"
        )],
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 1])
        ),
        title=title
    )
    return fig