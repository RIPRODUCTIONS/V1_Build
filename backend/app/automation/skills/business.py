from __future__ import annotations

from typing import Any

from app.automation.registry import skill


@skill('business.prepare_campaign')
async def prepare_campaign(context: dict[str, Any]) -> dict[str, Any]:
    name = (context.get('campaign_name') or 'Untitled').strip()
    channels = context.get('channels') or ['email']
    return {
        **context,
        'campaign': {'name': name, 'channels': channels, 'assets': ['copy.md', 'banner.png']},
    }


@skill('business.launch_campaign')
async def launch_campaign(context: dict[str, Any]) -> dict[str, Any]:
    campaign = context.get('campaign') or {}
    return {**context, 'launched': True, 'launch_id': f'mkt-{campaign.get("name", "untitled")[:8]}'}


@skill('business.collect_metrics')
async def collect_metrics(context: dict[str, Any]) -> dict[str, Any]:
    return {**context, 'metrics': {'sent': 1000, 'open_rate': 0.42, 'ctr': 0.08}}


@skill('business.prepare_outreach')
async def prepare_outreach(context: dict[str, Any]) -> dict[str, Any]:
    leads = context.get('leads') or ['lead@example.com']
    template = context.get('template') or 'hi {{name}}'
    return {**context, 'outreach': {'leads': leads, 'template': template}}


@skill('business.send_outreach')
async def send_outreach(context: dict[str, Any]) -> dict[str, Any]:
    outreach = context.get('outreach') or {}
    sent = len(outreach.get('leads', []))
    return {**context, 'outreach_sent': sent}


@skill('business.ops_daily_briefing')
async def ops_daily_briefing(context: dict[str, Any]) -> dict[str, Any]:
    return {
        **context,
        'briefing': {
            'tasks': ['check metrics', 'review incidents'],
            'summary': 'All systems nominal',
        },
    }
