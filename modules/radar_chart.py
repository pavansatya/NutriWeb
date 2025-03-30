import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def preprocess_data(data, category_col, nutrient_cols, top_n=10):
    
    results = []
    top_categories = data[category_col].value_counts().nlargest(top_n).index
    
    # Process each category separately
    for category in top_categories:
        category_data = data[data[category_col] == category].copy()
        
        # Scale each nutrient using category's 5th-95th percentiles
        scaled_values = []
        for col in nutrient_cols:
            # Calculate percentiles for this category+nutrient
            low = category_data[col].quantile(0.05)
            high = category_data[col].quantile(0.95)
            
            # Clip and scale
            scaled_col = (category_data[col].clip(low, high) - low) / (high - low)
            scaled_values.append(scaled_col)
        
        # Combine results
        scaled_df = pd.DataFrame(dict(zip(nutrient_cols, scaled_values)))
        scaled_df[category_col] = category
        results.append(scaled_df)
    
    # Combine all categories
    return pd.concat(results).groupby(category_col)[nutrient_cols].mean().reset_index()

def create_radar_chart(categories, values, title):
    fig = go.Figure()
    
    for i, category in enumerate(categories):
        fig.add_trace(go.Scatterpolar(
            r=values.iloc[i].tolist(),
            theta=values.columns,
            fill='toself',
            name=category
        ))

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
    

def get_category_colors(categories):
    color_palette = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
    ]
    return {category: color_palette[i % len(color_palette)] 
            for i, category in enumerate(categories)}


def create_radar_chart_with_dropdown(categories, values, title):
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
    fig.show()