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
MAIN_LINE_WIDTH = 2.0
TREND_LINE_WIDTH = 1.4
DATE_LABEL_LINE_WIDTH = 1.2
DATE_LABEL_COLOR = 'dimgray'
Y_AXIS_PADDING_RATIO = 0.12
MIN_Y_AXIS_PADDING = 0.35


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


def get_weight_axis_limits(raw_weights, line_weights):
    weights = np.concatenate([
        np.asarray(raw_weights, dtype=float),
        np.asarray(line_weights, dtype=float),
    ])
    min_weight = weights.min()
    max_weight = weights.max()
    if min_weight == max_weight:
        return min_weight - 5, max_weight + 5

    padding = max((max_weight - min_weight) * Y_AXIS_PADDING_RATIO, MIN_Y_AXIS_PADDING)
    return min_weight - padding, max_weight + padding


def get_date_label_attr(date_label, attr):
    if isinstance(date_label, dict):
        return date_label[attr]
    return getattr(date_label, attr)


def get_visible_date_labels(date_labels, df: pd.DataFrame):
    if not date_labels:
        return []

    chart_start_date = pd.to_datetime(df['created_at'].iloc[0]).date()
    chart_end_date = pd.to_datetime(df['created_at'].iloc[-1]).date()
    visible_date_labels_by_date = {}

    for date_label in date_labels:
        label_date = pd.to_datetime(get_date_label_attr(date_label, 'label_date')).date()
        if chart_start_date <= label_date <= chart_end_date:
            visible_date_labels_by_date[label_date] = date_label

    return list(visible_date_labels_by_date.values())


def plot_date_labels(ax: Axes, date_labels, df: pd.DataFrame):
    visible_date_labels = get_visible_date_labels(date_labels, df)
    if not visible_date_labels:
        return

    for date_label in visible_date_labels:
        label_date = pd.to_datetime(get_date_label_attr(date_label, 'label_date')).to_pydatetime()
        label = get_date_label_attr(date_label, 'label')
        legend_label = '{}: {}'.format(label_date.strftime('%Y-%m-%d'), label)
        ax.axvline(
            label_date,
            linestyle=':',
            color=DATE_LABEL_COLOR,
            linewidth=DATE_LABEL_LINE_WIDTH,
            label=legend_label,
        )

    legend = ax.legend(
        loc='upper right',
        fontsize=7,
        frameon=False,
        handlelength=0,
        handletextpad=0,
    )
    for handle in legend.legend_handles:
        handle.set_visible(False)


def plot_data(ax: Axes, df: pd.DataFrame, title: str, date_labels=None):
    line_dates, line_weights = get_smoothed_weight_line(df)
    ax.plot(line_dates, line_weights, linewidth=MAIN_LINE_WIDTH)
    ax.set_title(title)
    ax.set_ylim(get_weight_axis_limits(df['weight'], line_weights))

    ax.set_xticks([df['created_at'].iloc[0], df['created_at'].iloc[-1]])

    x = mdates.date2num(pd.to_datetime(df['created_at']).to_numpy())
    y = df['weight']
    m, b = np.polyfit(x, y, 1)
    trend_line = m * x + b
    trend_value = trend_line[-1] - trend_line[0]
    trend_dates = mdates.num2date(x)
    trend_color = 'red' if trend_value >= 0 else 'green'
    ax.plot(trend_dates, trend_line, linestyle='--', color=trend_color, linewidth=TREND_LINE_WIDTH)
    trend_text = f"Trend: {'+' if trend_value >= 0 else ''}{trend_value:.2f}"
    ax.text(0.02, 0.95, trend_text, transform=ax.transAxes, fontsize=8, verticalalignment='top')
    plot_date_labels(ax, date_labels, df)


def create_weight_chart_figure(chart_ranges: list, date_labels=None):
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
        plot_data(ax, chart_df, title, date_labels)

    return fig


def close_weight_chart_figure(fig):
    plt.close(fig)
