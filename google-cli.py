#!/usr/bin/env python3
"""
Acidni Google CLI - Standalone utility for GA4 Admin + Data API operations.
Called by google-helper.ps1 and the @acidni-google chat mode agent.

Usage:
    python google-cli.py list-accounts
    python google-cli.py list-properties
    python google-cli.py list-streams <property_id>
    python google-cli.py get-property <property_id>
    python google-cli.py create-property <display_name> <account_id> [--url <url>]
    python google-cli.py create-stream <property_id> <display_name> <url>
    python google-cli.py run-report <property_id> <start_date> <end_date> [--metrics m1,m2] [--dimensions d1,d2]
    python google-cli.py delete-property <property_id>
    python google-cli.py list-custom-dimensions <property_id>
    python google-cli.py list-custom-metrics <property_id>
    python google-cli.py list-audiences <property_id>

Credentials:
    Loads service account JSON from Azure Key Vault:
      Vault:  kv-terprint-dev
      Secret: ga4-service-account-json
"""

import argparse
import json
import sys
import os


# ---------------------------------------------------------------------------
# Credential loading
# ---------------------------------------------------------------------------

def get_credentials():
    """Load Google service account credentials from Azure Key Vault."""
    from azure.identity import DefaultAzureCredential
    from azure.keyvault.secrets import SecretClient
    from google.oauth2 import service_account

    vault_url = os.environ.get("AZURE_KEY_VAULT_URL", "https://kv-terprint-dev.vault.azure.net")
    secret_name = os.environ.get("GA4_SECRET_NAME", "ga4-service-account-json")

    credential = DefaultAzureCredential()
    kv = SecretClient(vault_url=vault_url, credential=credential)
    secret = kv.get_secret(secret_name)
    sa_info = json.loads(secret.value)

    creds = service_account.Credentials.from_service_account_info(
        sa_info,
        scopes=[
            "https://www.googleapis.com/auth/analytics.readonly",
            "https://www.googleapis.com/auth/analytics.edit",
        ],
    )
    return creds


def get_admin_client(creds):
    from google.analytics.admin import AnalyticsAdminServiceClient
    return AnalyticsAdminServiceClient(credentials=creds)


def get_data_client(creds):
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    return BetaAnalyticsDataClient(credentials=creds)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_list_accounts(args):
    """List all GA4 accounts the service account has access to."""
    creds = get_credentials()
    client = get_admin_client(creds)
    accounts = list(client.list_accounts())
    result = []
    for a in accounts:
        result.append({
            "name": a.name,
            "displayName": a.display_name,
            "createTime": str(a.create_time) if a.create_time else None,
            "updateTime": str(a.update_time) if a.update_time else None,
            "regionCode": a.region_code or "",
        })
    print(json.dumps(result, indent=2))


def cmd_list_properties(args):
    """List all GA4 properties across all accounts."""
    creds = get_credentials()
    client = get_admin_client(creds)

    accounts = list(client.list_accounts())
    all_props = []
    for acct in accounts:
        props = list(client.list_properties(
            request={"filter": f"parent:{acct.name}"}
        ))
        for p in props:
            all_props.append({
                "name": p.name,
                "displayName": p.display_name,
                "propertyType": str(p.property_type) if p.property_type else "",
                "timeZone": p.time_zone or "",
                "currencyCode": p.currency_code or "",
                "industryCategory": str(p.industry_category) if p.industry_category else "",
                "createTime": str(p.create_time) if p.create_time else None,
                "parent": p.parent or "",
                "account": acct.display_name,
            })
    print(json.dumps(all_props, indent=2))


def cmd_get_property(args):
    """Get details for a specific property."""
    creds = get_credentials()
    client = get_admin_client(creds)
    prop_name = args.property_id
    if not prop_name.startswith("properties/"):
        prop_name = f"properties/{prop_name}"
    p = client.get_property(name=prop_name)
    result = {
        "name": p.name,
        "displayName": p.display_name,
        "propertyType": str(p.property_type) if p.property_type else "",
        "timeZone": p.time_zone or "",
        "currencyCode": p.currency_code or "",
        "industryCategory": str(p.industry_category) if p.industry_category else "",
        "createTime": str(p.create_time) if p.create_time else None,
        "parent": p.parent or "",
    }
    print(json.dumps(result, indent=2))


def cmd_list_streams(args):
    """List data streams for a property."""
    creds = get_credentials()
    client = get_admin_client(creds)
    prop_name = args.property_id
    if not prop_name.startswith("properties/"):
        prop_name = f"properties/{prop_name}"
    streams = list(client.list_data_streams(parent=prop_name))
    result = []
    for s in streams:
        entry = {
            "name": s.name,
            "displayName": s.display_name,
            "type": str(s.type_),
        }
        if s.web_stream_data:
            entry["measurementId"] = s.web_stream_data.measurement_id or ""
            entry["defaultUri"] = s.web_stream_data.default_uri or ""
            entry["firebaseAppId"] = s.web_stream_data.firebase_app_id or ""
        result.append(entry)
    print(json.dumps(result, indent=2))


def cmd_create_property(args):
    """Create a new GA4 property."""
    from google.analytics.admin_v1alpha.types import Property, IndustryCategory, DataStream

    creds = get_credentials()
    client = get_admin_client(creds)

    account_name = args.account_id
    if not account_name.startswith("accounts/"):
        account_name = f"accounts/{account_name}"

    prop = Property(
        display_name=args.display_name,
        parent=account_name,
        time_zone="America/New_York",
        currency_code="USD",
        industry_category=IndustryCategory.TECHNOLOGY,
    )
    created = client.create_property(property=prop)

    result = {
        "name": created.name,
        "displayName": created.display_name,
        "createTime": str(created.create_time) if created.create_time else None,
    }

    # Optionally create a web data stream
    if args.url:
        stream = DataStream(
            display_name=f"{args.display_name} Web",
            type_=DataStream.DataStreamType.WEB_DATA_STREAM,
            web_stream_data=DataStream.WebStreamData(default_uri=args.url),
        )
        created_stream = client.create_data_stream(
            parent=created.name, data_stream=stream
        )
        result["stream"] = {
            "name": created_stream.name,
            "measurementId": created_stream.web_stream_data.measurement_id,
            "defaultUri": created_stream.web_stream_data.default_uri,
        }

    print(json.dumps(result, indent=2))


def cmd_create_stream(args):
    """Create a web data stream for an existing property."""
    from google.analytics.admin_v1alpha.types import DataStream

    creds = get_credentials()
    client = get_admin_client(creds)

    prop_name = args.property_id
    if not prop_name.startswith("properties/"):
        prop_name = f"properties/{prop_name}"

    stream = DataStream(
        display_name=args.display_name,
        type_=DataStream.DataStreamType.WEB_DATA_STREAM,
        web_stream_data=DataStream.WebStreamData(default_uri=args.url),
    )
    created = client.create_data_stream(parent=prop_name, data_stream=stream)

    result = {
        "name": created.name,
        "displayName": created.display_name,
        "measurementId": created.web_stream_data.measurement_id,
        "defaultUri": created.web_stream_data.default_uri,
    }
    print(json.dumps(result, indent=2))


def cmd_delete_property(args):
    """Delete (trash) a GA4 property."""
    creds = get_credentials()
    client = get_admin_client(creds)
    prop_name = args.property_id
    if not prop_name.startswith("properties/"):
        prop_name = f"properties/{prop_name}"
    client.delete_property(name=prop_name)
    print(json.dumps({"deleted": prop_name}))


def cmd_run_report(args):
    """Run a GA4 data report."""
    from google.analytics.data_v1beta.types import (
        RunReportRequest,
        DateRange,
        Dimension,
        Metric,
    )

    creds = get_credentials()
    client = get_data_client(creds)

    prop_name = args.property_id
    if not prop_name.startswith("properties/"):
        prop_name = f"properties/{prop_name}"

    metrics_list = (args.metrics or "activeUsers,sessions").split(",")
    dims_list = args.dimensions.split(",") if args.dimensions else []

    request = RunReportRequest(
        property=prop_name,
        date_ranges=[DateRange(start_date=args.start_date, end_date=args.end_date)],
        metrics=[Metric(name=m.strip()) for m in metrics_list],
        dimensions=[Dimension(name=d.strip()) for d in dims_list] if dims_list else [],
    )
    response = client.run_report(request)

    rows = []
    for row in response.rows:
        entry = {}
        for i, dim in enumerate(response.dimension_headers):
            entry[dim.name] = row.dimension_values[i].value
        for i, met in enumerate(response.metric_headers):
            entry[met.name] = row.metric_values[i].value
        rows.append(entry)

    result = {
        "property": prop_name,
        "dateRange": {"startDate": args.start_date, "endDate": args.end_date},
        "rowCount": response.row_count,
        "rows": rows,
    }
    print(json.dumps(result, indent=2))


def cmd_list_custom_dimensions(args):
    """List custom dimensions for a property."""
    creds = get_credentials()
    client = get_admin_client(creds)
    prop_name = args.property_id
    if not prop_name.startswith("properties/"):
        prop_name = f"properties/{prop_name}"
    dims = list(client.list_custom_dimensions(parent=prop_name))
    result = []
    for d in dims:
        result.append({
            "name": d.name,
            "parameterName": d.parameter_name,
            "displayName": d.display_name,
            "description": d.description or "",
            "scope": str(d.scope),
        })
    print(json.dumps(result, indent=2))


def cmd_list_custom_metrics(args):
    """List custom metrics for a property."""
    creds = get_credentials()
    client = get_admin_client(creds)
    prop_name = args.property_id
    if not prop_name.startswith("properties/"):
        prop_name = f"properties/{prop_name}"
    mets = list(client.list_custom_metrics(parent=prop_name))
    result = []
    for m in mets:
        result.append({
            "name": m.name,
            "parameterName": m.parameter_name,
            "displayName": m.display_name,
            "description": m.description or "",
            "scope": str(m.scope),
            "measurementUnit": str(m.measurement_unit),
        })
    print(json.dumps(result, indent=2))


def cmd_list_audiences(args):
    """List audiences for a property."""
    creds = get_credentials()
    client = get_admin_client(creds)
    prop_name = args.property_id
    if not prop_name.startswith("properties/"):
        prop_name = f"properties/{prop_name}"
    audiences = list(client.list_audiences(parent=prop_name))
    result = []
    for a in audiences:
        result.append({
            "name": a.name,
            "displayName": a.display_name,
            "description": a.description or "",
            "membershipDurationDays": a.membership_duration_days,
        })
    print(json.dumps(result, indent=2))


# ---------------------------------------------------------------------------
# CLI parser
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Acidni Google CLI - GA4 Admin & Data API operations"
    )
    sub = parser.add_subparsers(dest="command", help="Command to execute")

    sub.add_parser("list-accounts", help="List all GA4 accounts")
    sub.add_parser("list-properties", help="List all GA4 properties")

    p = sub.add_parser("get-property", help="Get property details")
    p.add_argument("property_id", help="Property ID (e.g. 123456789)")

    p = sub.add_parser("list-streams", help="List data streams for a property")
    p.add_argument("property_id", help="Property ID")

    p = sub.add_parser("create-property", help="Create a new GA4 property")
    p.add_argument("display_name", help="Display name for the property")
    p.add_argument("account_id", help="Account ID (e.g. 101587418)")
    p.add_argument("--url", help="URL to auto-create web data stream", default=None)

    p = sub.add_parser("create-stream", help="Create a web data stream")
    p.add_argument("property_id", help="Property ID")
    p.add_argument("display_name", help="Display name for the stream")
    p.add_argument("url", help="Default URI for the stream")

    p = sub.add_parser("delete-property", help="Delete (trash) a GA4 property")
    p.add_argument("property_id", help="Property ID")

    p = sub.add_parser("run-report", help="Run a GA4 data report")
    p.add_argument("property_id", help="Property ID")
    p.add_argument("start_date", help="Start date (YYYY-MM-DD or 7daysAgo)")
    p.add_argument("end_date", help="End date (YYYY-MM-DD or today)")
    p.add_argument("--metrics", help="Comma-separated metrics", default="activeUsers,sessions")
    p.add_argument("--dimensions", help="Comma-separated dimensions", default=None)

    p = sub.add_parser("list-custom-dimensions", help="List custom dimensions")
    p.add_argument("property_id", help="Property ID")

    p = sub.add_parser("list-custom-metrics", help="List custom metrics")
    p.add_argument("property_id", help="Property ID")

    p = sub.add_parser("list-audiences", help="List audiences")
    p.add_argument("property_id", help="Property ID")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    cmd_map = {
        "list-accounts": cmd_list_accounts,
        "list-properties": cmd_list_properties,
        "get-property": cmd_get_property,
        "list-streams": cmd_list_streams,
        "create-property": cmd_create_property,
        "create-stream": cmd_create_stream,
        "delete-property": cmd_delete_property,
        "run-report": cmd_run_report,
        "list-custom-dimensions": cmd_list_custom_dimensions,
        "list-custom-metrics": cmd_list_custom_metrics,
        "list-audiences": cmd_list_audiences,
    }

    try:
        cmd_map[args.command](args)
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
