### Import Libraries
import os

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

### Create a Title
st.title('FDI Outflows in Lebanon: Exploring Relationship to Economic Indicators')


@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    fdi_data = pd.read_csv(os.path.join(base_dir, 'FDI.csv'))
    external_debt_data = pd.read_csv(os.path.join(base_dir, 'External_Debt.csv'))
    exchange_rate_data = pd.read_csv(os.path.join(base_dir, 'Exchange_Rates.csv'))

    fdi_data['Year'] = pd.to_numeric(fdi_data['Year'], errors='coerce')
    external_debt_data['refPeriod'] = pd.to_numeric(external_debt_data['refPeriod'], errors='coerce')
    exchange_rate_data['Year'] = pd.to_numeric(exchange_rate_data['Year'], errors='coerce')

    fdi_outflows = fdi_data[
        fdi_data['Item'].astype(str).str.contains('outflow', case=False, na=False)
    ].copy()

    yearly_outflows = (
        fdi_outflows.groupby('Year', as_index=False)['Value']
        .sum()
        .rename(columns={'Value': 'FDI Outflows'})
    )

    yearly_external_debt = (
        external_debt_data[['refPeriod', 'Value']]
        .rename(columns={'refPeriod': 'Year', 'Value': 'External Debt'})
        .groupby('Year', as_index=False)['External Debt']
        .sum()
    )

    yearly_exchange_rate = (
        exchange_rate_data[['Year', 'Value']]
        .rename(columns={'Value': 'Exchange Rate'})
        .groupby('Year', as_index=False)['Exchange Rate']
        .sum()
    )

    merged_data = yearly_outflows.merge(yearly_external_debt, on='Year', how='outer')
    merged_data = merged_data.merge(yearly_exchange_rate, on='Year', how='outer')
    merged_data = merged_data.sort_values('Year').reset_index(drop=True)
    return merged_data


def make_line_chart(df, y_col, title, tick_interval=1):
    fig = px.line(df, x='Year', y=y_col, markers=True, title=title)
    if tick_interval > 1:
        fig.update_xaxes(
            tickmode='array',
            tickvals=list(range(int(df['Year'].min()), int(df['Year'].max()) + 1, tick_interval)),
            title='Year',
        )
    else:
        fig.update_xaxes(
            tickmode='linear',
            dtick=1,
            title='Year',
        )
    fig.update_layout(
        template='plotly_white',
        xaxis_title='Year',
        yaxis_title=y_col,
        margin=dict(l=20, r=20, t=40, b=20),
        height=350,
    )
    return fig


def make_scatter_chart(df, x_col, y_col, title, add_trend_line=False):
    clean_df = df[['Year', x_col, y_col]].dropna().copy()
    if clean_df.empty:
        return px.scatter(df, x=x_col, y=y_col, title=title)

    fig = px.scatter(
        clean_df,
        x=x_col,
        y=y_col,
        hover_data=['Year'],
        title=title,
        opacity=0.8,
    )

    if add_trend_line and len(clean_df) > 1:
        x_vals = clean_df[x_col].astype(float).to_numpy()
        y_vals = clean_df[y_col].astype(float).to_numpy()
        slope, intercept = np.polyfit(x_vals, y_vals, 1)
        x_min, x_max = float(x_vals.min()), float(x_vals.max())
        y_min = slope * x_min + intercept
        y_max = slope * x_max + intercept
        fig.add_trace(
            px.line(
                pd.DataFrame({x_col: [x_min, x_max], y_col: [y_min, y_max]}),
                x=x_col,
                y=y_col,
            ).data[0]
        )
        fig.data[-1].name = 'Trend Line'
        fig.data[-1].line.color = '#d62728'
        fig.data[-1].line.width = 2

    fig.update_layout(
        template='plotly_white',
        margin=dict(l=20, r=20, t=40, b=20),
        height=350,
        legend_title_text='Series',
        dragmode='zoom',
        hovermode='closest',
        clickmode='event+select',
        xaxis=dict(
            title=x_col,
            fixedrange=False,
            autorange=True,
        ),
        yaxis=dict(
            title=y_col,
            fixedrange=False,
            autorange=True,
        ),
    )
    return fig


data = load_data()
available_years = data['Year'].dropna()
min_year = int(available_years.min())
max_year = int(available_years.max())

st.subheader('Data Range Filter')
start_year, end_year = st.slider(
    'Select year range:',
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),
    step=1,
)

filtered_data = data[(data['Year'] >= start_year) & (data['Year'] <= end_year)].copy()
filtered_data['Year'] = filtered_data['Year'].astype(int)

st.caption(f'This dashboard shows annual values from {start_year} to {end_year} for Lebanon.')

st.subheader('Yearly Trends')
trend_view = st.selectbox(
    'Choose which series to view:',
    ['FDI Outflows', 'External Debt', 'Exchange Rate', 'All Series Side by Side'],
    index=3,
)

if trend_view == 'FDI Outflows':
    st.plotly_chart(make_line_chart(filtered_data, 'FDI Outflows', 'FDI Outflows', show_every_5_years=False), use_container_width=True)
elif trend_view == 'External Debt':
    st.plotly_chart(make_line_chart(filtered_data, 'External Debt', 'External Debt', show_every_5_years=False), use_container_width=True)
elif trend_view == 'Exchange Rate':
    st.plotly_chart(make_line_chart(filtered_data, 'Exchange Rate', 'Exchange Rate', show_every_5_years=False), use_container_width=True)
else:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.plotly_chart(make_line_chart(filtered_data, 'FDI Outflows', 'FDI Outflows', tick_interval=20), use_container_width=True)
    with col2:
        st.plotly_chart(make_line_chart(filtered_data, 'External Debt', 'External Debt', tick_interval=20), use_container_width=True)
    with col3:
        st.plotly_chart(make_line_chart(filtered_data, 'Exchange Rate', 'Exchange Rate', tick_interval=20), use_container_width=True)

st.subheader('Scatter Plots with Trend Lines')
scatter_start_year, scatter_end_year = st.slider(
    'Select scatter plot year range:',
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),
    step=1,
    key='scatter_year_range',
)
scatter_data = data[
    (data['Year'] >= scatter_start_year) & (data['Year'] <= scatter_end_year)
].copy()
scatter_data['Year'] = scatter_data['Year'].astype(int)

scatter_col1, scatter_col2 = st.columns(2)
with scatter_col1:
    debt_trend = st.checkbox('Add trend line for debt comparison', key='debt_trend_checkbox')
    st.plotly_chart(
        make_scatter_chart(
            scatter_data,
            'External Debt',
            'FDI Outflows',
            'FDI Outflows vs External Debt',
            add_trend_line=debt_trend,
        ),
        use_container_width=True,
    )
with scatter_col2:
    exchange_trend = st.checkbox('Add trend line for exchange-rate comparison', key='exchange_trend_checkbox')
    st.plotly_chart(
        make_scatter_chart(
            scatter_data,
            'Exchange Rate',
            'FDI Outflows',
            'FDI Outflows vs Exchange Rate',
            add_trend_line=exchange_trend,
        ),
        use_container_width=True,
    )