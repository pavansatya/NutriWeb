import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# def preprocess_data(data, category_col, nutrient_cols, top_n=10):
#     """
#     Preprocesses the data by grouping by category, calculating mean nutrient values,
#     and selecting the top N categories.

#     Args:
#         data (pd.DataFrame): Input data.
#         category_col (str): Name of the column containing categories.
#         nutrient_cols (list): List of nutrient columns to analyze.
#         top_n (int): Number of top categories to select.

#     Returns:
#         pd.DataFrame: Processed data with top categories and scaled nutrient values.
#     """
#     category_nutrition = data.groupby(category_col)[nutrient_cols].mean().reset_index()

#     top_categories = data[category_col].value_counts().nlargest(top_n).index
#     top_category_nutrition = category_nutrition[category_nutrition[category_col].isin(top_categories)].copy()
#     #scaler = MinMaxScaler()
#     #top_category_nutrition[nutrient_cols] = scaler.fit_transform(top_category_nutrition[nutrient_cols])

#     return top_category_nutrition

# def create_radar_chart(categories, values, title):
#     """
#     Creates an interactive radar chart for the given categories and nutrient values.

#     Args:
#         categories (pd.Series): Categories to display on the chart.
#         values (pd.DataFrame): Nutrient values for each category.
#         title (str): Title of the chart.
#     """
#     fig = go.Figure()

#     # Find the maximum value to set the range of the radar chart (remove this later)
#     max_value = values.max().max() * 1.1
    
#     for i, category in enumerate(categories):
#         fig.add_trace(go.Scatterpolar(
#             r=values.iloc[i].tolist(),
#             theta=values.columns,
#             fill='toself',
#             name=category
#         ))

#     # Update layout for better visualization
#     fig.update_layout(
#         polar=dict(
#             radialaxis=dict(
#                 visible=True,
#                 range=[0, max_value]   #change max_value to 1
#             )
#         ),
#         title=title,
#         showlegend=True
#     )


# def create_radar_chart_with_dropdown(categories, values, title):
#     """
#     Creates an interactive radar chart with a dropdown to toggle between categories.

#     Args:
#         categories (pd.Series): Categories to display on the chart.
#         values (pd.DataFrame): Nutrient values for each category.
#         title (str): Title of the chart.
#     """
#     fig = go.Figure()
    
#     # Find the maximum value to set the range of the radar chart (remove this later)
#     max_value = values.max().max() * 1.1

#     for i, category in enumerate(categories):
#         fig.add_trace(go.Scatterpolar(
#             r=values.iloc[i].tolist(),
#             theta=values.columns,
#             fill='toself',
#             name=category,
#             visible=True
#         ))

#     # Create dropdown options
#     dropdown_options = []
#     for i, category in enumerate(categories):
#         dropdown_options.append(
#             dict(
#                 args=[{"visible": [j == i for j in range(len(categories))]}],
#                 label=category,
#                 method="update"
#             )
#         )

#     # Add dropdown to the layout
#     fig.update_layout(
#         updatemenus=[
#             dict(
#                 buttons=dropdown_options,
#                 direction="down",
#                 showactive=True,
#                 x=0.1,
#                 xanchor="left",
#                 y=1.1,
#                 yanchor="top"
#             )
#         ],
#         polar=dict(
#             radialaxis=dict(
#                 visible=True,
#                 range=[0, max_value]   #change max_value to 1
#             )
#         ),
#         title=title,
#         showlegend=True
#     )

#     fig.show()

def preprocess_data(data, category_col, nutrient_cols, top_n=10):
    """Returns unscaled mean values for top categories"""
    category_nutrition = data.groupby(category_col)[nutrient_cols].mean().reset_index()
    top_categories = data[category_col].value_counts().nlargest(top_n).index
    return category_nutrition[category_nutrition[category_col].isin(top_categories)].copy()

def create_nutrition_radar_charts(categories, values, title_prefix=""):
    """
    Creates TWO radar charts:
    1. Energy (kcal) alone
    2. Macronutrients (proteins, carbs, fats, fiber) together
    """
    # Split nutrients
    energy_col = [col for col in values.columns if 'energy' in col.lower()]
    macro_cols = [col for col in values.columns if col not in energy_col]
    
    # Create subplots
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{'type': 'polar'}, {'type': 'polar'}]],
        subplot_titles=("Energy (kcal per 100g)", "Macronutrients (g per 100g)")
    )
    
    # Chart 1: Energy
    max_energy = values[energy_col].max().max() * 1.1
    for i, category in enumerate(categories):
        fig.add_trace(
            go.Scatterpolar(
                r=values[energy_col].iloc[i].tolist(),
                theta=energy_col,
                fill='toself',
                name=category,
                legendgroup=f'group{i}',
                showlegend=True
            ),
            row=1, col=1
        )
    
    # Chart 2: Macronutrients
    max_macro = values[macro_cols].max().max() * 1.1
    for i, category in enumerate(categories):
        fig.add_trace(
            go.Scatterpolar(
                r=values[macro_cols].iloc[i].tolist(),
                theta=macro_cols,
                fill='toself',
                name=category,
                legendgroup=f'group{i}',
                showlegend=False
            ),
            row=1, col=2
        )
    
    # Update layout
    fig.update_layout(
        polar=dict(
            radialaxis=dict(range=[0, max_energy])
        ),
        polar2=dict(
            radialaxis=dict(range=[0, max_macro])
        ),
        title=f"{title_prefix}Nutritional Composition",
        height=500,
        width=1000
    )
    
    fig.show()
    
def create_combined_radar(categories, values):
    """Shows energy as bar and macros as radar"""
    # Normalize only macronutrients (0-1 scale)
    macro_cols = [col for col in values.columns if col != 'energy_100g']
    values[macro_cols] = values[macro_cols].apply(lambda x: x/x.max(), axis=0)
    
    fig = go.Figure()
    for i, category in enumerate(categories):
        fig.add_trace(go.Scatterpolar(
            r=values[macro_cols].iloc[i].tolist(),
            theta=macro_cols,
            fill='toself',
            name=f"{category} (Energy: {values['energy_100g'].iloc[i]:.0f} kcal)",
            customdata=[values['energy_100g'].iloc[i]],
            hovertemplate="<b>%{theta}</b>: %{r:.2f}<br>Energy: %{customdata:.0f} kcal"
        ))
    
    fig.update_layout(
        polar=dict(radialaxis=dict(range=[0, 1])),
        title="Macronutrients (Normalized) with Energy Values"
    )
    fig.show()    