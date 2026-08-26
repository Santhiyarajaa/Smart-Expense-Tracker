"""
utils.py

Shared helper functions for date-range calculations, spending
insights, budget percentage math, and report data preparation.
Keeping this logic here avoids duplicating it across views.py.
"""
from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone

from .models import Budget, Expense


def get_today():
    return timezone.localdate()


def get_week_range(reference_date=None):
    """Return (start, end) dates for the Mon-Sun week containing reference_date."""
    reference_date = reference_date or get_today()
    start = reference_date - timedelta(days=reference_date.weekday())
    end = start + timedelta(days=6)
    return start, end


def get_month_range(reference_date=None):
    """Return (start, end) dates for the calendar month containing reference_date."""
    reference_date = reference_date or get_today()
    start = reference_date.replace(day=1)
    if start.month == 12:
        next_month_start = start.replace(year=start.year + 1, month=1, day=1)
    else:
        next_month_start = start.replace(month=start.month + 1, day=1)
    end = next_month_start - timedelta(days=1)
    return start, end


def get_previous_month(reference_date=None):
    """Return (year, month) tuple for the month before reference_date's month."""
    reference_date = reference_date or get_today()
    first_of_this_month = reference_date.replace(day=1)
    last_of_prev_month = first_of_this_month - timedelta(days=1)
    return last_of_prev_month.year, last_of_prev_month.month


def sum_expenses(queryset):
    """Return the decimal sum of `amount` for a queryset (0 if empty)."""
    total = queryset.aggregate(total=Sum('amount'))['total']
    return total or 0


def get_dashboard_summary(user):
    """Compute today's / week's / month's / total spending for a user."""
    today = get_today()
    week_start, week_end = get_week_range(today)
    month_start, month_end = get_month_range(today)

    base_qs = Expense.objects.filter(user=user)

    today_total = sum_expenses(base_qs.filter(date=today))
    week_total = sum_expenses(base_qs.filter(date__gte=week_start, date__lte=week_end))
    month_total = sum_expenses(base_qs.filter(date__gte=month_start, date__lte=month_end))
    overall_total = sum_expenses(base_qs)

    return {
        'today_total': today_total,
        'week_total': week_total,
        'month_total': month_total,
        'overall_total': overall_total,
    }


def get_category_breakdown(user, start_date=None, end_date=None):
    """Return a list of {category, total} dicts for charting, for a date range."""
    qs = Expense.objects.filter(user=user)
    if start_date:
        qs = qs.filter(date__gte=start_date)
    if end_date:
        qs = qs.filter(date__lte=end_date)

    breakdown = (
        qs.values('category')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )
    return list(breakdown)


def get_daily_trend(user, start_date, end_date):
    """Return a list of {date, total} dicts for each day in the given range."""
    qs = Expense.objects.filter(user=user, date__gte=start_date, date__lte=end_date)
    totals_by_date = {
        row['date']: row['total']
        for row in qs.values('date').annotate(total=Sum('amount'))
    }

    trend = []
    current = start_date
    while current <= end_date:
        trend.append({'date': current, 'total': totals_by_date.get(current, 0)})
        current += timedelta(days=1)
    return trend


def get_budget_status(user, reference_date=None):
    """
    Compute the current month's budget status for a user:
    monthly_budget, current_spending, remaining, percentage_used,
    plus warning flags.
    """
    reference_date = reference_date or get_today()
    month_start, month_end = get_month_range(reference_date)

    budget = Budget.objects.filter(
        user=user, month=reference_date.month, year=reference_date.year
    ).first()

    current_spending = sum_expenses(
        Expense.objects.filter(user=user, date__gte=month_start, date__lte=month_end)
    )

    if budget:
        monthly_budget = budget.monthly_budget
        remaining = monthly_budget - current_spending
        percentage_used = round((current_spending / monthly_budget) * 100, 1) if monthly_budget else 0
    else:
        monthly_budget = None
        remaining = None
        percentage_used = 0

    is_warning = bool(budget) and percentage_used >= 80 and percentage_used < 100
    is_exceeded = bool(budget) and percentage_used >= 100
    # Cap the value used for progress-bar width so the bar never visually
    # overflows its container, while percentage_used above still holds the
    # real (possibly >100) figure for display in text.
    display_percentage = min(percentage_used, 100) if budget else 0

    return {
        'budget': budget,
        'monthly_budget': monthly_budget,
        'current_spending': current_spending,
        'remaining': remaining,
        'percentage_used': percentage_used,
        'display_percentage': display_percentage,
        'is_warning': is_warning,
        'is_exceeded': is_exceeded,
        'is_within_budget': bool(budget) and percentage_used < 80,
    }


def get_spending_insights(user, reference_date=None):
    """
    Generate a short, non-repetitive list of human-readable spending
    insights using plain Python/Django ORM logic (NO external AI APIs).

    Produces at most:
      1. Highest spending category (with its amount, combined in one line)
      2. Total monthly spending
      3. Budget usage percentage (if a budget is set)
      4. Remaining budget (if a budget is set)
      5. Month-over-month spending change (only if last month has data)
    """
    reference_date = reference_date or get_today()
    month_start, month_end = get_month_range(reference_date)

    insights = []

    category_breakdown = get_category_breakdown(user, month_start, month_end)
    month_total = sum_expenses(
        Expense.objects.filter(user=user, date__gte=month_start, date__lte=month_end)
    )

    # 1. Highest spending category + amount, combined into a single insight.
    if category_breakdown:
        top_category = category_breakdown[0]
        insights.append(
            f"💡 {top_category['category']} is your highest spending category "
            f"this month at ₹{top_category['total']:.2f}."
        )

    # 2. Total monthly spending.
    if month_total:
        insights.append(f"💡 Your total spending this month is ₹{month_total:.2f}.")

    # 3 & 4. Budget usage and remaining amount (only if a budget exists).
    budget_status = get_budget_status(user, reference_date)
    if budget_status['budget']:
        insights.append(
            f"💡 You have used {min(budget_status['percentage_used'], 999):.0f}% "
            f"of your monthly budget."
        )
        if budget_status['remaining'] >= 0:
            insights.append(
                f"💡 You have ₹{budget_status['remaining']:.2f} remaining from your monthly budget."
            )
        else:
            insights.append(
                f"🚨 You have exceeded your monthly budget by ₹{-budget_status['remaining']:.2f}."
            )

    # 5. Month-over-month overall spending comparison (skip if no prior data).
    prev_year, prev_month = get_previous_month(reference_date)
    prev_month_start, prev_month_end = get_month_range(
        reference_date.replace(year=prev_year, month=prev_month, day=1)
    )
    prev_month_total = sum_expenses(
        Expense.objects.filter(user=user, date__gte=prev_month_start, date__lte=prev_month_end)
    )

    if prev_month_total and month_total:
        change_pct = ((month_total - prev_month_total) / prev_month_total) * 100
        if change_pct > 0.5:
            insights.append(
                f"📈 Your spending increased by {change_pct:.0f}% compared with last month."
            )
        elif change_pct < -0.5:
            insights.append(
                f"📉 Your spending decreased by {abs(change_pct):.0f}% compared with last month."
            )
        # If change is negligible (~0%), we simply omit the comparison
        # insight to avoid a meaningless "0% change" message.

    if not insights:
        insights.append("💡 Add some expenses this month to start seeing personalized insights.")

    return insights
