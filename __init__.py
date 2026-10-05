import logging
from .adapter import RubikaAdapter

logger = logging.getLogger(__name__)
logger.info("Rubika plugin __init__ loaded")


def register(ctx):
    """
    Register the Rubika platform with the Hermes gateway.
    Called by Hermes when the plugin is loaded.
    """
    try:
        import dataclasses
        from gateway.platform_registry import PlatformEntry

        kwargs = dict(
            name="rubika",
            label="Rubika",
            adapter_factory=lambda cfg: RubikaAdapter(cfg),
        )

        # Feature-detect optional fields so we stay compatible
        # with older and newer Hermes cores alike.
        known = {f.name for f in dataclasses.fields(PlatformEntry)}
        if "trusted_inbound" in known:
            kwargs["trusted_inbound"] = False
        if "display_tier" in known:
            kwargs["display_tier"] = "medium"

        ctx.register_platform(**kwargs)
        logger.info("Rubika platform registered successfully")
    except Exception as e:
        logger.error(f"Failed to register Rubika platform: {e}", exc_info=True)
