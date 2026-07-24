"""
Custom admin dashboard with aggregate statistics and charts.

Monkey-patches the default ``admin.site.index`` view so that visiting
``/admin/`` renders a dashboard (stats cards + Chart.js charts + recent
activity tables) above the standard app list.

All heavy lifting (aggregations) happens here so the template stays
presentational.
"""
import json
from datetime import timedelta

from django.contrib import admin
from django.db.models import Avg, Count
from django.utils import timezone

from accounts.models import User
from api.models import Appointment, Article, Prediction, Vote


def _pct_change(current, previous):
    """Return % change from previous to current. None if previous == 0."""
    if not previous:
        return None
    return round(((current - previous) / previous) * 100, 1)


def _build_dashboard_context():
    """Compute every statistic displayed on the admin dashboard."""
    now          = timezone.now()
    today        = now.date()
    week_ago     = today - timedelta(days=7)
    two_weeks    = today - timedelta(days=14)

    # ── Top-level counts ─────────────────────────────────────────────
    total_users        = User.objects.count()
    total_patients     = User.objects.filter(role='patient').count()
    total_doctors      = User.objects.filter(role='doctor').count()
    total_predictions  = Prediction.objects.count()
    total_appointments = Appointment.objects.count()
    total_articles     = Article.objects.count()
    total_votes        = Vote.objects.count()

    # ── Week-over-week deltas ────────────────────────────────────────
    preds_this_week = Prediction.objects.filter(created_at__date__gte=week_ago).count()
    preds_prev_week = Prediction.objects.filter(
        created_at__date__gte=two_weeks, created_at__date__lt=week_ago
    ).count()
    preds_delta = _pct_change(preds_this_week, preds_prev_week)

    users_this_week = User.objects.filter(date_joined__date__gte=week_ago).count()
    users_prev_week = User.objects.filter(
        date_joined__date__gte=two_weeks, date_joined__date__lt=week_ago
    ).count()
    users_delta = _pct_change(users_this_week, users_prev_week)

    # ── Prediction breakdown ─────────────────────────────────────────
    high_risk     = Prediction.objects.filter(prediction=True).count()
    low_risk      = Prediction.objects.filter(prediction=False).count()
    high_risk_pct = (high_risk / total_predictions * 100) if total_predictions else 0
    avg_prob      = Prediction.objects.aggregate(avg=Avg('probability'))['avg'] or 0

    # ── Appointment breakdown ────────────────────────────────────────
    pending_ap      = Appointment.objects.filter(status='pending').count()
    confirmed_ap    = Appointment.objects.filter(status='confirmed').count()
    cancelled_ap    = Appointment.objects.filter(status='cancelled').count()
    decided_ap      = confirmed_ap + cancelled_ap
    confirm_rate    = (confirmed_ap / decided_ap * 100) if decided_ap else 0

    # ── Vote breakdown ───────────────────────────────────────────────
    upvotes     = Vote.objects.filter(direction=1).count()
    downvotes   = Vote.objects.filter(direction=-1).count()
    upvote_rate = (upvotes / total_votes * 100) if total_votes else 0

    # ── Time series: predictions per day (last 30 days) ──────────────
    labels_30d  = []
    values_30d  = []
    for i in range(29, -1, -1):
        day   = (now - timedelta(days=i)).date()
        count = Prediction.objects.filter(created_at__date=day).count()
        labels_30d.append(day.strftime('%d/%m'))
        values_30d.append(count)

    # ── Top 5 doctors by number of appointments ──────────────────────
    top_doctors = (
        User.objects.filter(role='doctor')
        .annotate(n=Count('doctor_appointments'))
        .order_by('-n')[:5]
    )
    top_doctors_labels = [d.full_name or d.username for d in top_doctors]
    top_doctors_values = [d.n for d in top_doctors]

    # ── Recent activity (5 most recent) ──────────────────────────────
    recent_predictions  = list(Prediction.objects.select_related('user')[:5])
    recent_appointments = list(
        Appointment.objects.select_related('patient', 'doctor')[:5]
    )

    return {
        'stats': {
            'total_users':        total_users,
            'total_patients':     total_patients,
            'total_doctors':      total_doctors,
            'total_predictions':  total_predictions,
            'total_appointments': total_appointments,
            'total_articles':     total_articles,
            'total_votes':        total_votes,
            'high_risk':          high_risk,
            'low_risk':           low_risk,
            'high_risk_pct':      round(high_risk_pct, 1),
            'avg_prob':           round(avg_prob * 100, 1),
            'pending_ap':         pending_ap,
            'confirmed_ap':       confirmed_ap,
            'cancelled_ap':       cancelled_ap,
            'confirm_rate':       round(confirm_rate, 1),
            'upvotes':            upvotes,
            'downvotes':          downvotes,
            'upvote_rate':        round(upvote_rate, 1),
            'preds_this_week':    preds_this_week,
            'preds_delta':        preds_delta,
            'users_this_week':    users_this_week,
            'users_delta':        users_delta,
        },
        # All chart data serialised to JSON so the template can embed it
        # directly without worrying about Python repr quirks.
        'charts_json': json.dumps({
            'predictions_per_day_labels': labels_30d,
            'predictions_per_day_values': values_30d,
            'risk_values':                [high_risk, low_risk],
            'appointment_status_values':  [pending_ap, confirmed_ap, cancelled_ap],
            'users_by_role_values':       [total_patients, total_doctors],
            'top_doctors_labels':         top_doctors_labels,
            'top_doctors_values':         top_doctors_values,
        }),
        'recent_predictions':  recent_predictions,
        'recent_appointments': recent_appointments,
    }


# ─── Monkey-patch admin index ────────────────────────────────────────
_original_index = admin.site.index


def _dashboard_index(request, extra_context=None):
    extra_context = extra_context or {}
    extra_context['dashboard'] = _build_dashboard_context()
    return _original_index(request, extra_context=extra_context)


admin.site.index        = _dashboard_index
admin.site.site_header  = 'Smart Healthcare — Administration'
admin.site.site_title   = 'Smart Healthcare Admin'
admin.site.index_title  = 'Dashboard'
admin.site.site_url     = 'http://localhost:5173'
