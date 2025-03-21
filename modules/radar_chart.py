import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import plotly.graph_objects as go

def preprocess_data(data, category_col, nutrient_cols, top_n=10):
    """
    Preprocesses the data by grouping by category, calculating mean nutrient values,
    and selecting the top N categories.

    Args:
        data (pd.DataFrame): Input data.
        category_col (str): Name of the column containing categories.
        nutrient_cols (list): List of nutrient columns to analyze.
        top_n (int): Number of top categories to select.

    Returns:
        pd.DataFrame: Processed data with top categories and scaled nutrient values.
    """
    category_nutrition = data.groupby(category_col)[nutrient_cols].mean().reset_index()

    top_categories = data[category_col].value_counts().nlargest(top_n).index
    top_category_nutrition = category_nutrition[category_nutrition[category_col].isin(top_categories)].copy()
    scaler = MinMaxScaler()
    top_category_nutrition[nutrient_cols] = scaler.fit_transform(top_category_nutrition[nutrient_cols])

    return top_category_nutrition

def create_radar_chart(categories, values, title):
    """
    Creates an interactive radar chart for the given categories and nutrient values.

    Args:
        categories (pd.Series): Categories to display on the chart.
        values (pd.DataFrame): Nutrient values for each category.
        title (str): Title of the chart.
    """
    fig = go.Figure()

    for i, category in enumerate(categories):
        fig.add_trace(go.Scatterpolar(
            r=values.iloc[i].tolist(),
            theta=values.columns,
            fill='toself',
            name=category
        ))

    # Update layout for better visualization
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )
        ),
        title=title,
        showlegend=True
    )


def create_radar_chart_with_dropdown(categories, values, title):
    """
    Creates an interactive radar chart with a dropdown to toggle between categories.

    Args:
        categories (pd.Series): Categories to display on the chart.
        values (pd.DataFrame): Nutrient values for each category.
        title (str): Title of the chart.
    """
    fig = go.Figure()

    for i, category in enumerate(categories):
        fig.add_trace(go.Scatterpolar(
            r=values.iloc[i].tolist(),
            theta=values.columns,
            fill='toself',
            name=category,
            visible=True
        ))

    # Create dropdown options
    dropdown_options = []
    for i, category in enumerate(categories):
        dropdown_options.append(
            dict(
                args=[{"visible": [j == i for j in range(len(categories))]}],
                label=category,
                method="update"
            )
        )

    # Add dropdown to the layout
    fig.update_layout(
        updatemenus=[
            dict(
                buttons=dropdown_options,
                direction="down",
                showactive=True,
                x=0.1,
                xanchor="left",
                y=1.1,
                yanchor="top"
            )
        ],
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )
        ),
        title=title,
        showlegend=True
    )

    fig.show()