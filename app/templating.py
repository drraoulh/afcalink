from fastapi import Request
from fastapi.templating import Jinja2Templates
from app.flash import pop_flashes


class FlashTemplates(Jinja2Templates):
    def TemplateResponse(self, shadow_name: str, context: dict, status_code: int = 200, **kwargs):
        req: Request | None = context.get("request")
        if req is not None:
            context = dict(context)
            context.setdefault("flashes", pop_flashes(req))
            from datetime import datetime
            context.setdefault("now_date", datetime.utcnow().strftime("%Y-%m-%d"))
            
            # Global Notifications Count
            user = context.get("user")
            if user and "id" in user:
                from app.db import get_db
                from app.data.notifications import count_unread
                import asyncio
                # Note: This is a bit hacky for Jinja default, usually done in middleware
                # but for this architecture let's try to get a sync-wrapped count or similar
                # Since TemplateResponse is usually called from an async route, we can try to get the count
                try:
                    db = get_db()
                    # We can't easily await inside a non-async function without complexity
                    # Let's just put a placeholder or make TemplateResponse async (complex for inheritance)
                    # Alternative: use a sync version or just rely on specific routes
                    pass
                except:
                    pass
        return super().TemplateResponse(shadow_name, context, status_code=status_code, **kwargs)


templates = FlashTemplates(directory="templates")
