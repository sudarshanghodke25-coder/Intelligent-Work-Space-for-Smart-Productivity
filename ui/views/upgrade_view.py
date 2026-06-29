import customtkinter as ctk
from theme import Colors, Fonts
from ui.glass_card import GlassCard
from utils.animations import apply_hover_animation

class UpgradeView(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.pack_propagate(False)

        # Main Scrollable Container
        self.scroll_container = ctk.CTkScrollableFrame(self, fg_color="transparent", bg_color="transparent")
        self.scroll_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Header Section
        header = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        header.pack(fill="x", pady=(20, 40))

        title = ctk.CTkLabel(header, text="Choose Your Plan", font=Fonts.TITLE, text_color=Colors.TEXT_PRIMARY)
        title.pack(anchor="center", pady=(0, 10))

        subtitle = ctk.CTkLabel(
            header,
            text="Unlock the full potential of FLOWSPACE Cosmic Glass Workspace.\nSelect the plan that best fits your workflow.",
            font=Fonts.BODY,
            text_color=Colors.TEXT_SECONDARY,
            justify="center"
        )
        subtitle.pack(anchor="center")

        # Plans Container (Side by side)
        plans_container = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        plans_container.pack(fill="x", expand=True, pady=10)
        
        plans_container.grid_columnconfigure(0, weight=1)
        plans_container.grid_columnconfigure(1, weight=1)
        plans_container.grid_columnconfigure(2, weight=1)

        # 1. Normal Plan
        self._build_plan_card(
            plans_container,
            col=0,
            title="Normal Plan",
            price="Free",
            period="Forever",
            color=Colors.TEXT_SECONDARY,
            features=[
                "Basic AI Assistant (Llama-3 8B)",
                "Standard Image Studio (720p)",
                "5 AI Planner roadmaps / month",
                "Local SQLite database",
                "Standard theme support"
            ],
            button_text="Current Plan",
            is_active=True
        )

        # 2. Pro Plan
        self._build_plan_card(
            plans_container,
            col=1,
            title="Pro Plan",
            price="$9.99",
            period="/ month",
            color=Colors.ACCENT_PRIMARY,
            features=[
                "Advanced AI Models (GPT-4o, Claude)",
                "Pro Image Studio (4K, Ultra HD)",
                "Unlimited AI Planner roadmaps",
                "Cloud sync & cross-device backup",
                "Priority email support"
            ],
            button_text="Upgrade to Pro",
            highlight=True
        )

        # 3. Ultra Pro Plan
        self._build_plan_card(
            plans_container,
            col=2,
            title="Ultra Pro",
            price="$24.99",
            period="/ month",
            color=Colors.SUCCESS,
            features=[
                "All Pro Plan features",
                "Enterprise-grade Security",
                "Custom AI fine-tuning capabilities",
                "API access for developers",
                "24/7 Dedicated account manager"
            ],
            button_text="Get Ultra Pro"
        )

    def _build_plan_card(self, parent, col, title, price, period, color, features, button_text, is_active=False, highlight=False):
        # Create Card
        card = GlassCard(parent, title="")
        card.grid(row=0, column=col, sticky="nsew", padx=15, pady=10)
        
        # Border highlight for the recommended/pro plan
        if highlight:
            card.configure(border_color=color, border_width=2)
            apply_hover_animation(card, 'border_color', color, Colors.TEXT_PRIMARY)
        else:
            apply_hover_animation(card, 'border_color', Colors.BORDER_SUBTLE, color)

        content = card.content
        content.pack(fill="both", expand=True, padx=20, pady=25)

        # Plan Title
        ctk.CTkLabel(content, text=title, font=Fonts.TITLE, text_color=color).pack(anchor="center", pady=(0, 15))

        # Price
        price_frame = ctk.CTkFrame(content, fg_color="transparent")
        price_frame.pack(anchor="center", pady=(0, 25))
        ctk.CTkLabel(price_frame, text=price, font=Fonts.TITLE, text_color=Colors.TEXT_PRIMARY).pack(side="left")
        ctk.CTkLabel(price_frame, text=period, font=Fonts.BODY, text_color=Colors.TEXT_MUTED).pack(side="left", padx=(5, 0), anchor="s", pady=(0, 5))

        # Divider
        divider = ctk.CTkFrame(content, fg_color=Colors.BORDER_SUBTLE, height=1)
        divider.pack(fill="x", pady=(0, 20))

        # Features List
        features_frame = ctk.CTkFrame(content, fg_color="transparent")
        features_frame.pack(fill="both", expand=True)

        for feature in features:
            f_row = ctk.CTkFrame(features_frame, fg_color="transparent")
            f_row.pack(fill="x", pady=6)
            ctk.CTkLabel(f_row, text="✓", font=Fonts.BODY_BOLD, text_color=color).pack(side="left", padx=(0, 10))
            ctk.CTkLabel(f_row, text=feature, font=Fonts.BODY, text_color=Colors.TEXT_SECONDARY, justify="left", wraplength=220).pack(side="left", fill="x")

        # Action Button
        btn_kwargs = {
            "text": button_text,
            "font": Fonts.BUTTON,
            "height": 45,
            "corner_radius": 10,
        }
        
        if is_active:
            btn_kwargs["fg_color"] = "transparent"
            btn_kwargs["text_color"] = Colors.TEXT_MUTED
            btn_kwargs["border_width"] = 1
            btn_kwargs["border_color"] = Colors.BORDER_SUBTLE
            btn_kwargs["state"] = "disabled"
        else:
            btn_kwargs["fg_color"] = color
            btn_kwargs["hover_color"] = Colors.ACCENT_HOVER
            btn_kwargs["text_color"] = Colors.TEXT_PRIMARY

        action_btn = ctk.CTkButton(content, **btn_kwargs)
        action_btn.pack(fill="x", side="bottom", pady=(30, 0))
