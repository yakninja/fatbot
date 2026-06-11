from datetime import datetime, timedelta

import pandas as pd

from weight_charts import (
    CHART_HEIGHT_INCHES,
    close_weight_chart_figure,
    create_weight_chart_figure,
    get_smoothed_weight_line,
    get_weight_chart_ranges,
)


def weight_df(now, day_offsets):
    return pd.DataFrame({
        'created_at': [now - timedelta(days=days) for days in day_offsets],
        'weight': [70 + index for index in range(len(day_offsets))],
    })


def test_weight_chart_ranges_skip_periods_with_fewer_than_two_points():
    now = datetime(2026, 6, 11, 12)

    chart_ranges = get_weight_chart_ranges(weight_df(now, [364, 200, 0]), now)
    assert [title for title, _ in chart_ranges] == ['Year']

    chart_ranges = get_weight_chart_ranges(weight_df(now, [364, 40, 20, 0]), now)
    assert [title for title, _ in chart_ranges] == ['Month', 'Year']

    chart_ranges = get_weight_chart_ranges(weight_df(now, [364, 20, 3, 0]), now)
    assert [title for title, _ in chart_ranges] == ['Week', 'Month', 'Year']


def test_weight_chart_figure_height_matches_visible_chart_count():
    now = datetime(2026, 6, 11, 12)
    chart_ranges = get_weight_chart_ranges(weight_df(now, [364, 40, 20, 0]), now)

    fig = create_weight_chart_figure(chart_ranges)

    try:
        assert len(fig.axes) == 2
        assert fig.get_size_inches()[1] == CHART_HEIGHT_INCHES * 2
    finally:
        close_weight_chart_figure(fig)


def test_weight_chart_figure_is_not_created_without_visible_ranges():
    now = datetime(2026, 6, 11, 12)

    assert create_weight_chart_figure(get_weight_chart_ranges(weight_df(now, [0]), now)) is None


def test_weight_line_is_smoothed_when_enough_points_are_available():
    now = datetime(2026, 6, 11, 12)
    df = weight_df(now, [4, 3, 2, 0])

    line_dates, line_weights = get_smoothed_weight_line(df)

    assert len(line_dates) > len(df)
    assert len(line_weights) == len(line_dates)
