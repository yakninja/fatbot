from datetime import datetime, timedelta
import os
import tempfile

os.environ.setdefault('MPLCONFIGDIR', os.path.join(tempfile.gettempdir(), 'matplotlib'))
os.environ.setdefault('XDG_CACHE_HOME', tempfile.gettempdir())
import matplotlib
matplotlib.use('Agg')  # non-interactive backend
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from scipy.interpolate import PchipInterpolator

MIN_CHART_POINTS = 2
FIGURE_WIDTH_INCHES = 8
CHART_HEIGHT_INCHES = 2
FIGURE_DPI = 100


def get_weight_chart_ranges(df: pd.DataFrame, current_time: datetime) -> list:
    one_week_ago_datetime = current_time - timedelta(days=7)
    one_month_ago_datetime = current_time - timedelta(days=30)
    one_year_ago_datetime = current_time - timedelta(days=365)

    chart_ranges = [
        ('Week', df[df['created_at'] >= one_week_ago_datetime]),
        ('Month', df[df['created_at'] >= one_month_ago_datetime]),
        ('Year', df[df['created_at'] >= one_year_ago_datetime]),
    ]
    return [
        (title, chart_df)
        for title, chart_df in chart_ranges
        if len(chart_df) >= MIN_CHART_POINTS
    ]


def get_smoothed_weight_line(df: pd.DataFrame):
    dates = pd.to_datetime(df['created_at']).to_numpy()
    x = mdates.date2num(dates)
    y = df['weight'].astype(float).to_numpy()
    unique_x, unique_indices = np.unique(x, return_index=True)

    if len(unique_x) < 3:
        return dates, y

    unique_y = y[unique_indices]
    interpolator = PchipInterpolator(unique_x, unique_y)
    smooth_x = np.linspace(unique_x[0], unique_x[-1], max(100, len(unique_x) * 20))
    smooth_y = interpolator(smooth_x)
    return mdates.num2date(smooth_x), smooth_y


def plot_data(ax: Axes, df: pd.DataFrame, title: str):
    line_dates, line_weights = get_smoothed_weight_line(df)
    ax.plot(line_dates, line_weights)
    ax.set_title(title)
    min_weight = df['weight'].min()
    max_weight = df['weight'].max()
    ax.set_ylim([min_weight if min_weight != max_weight else min_weight - 5,
                 max_weight if min_weight != max_weight else max_weight + 5])

    ax.set_xticks([df['created_at'].iloc[0], df['created_at'].iloc[-1]])

    x = mdates.date2num(pd.to_datetime(df['created_at']).to_numpy())
    y = df['weight']
    m, b = np.polyfit(x, y, 1)
    trend_line = m * x + b
    trend_value = trend_line[-1] - trend_line[0]
    trend_dates = mdates.num2date(x)
    trend_color = 'red' if trend_value >= 0 else 'green'
    ax.plot(trend_dates, trend_line, linestyle='--', color=trend_color)
    trend_text = f"Trend: {'+' if trend_value >= 0 else ''}{trend_value:.2f}"
    ax.text(0.02, 0.95, trend_text, transform=ax.transAxes, fontsize=8, verticalalignment='top')


def create_weight_chart_figure(chart_ranges: list):
    if not chart_ranges:
        return None

    fig, axes = plt.subplots(
        len(chart_ranges),
        1,
        figsize=(FIGURE_WIDTH_INCHES, CHART_HEIGHT_INCHES * len(chart_ranges)),
        dpi=FIGURE_DPI,
        constrained_layout=True,
    )
    if len(chart_ranges) == 1:
        axes = [axes]

    for ax, (title, chart_df) in zip(axes, chart_ranges):
        plot_data(ax, chart_df, title)

    return fig


def close_weight_chart_figure(fig):
    plt.close(fig)
