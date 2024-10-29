class ThemeManager:
    @staticmethod
    def get_default_theme():
        return {
            "name": "Default Theme",
            "preview": "#34495e",
            "colors": {
                "main_bg": "#34495e",
                "card_bg": "#2c3e50",
                "input_bg": "#465c71",
                "text": "#ecf0f1",
                "secondary_text": "#bdc3c7",
                "button_bg": "#3498db",
                "button_hover": "#2980b9",
                "button_pressed": "#21618c",
                "progress_bg": "#465c71",
                "progress_chunk": "#2ecc71",
                "success": "#2ecc71",
                "warning": "#f39c12",
                "error": "#e74c3c",
                "border": "none"
            }
        }

    @staticmethod
    def get_available_themes():
        themes = {
            "default": ThemeManager.get_default_theme(),
            "nord": {
                "name": "Nord Theme",
                "preview": "#2E3440",
                "colors": {
                    "main_bg": "#2E3440",
                    "card_bg": "#3B4252",
                    "input_bg": "#434C5E",
                    "text": "#ECEFF4",
                    "secondary_text": "#D8DEE9",
                    "button_bg": "#5E81AC",
                    "button_hover": "#81A1C1",
                    "button_pressed": "#4C566A",
                    "progress_bg": "#434C5E",
                    "progress_chunk": "#A3BE8C",
                    "success": "#A3BE8C",
                    "warning": "#EBCB8B",
                    "error": "#BF616A",
                    "border": "none"
                }
            },
            "dracula": {
                "name": "Dracula Theme",
                "preview": "#282A36",
                "colors": {
                    "main_bg": "#282A36",
                    "card_bg": "#44475A",
                    "input_bg": "#6272A4",
                    "text": "#F8F8F2",
                    "secondary_text": "#BFBFBF",
                    "button_bg": "#BD93F9",
                    "button_hover": "#FF79C6",
                    "button_pressed": "#6272A4",
                    "progress_bg": "#44475A",
                    "progress_chunk": "#50FA7B",
                    "success": "#50FA7B",
                    "warning": "#FFB86C",
                    "error": "#FF5555",
                    "border": "none"
                }
            },
            "monokai": {
                "name": "Monokai Theme",
                "preview": "#272822",
                "colors": {
                    "main_bg": "#272822",
                    "card_bg": "#3E3D32",
                    "input_bg": "#49483E",
                    "text": "#F8F8F2",
                    "secondary_text": "#BFBFBF",
                    "button_bg": "#A6E22E",
                    "button_hover": "#F92672",
                    "button_pressed": "#49483E",
                    "progress_bg": "#3E3D32",
                    "progress_chunk": "#A6E22E",
                    "success": "#A6E22E",
                    "warning": "#FD971F",
                    "error": "#F92672",
                    "border": "none"
                }
            },
            "solarized": {
                "name": "Solarized Dark Theme",
                "preview": "#002B36",
                "colors": {
                    "main_bg": "#002B36",
                    "card_bg": "#073642",
                    "input_bg": "#586E75",
                    "text": "#93A1A1",
                    "secondary_text": "#839496",
                    "button_bg": "#268BD2",
                    "button_hover": "#2AA198",
                    "button_pressed": "#586E75",
                    "progress_bg": "#073642",
                    "progress_chunk": "#859900",
                    "success": "#859900",
                    "warning": "#B58900",
                    "error": "#DC322F",
                    "border": "none"
                }
            },
            "github-dark": {
                "name": "GitHub Dark Theme",
                "preview": "#0D1117",
                "colors": {
                    "main_bg": "#0D1117",
                    "card_bg": "#161B22",
                    "input_bg": "#21262D",
                    "text": "#C9D1D9",
                    "secondary_text": "#8B949E",
                    "button_bg": "#238636",
                    "button_hover": "#2EA043",
                    "button_pressed": "#238636",
                    "progress_bg": "#21262D",
                    "progress_chunk": "#238636",
                    "success": "#238636",
                    "warning": "#F85149",
                    "error": "#F85149",
                    "border": "none"
                }
            },
            "cyberpunk": {
                "name": "Cyberpunk Theme",
                "preview": "#2A2139",
                "colors": {
                    "main_bg": "#2A2139",
                    "card_bg": "#34294F",
                    "input_bg": "#3B2E5A",
                    "text": "#FF7EDB",
                    "secondary_text": "#F8F8F2",
                    "button_bg": "#F92A82",
                    "button_hover": "#FF2E97",
                    "button_pressed": "#D61F6F",
                    "progress_bg": "#3B2E5A",
                    "progress_chunk": "#36F9F6",
                    "success": "#72F1B8",
                    "warning": "#FFE600",
                    "error": "#FF2E97",
                    "border": "none"
                }
            },
            "material-ocean": {
                "name": "Material Ocean Theme",
                "preview": "#0F111A",
                "colors": {
                    "main_bg": "#0F111A",
                    "card_bg": "#1A1C25",
                    "input_bg": "#252931",
                    "text": "#8F93A2",
                    "secondary_text": "#717CB4",
                    "button_bg": "#84FFFF",
                    "button_hover": "#80CBC4",
                    "button_pressed": "#80CBC4",
                    "progress_bg": "#252931",
                    "progress_chunk": "#80CBC4",
                    "success": "#C3E88D",
                    "warning": "#FFCB6B",
                    "error": "#FF5370",
                    "border": "none"
                }
            },
            "gruvbox": {
                "name": "Gruvbox Dark Theme",
                "preview": "#282828",
                "colors": {
                    "main_bg": "#282828",
                    "card_bg": "#3C3836",
                    "input_bg": "#504945",
                    "text": "#EBDBB2",
                    "secondary_text": "#D5C4A1",
                    "button_bg": "#B8BB26",
                    "button_hover": "#98971A",
                    "button_pressed": "#79740E",
                    "progress_bg": "#504945",
                    "progress_chunk": "#B8BB26",
                    "success": "#B8BB26",
                    "warning": "#FABD2F",
                    "error": "#FB4934",
                    "border": "none"
                }
            },
            "tokyo-night": {
                "name": "Tokyo Night Theme",
                "preview": "#1A1B26",
                "colors": {
                    "main_bg": "#1A1B26",
                    "card_bg": "#24283B",
                    "input_bg": "#414868",
                    "text": "#A9B1D6",
                    "secondary_text": "#787C99",
                    "button_bg": "#7AA2F7",
                    "button_hover": "#3D59A1",
                    "button_pressed": "#3D59A1",
                    "progress_bg": "#414868",
                    "progress_chunk": "#7AA2F7",
                    "success": "#9ECE6A",
                    "warning": "#E0AF68",
                    "error": "#F7768E",
                    "border": "none"
                }
            },
            "catppuccin": {
                "name": "Catppuccin Theme",
                "preview": "#1E1E2E",
                "colors": {
                    "main_bg": "#1E1E2E",
                    "card_bg": "#24273A",
                    "input_bg": "#363A4F",
                    "text": "#CAD3F5",
                    "secondary_text": "#B8C0E0",
                    "button_bg": "#8AADF4",
                    "button_hover": "#7DC4E4",
                    "button_pressed": "#5B6078",
                    "progress_bg": "#363A4F",
                    "progress_chunk": "#A6DA95",
                    "success": "#A6DA95",
                    "warning": "#EED49F",
                    "error": "#ED8796",
                    "border": "none"
                }
            },
            "one-dark": {
                "name": "One Dark Theme",
                "preview": "#282C34",
                "colors": {
                    "main_bg": "#282C34",
                    "card_bg": "#21252B",
                    "input_bg": "#3B4048",
                    "text": "#ABB2BF",
                    "secondary_text": "#828997",
                    "button_bg": "#61AFEF",
                    "button_hover": "#528BFF",
                    "button_pressed": "#4B5263",
                    "progress_bg": "#3B4048",
                    "progress_chunk": "#98C379",
                    "success": "#98C379",
                    "warning": "#E5C07B",
                    "error": "#E06C75",
                    "border": "none"
                }
            },
            "ayu-dark": {
                "name": "Ayu Dark Theme",
                "preview": "#0A0E14",
                "colors": {
                    "main_bg": "#0A0E14",
                    "card_bg": "#0F1419",
                    "input_bg": "#1C1F25",
                    "text": "#B3B1AD",
                    "secondary_text": "#828A97",
                    "button_bg": "#39BAE6",
                    "button_hover": "#59C2FF",
                    "button_pressed": "#1C1F25",
                    "progress_bg": "#1C1F25",
                    "progress_chunk": "#C2D94C",
                    "success": "#C2D94C",
                    "warning": "#FFB454",
                    "error": "#FF3333",
                    "border": "none"
                }
            },
            "rose-pine": {
                "name": "Rosé Pine Theme",
                "preview": "#191724",
                "colors": {
                    "main_bg": "#191724",
                    "card_bg": "#1F1D2E",
                    "input_bg": "#26233A",
                    "text": "#E0DEF4",
                    "secondary_text": "#908CAA",
                    "button_bg": "#9CCFD8",
                    "button_hover": "#31748F",
                    "button_pressed": "#26233A",
                    "progress_bg": "#26233A",
                    "progress_chunk": "#A6E3A1",
                    "success": "#A6E3A1",
                    "warning": "#F6C177",
                    "error": "#EB6F92",
                    "border": "none"
                }
            },
            "everforest": {
                "name": "Everforest Theme",
                "preview": "#2B3339",
                "colors": {
                    "main_bg": "#2B3339",
                    "card_bg": "#323C41",
                    "input_bg": "#404C51",
                    "text": "#D3C6AA",
                    "secondary_text": "#9DA9A0",
                    "button_bg": "#A7C080",
                    "button_hover": "#83C092",
                    "button_pressed": "#404C51",
                    "progress_bg": "#404C51",
                    "progress_chunk": "#A7C080",
                    "success": "#A7C080",
                    "warning": "#E69875",
                    "error": "#E67E80",
                    "border": "none"
                }
            },
            "light": {
                "name": "Light Theme",
                "preview": "#FFFFFF",
                "colors": {
                    "main_bg": "#FFFFFF",
                    "card_bg": "#F5F5F5",
                    "input_bg": "#EEEEEE",
                    "text": "#2C3E50",
                    "secondary_text": "#7F8C8D",
                    "button_bg": "#3498DB",
                    "button_hover": "#2980B9",
                    "button_pressed": "#2574A9",
                    "progress_bg": "#EEEEEE",
                    "progress_chunk": "#2ECC71",
                    "success": "#27AE60",
                    "warning": "#F39C12",
                    "error": "#E74C3C",
                    "border": "1px solid #E0E0E0"
                }
            },
            "github-light": {
                "name": "GitHub Light Theme",
                "preview": "#FFFFFF",
                "colors": {
                    "main_bg": "#FFFFFF",
                    "card_bg": "#F6F8FA",
                    "input_bg": "#EAEEF2",
                    "text": "#24292F",
                    "secondary_text": "#57606A",
                    "button_bg": "#2DA44E",
                    "button_hover": "#2C974B",
                    "button_pressed": "#298E46",
                    "progress_bg": "#EAEEF2",
                    "progress_chunk": "#2DA44E",
                    "success": "#2DA44E",
                    "warning": "#D29922",
                    "error": "#CF222E",
                    "border": "1px solid #D0D7DE"
                }
            }
        }
        return themes