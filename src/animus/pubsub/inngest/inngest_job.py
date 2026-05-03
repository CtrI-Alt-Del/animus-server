from typing import Any, cast

from inngest import Context


class InngestJob:
    @staticmethod
    def get_event_data_from_context_failure(context: Context) -> dict[str, Any]:
        failure_data = context.event.data

        event_raw = failure_data.get('event')
        if not isinstance(event_raw, dict):
            return {}

        data_raw = event_raw.get('data')
        if not isinstance(data_raw, dict):
            return {}

        return cast(dict[str, Any], data_raw)
