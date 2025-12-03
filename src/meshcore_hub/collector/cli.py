"""CLI for the Collector component."""

import click

from meshcore_hub.common.logging import configure_logging


@click.command("collector")
@click.option(
    "--mqtt-host",
    type=str,
    default="localhost",
    envvar="MQTT_HOST",
    help="MQTT broker host",
)
@click.option(
    "--mqtt-port",
    type=int,
    default=1883,
    envvar="MQTT_PORT",
    help="MQTT broker port",
)
@click.option(
    "--mqtt-username",
    type=str,
    default=None,
    envvar="MQTT_USERNAME",
    help="MQTT username",
)
@click.option(
    "--mqtt-password",
    type=str,
    default=None,
    envvar="MQTT_PASSWORD",
    help="MQTT password",
)
@click.option(
    "--prefix",
    type=str,
    default="meshcore",
    envvar="MQTT_PREFIX",
    help="MQTT topic prefix",
)
@click.option(
    "--database-url",
    type=str,
    default="sqlite:///./meshcore.db",
    envvar="DATABASE_URL",
    help="Database connection URL",
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    default="INFO",
    envvar="LOG_LEVEL",
    help="Log level",
)
def collector(
    mqtt_host: str,
    mqtt_port: int,
    mqtt_username: str | None,
    mqtt_password: str | None,
    prefix: str,
    database_url: str,
    log_level: str,
) -> None:
    """Run the collector component.

    The collector subscribes to MQTT broker and stores
    MeshCore events in the database for later retrieval.

    Events stored include:
    - Node advertisements
    - Contact and channel messages
    - Trace path data
    - Telemetry responses
    - Informational events (battery, status, etc.)

    Webhooks can be configured via environment variables:
    - WEBHOOK_ADVERTISEMENT_URL: Webhook for advertisement events
    - WEBHOOK_MESSAGE_URL: Webhook for all message events
    - WEBHOOK_CHANNEL_MESSAGE_URL: Override for channel messages
    - WEBHOOK_DIRECT_MESSAGE_URL: Override for direct messages
    """
    configure_logging(level=log_level)

    click.echo("Starting MeshCore Collector")
    click.echo(f"MQTT: {mqtt_host}:{mqtt_port} (prefix: {prefix})")
    click.echo(f"Database: {database_url}")

    # Load webhook configuration from settings
    from meshcore_hub.common.config import get_collector_settings
    from meshcore_hub.collector.webhook import (
        WebhookDispatcher,
        create_webhooks_from_settings,
    )

    settings = get_collector_settings()
    webhooks = create_webhooks_from_settings(settings)
    webhook_dispatcher = WebhookDispatcher(webhooks) if webhooks else None

    if webhook_dispatcher and webhook_dispatcher.webhooks:
        click.echo(f"Webhooks configured: {len(webhooks)}")
        for wh in webhooks:
            click.echo(f"  - {wh.name}: {wh.url}")
    else:
        click.echo("Webhooks: None configured")

    from meshcore_hub.collector.subscriber import run_collector

    run_collector(
        mqtt_host=mqtt_host,
        mqtt_port=mqtt_port,
        mqtt_username=mqtt_username,
        mqtt_password=mqtt_password,
        mqtt_prefix=prefix,
        database_url=database_url,
        webhook_dispatcher=webhook_dispatcher,
    )
