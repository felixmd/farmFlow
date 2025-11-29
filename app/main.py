from fasthtml.common import *

# DaisyUI and Tailwind CSS headers
daisy_hdrs = (
    Link(href='https://cdn.jsdelivr.net/npm/daisyui@5', rel='stylesheet', type='text/css'),
    Script(src='https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4'),
    Link(rel='stylesheet', href='https://cdn.jsdelivr.net/npm/@tailwindcss/typography@0.4.1/dist/typography.min.css'),
    Link(href='https://cdn.jsdelivr.net/npm/daisyui@5/themes.css', rel='stylesheet', type='text/css')
)

# Initialize FastHTML app with DaisyUI headers
app, rt = fast_app(hdrs=daisy_hdrs)

@rt('/')
def get():
    """Main route - renders the welcome page"""
    return Titled(
        "FarmerPilot",
        Div(
            H1("Hello Farmer", cls="text-4xl font-bold text-primary"),
            P("Welcome to FarmerPilot - Your AI-powered farming assistant", cls="text-lg mt-4"),
            cls="hero min-h-screen bg-base-200"
        )
    )

# Run the application
serve()
