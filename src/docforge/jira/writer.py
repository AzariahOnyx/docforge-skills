"""Comments and ticket moves, sent only when the policy allows; always recorded in the ticket's outbox.

With `jira_comments` or `jira_transitions` off (the default), nothing is sent:
the outbox shows exactly what DocForge would have posted.
"""

from __future__ import annotations

from .state import OutboxEntry, TicketState, now


class JiraWriter:
    def __init__(self, publishing: dict, client_factory=None):
        """`publishing`: the resolved policy section. `client_factory`: returns an AtlassianClient when called."""
        self.comments_on = bool(publishing.get("jira_comments"))
        self.transitions_on = bool(publishing.get("jira_transitions"))
        self._factory = client_factory
        self._client = None

    def _connect(self):
        if self._client is None:
            if self._factory is None:
                raise RuntimeError("no Jira connection is configured")
            self._client = self._factory()
        return self._client

    def comment(self, state: TicketState, kind: str, body: dict) -> OutboxEntry:
        entry = OutboxEntry(at=now(), kind="comment", message=kind, body=body)
        if not self.comments_on:
            entry.note = "not sent: the jira_comments policy is off"
        else:
            from docforge.sources.atlassian import SourceFetchError, post_json, segment

            try:
                post_json(self._connect(), f"rest/api/3/issue/{segment(state.key)}/comment", {"body": body})
                entry.sent = True
            except (SourceFetchError, RuntimeError) as exc:
                entry.note = f"not sent: {exc}"
        state.outbox.append(entry)
        return entry

    def transition(self, state: TicketState, status: str) -> OutboxEntry:
        entry = OutboxEntry(at=now(), kind="transition", message=status)
        if not self.transitions_on:
            entry.note = "not moved: the jira_transitions policy is off"
        else:
            from docforge.sources.atlassian import SourceFetchError, post_json, segment

            try:
                client = self._connect()
                path = f"rest/api/3/issue/{segment(state.key)}/transitions"
                options = client.get_json(path).get("transitions") or []
                match = next((t for t in options if str((t.get("to") or {}).get("name", "")).casefold()
                              == status.casefold()), None)
                if match is None:
                    entry.note = f"not moved: the workflow has no transition to {status}"
                else:
                    post_json(client, path, {"transition": {"id": str(match["id"])}})
                    entry.sent = True
            except (SourceFetchError, RuntimeError, KeyError) as exc:
                entry.note = f"not moved: {exc}"
        state.outbox.append(entry)
        return entry
