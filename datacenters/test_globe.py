import plotly.graph_objects as go
import pandas as pd

# Sample data (replace with your actual dataset)
data = {
    'latitude': [37.7749, 51.5074, -33.8688, 35.6895],
    'longitude': [-122.4194, -0.1278, 151.2093, 139.6917],
    'power': [50, 40, 35, 45],
    'colocation_space': [20000, 15000, 18000, 21000],
    'total_space': [50000, 40000, 45000, 47000]
}
df = pd.DataFrame(data)

fig = go.Figure()

fig.add_trace(go.Scattergeo(
    lon=df['longitude'],
    lat=df['latitude'],
    text=df.apply(lambda row: f"Power: {row['power']} MW<br>Colocation Space: {row['colocation_space']} sqft<br>Total Space: {row['total_space']} sqft", axis=1),
    marker=dict(
        size=10,
        color=df['power'],
        colorscale='Viridis',
        colorbar_title='Power (MW)',
        line=dict(width=0)
    )
))

fig.update_layout(
    title='Geographical Distribution of Data Centres',
    geo=dict(
        showland=True,
        landcolor="rgb(212, 212, 212)",
        projection=dict(
            type='orthographic',
            rotation=dict(lon=-100, lat=40)
        ),
        scope='world',
        showcountries=True
    ),
)

fig.show()
